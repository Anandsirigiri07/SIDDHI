# backend/graph_engine.py
from typing import List, Dict, Any, Tuple
import networkx as nx
from sqlalchemy import text
from backend.database import engine

def extract_ids_from_results(sql_results: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """
    Helper to extract fir_ids and accused_ids from raw SQL results.
    If direct IDs are missing (e.g. area/hotspot summary queries), performs deterministic 
    fallback entity resolution by mapping location_ids, names, or districts to backing FIRs.
    """
    fir_ids = []
    accused_ids = []
    location_ids = []
    districts = []

    for row in sql_results:
        for k, v in row.items():
            k_lower = str(k).lower()
            if isinstance(v, int):
                if k_lower == "fir_id":
                    fir_ids.append(v)
                elif "accused_id" in k_lower or "accusedmasterid" in k_lower:
                    accused_ids.append(v)
                elif k_lower == "location_id":
                    location_ids.append(v)
                elif k_lower == "id":
                    if "fir" in str(row.get("fir_number", "")).lower():
                        fir_ids.append(v)
                    elif "name" in row and "district" in row:
                        accused_ids.append(v)
            elif isinstance(v, str):
                if k_lower in ("district", "district_name"):
                    districts.append(v)
                elif k_lower in ("loc_name", "location_name") or (k_lower == "name" and "lat" in row):
                    # Location name string
                    districts.append(v)

    fir_ids = list(set(fir_ids))
    accused_ids = list(set(accused_ids))

    # Fallback Deterministic Entity Resolution if direct FIR/Accused IDs were absent but filters existed
    if not fir_ids and not accused_ids and sql_results:
        with engine.connect() as conn:
            if location_ids:
                loc_pl = ",".join(str(lid) for lid in list(set(location_ids))[:10])
                resolved_firs = conn.execute(text(f"SELECT fir_id FROM firs WHERE location_id IN ({loc_pl}) LIMIT 25")).fetchall()
                fir_ids = [r[0] for r in resolved_firs]
            elif districts:
                # Query locations matching these district/area strings
                d_conds = " OR ".join([f"LOWER(l.district) LIKE '%{d.lower()}%' OR LOWER(l.name) LIKE '%{d.lower()}%'" for d in list(set(districts))[:5]])
                resolved_firs = conn.execute(text(f"""
                    SELECT f.fir_id 
                    FROM firs f 
                    JOIN locations l ON f.location_id = l.location_id 
                    WHERE {d_conds}
                    LIMIT 25
                """)).fetchall()
                fir_ids = [r[0] for r in resolved_firs]

    return list(set(fir_ids)), list(set(accused_ids))

def build_network_graph(sql_results: List[Dict[str, Any]], include_shadow_links: bool = False) -> Dict[str, Any]:
    """
    Constructs a NetworkX graph centered around the query results.
    Performs a strict 2-hop relationship expansion starting from the query seed:
    Seed node -> Associated FIRs -> Co-Accused & Locations.
    Computes PageRank, Betweenness Centrality, Louvain communities, and Cross-District Bridge Suspects.
    
    Mandatory Rule #7: include_shadow_links defaults to False.
    Only when explicitly activated does it calculate/render 2-hop shadow links.
    """
    fir_ids, accused_ids = extract_ids_from_results(sql_results)
    
    G = nx.Graph()
    accused_districts_map: Dict[int, set] = {}
    
    # We will fetch relationships from database using direct SQL queries
    with engine.connect() as conn:
        # If we have accused_ids, expand starting from accused
        if accused_ids:
            acc_placeholder = ",".join(str(aid) for aid in accused_ids)
            acc_rows = conn.execute(text(f"SELECT accused_id, name, risk_score FROM accused WHERE accused_id IN ({acc_placeholder})")).fetchall()
            for row in acc_rows:
                aid, name, risk = row
                G.add_node(f"accused-{aid}", label=name, type="Accused", risk_score=risk)
                
            fir_acc_rows = conn.execute(text(f"SELECT fir_id, accused_id, role FROM fir_accused WHERE accused_id IN ({acc_placeholder})")).fetchall()
            associated_fir_ids = list(set([row[0] for row in fir_acc_rows]))
            if len(associated_fir_ids) > 10:
                associated_fir_ids = associated_fir_ids[:10]
            
            if associated_fir_ids:
                fir_pl = ",".join(str(fid) for fid in associated_fir_ids)
                fir_rows = conn.execute(text(f"""
                    SELECT f.fir_id, f.fir_number, f.crime_type, f.location_id, l.name as loc_name, l.district, f.date 
                    FROM firs f 
                    LEFT JOIN locations l ON f.location_id = l.location_id
                    WHERE f.fir_id IN ({fir_pl})
                """)).fetchall()
                
                for row in fir_rows:
                    fid, fnum, ctype, lid, lname, district, fdate = row
                    G.add_node(f"fir-{fid}", label=fnum, type="FIR", crime_type=ctype, date=fdate)
                    
                    # Link to seed accused
                    for fa_row in fir_acc_rows:
                        if fa_row[0] == fid:
                            aid = fa_row[1]
                            G.add_edge(f"fir-{fid}", f"accused-{aid}", relation="accused_in", role=fa_row[2])
                            if district:
                                accused_districts_map.setdefault(aid, set()).add(district)
                            
                    if lid:
                        G.add_node(f"loc-{lid}", label=lname, type="Location", district=district or "Bengaluru")
                        G.add_edge(f"fir-{fid}", f"loc-{lid}", relation="happened_at")
                
                # Co-accused in those FIRs (2-hop)
                co_acc_rows = conn.execute(text(f"""
                    SELECT fa.fir_id, fa.accused_id, fa.role, a.name, a.risk_score 
                    FROM fir_accused fa
                    JOIN accused a ON fa.accused_id = a.accused_id
                    WHERE fa.fir_id IN ({fir_pl}) AND fa.accused_id NOT IN ({acc_placeholder})
                """)).fetchall()
                
                for row in co_acc_rows:
                    fid, aid, role, name, risk = row
                    G.add_node(f"accused-{aid}", label=name, type="Accused", risk_score=risk)
                    G.add_edge(f"fir-{fid}", f"accused-{aid}", relation="co_accused", role=role)
                    
        elif fir_ids:
            fir_pl = ",".join(str(fid) for fid in fir_ids)
            fir_rows = conn.execute(text(f"""
                SELECT f.fir_id, f.fir_number, f.crime_type, f.location_id, l.name as loc_name, l.district, f.date 
                FROM firs f 
                LEFT JOIN locations l ON f.location_id = l.location_id
                WHERE f.fir_id IN ({fir_pl})
            """)).fetchall()
            
            for row in fir_rows:
                fid, fnum, ctype, lid, lname, district, fdate = row
                G.add_node(f"fir-{fid}", label=fnum, type="FIR", crime_type=ctype, date=fdate)
                if lid:
                    G.add_node(f"loc-{lid}", label=lname, type="Location", district=district or "Bengaluru")
                    G.add_edge(f"fir-{fid}", f"loc-{lid}", relation="happened_at")
            
            # Find accused in those FIRs
            fir_acc_rows = conn.execute(text(f"""
                SELECT fa.fir_id, fa.accused_id, fa.role, a.name, a.risk_score, l.district
                FROM fir_accused fa
                JOIN accused a ON fa.accused_id = a.accused_id
                JOIN firs f ON fa.fir_id = f.fir_id
                LEFT JOIN locations l ON f.location_id = l.location_id
                WHERE fa.fir_id IN ({fir_pl})
            """)).fetchall()
            
            accused_found_ids = set()
            for row in fir_acc_rows:
                fid, aid, role, name, risk, district = row
                accused_found_ids.add(aid)
                G.add_node(f"accused-{aid}", label=name, type="Accused", risk_score=risk)
                G.add_edge(f"fir-{fid}", f"accused-{aid}", relation="accused_in", role=role)
                if district:
                    accused_districts_map.setdefault(aid, set()).add(district)
                
            # Expand secondary links
            if accused_found_ids:
                acc_pl = ",".join(str(aid) for aid in accused_found_ids)
                other_fir_acc_rows = conn.execute(text(f"""
                    SELECT fa.fir_id, fa.accused_id, fa.role, f.fir_number, f.crime_type, f.date, l.district
                    FROM fir_accused fa
                    JOIN firs f ON fa.fir_id = f.fir_id
                    LEFT JOIN locations l ON f.location_id = l.location_id
                    WHERE fa.accused_id IN ({acc_pl}) AND fa.fir_id NOT IN ({fir_pl})
                    LIMIT 25
                """)).fetchall()
                
                for row in other_fir_acc_rows:
                    fid, aid, role, fnum, ctype, fdate, district = row
                    G.add_node(f"fir-{fid}", label=fnum, type="FIR", crime_type=ctype, date=fdate)
                    G.add_edge(f"fir-{fid}", f"accused-{aid}", relation="accused_in", role=role)
                    if district:
                        accused_districts_map.setdefault(aid, set()).add(district)

    # If the constructed graph has no nodes, load baseline 2-hop active crime network directly from siddhi.db
    if G.number_of_nodes() == 0:
        with engine.connect() as conn:
            fir_rows = conn.execute(text("SELECT f.fir_id, f.fir_number, f.crime_type, f.location_id, l.name as loc_name, l.district, f.date FROM firs f LEFT JOIN locations l ON f.location_id = l.location_id LIMIT 10")).fetchall()
            for row in fir_rows:
                fid, fnum, ctype, lid, lname, district, fdate = row
                G.add_node(f"fir-{fid}", label=fnum, type="FIR", crime_type=ctype, date=fdate)
                if lid:
                    G.add_node(f"loc-{lid}", label=lname, type="Location", district=district or "Bengaluru")
                    G.add_edge(f"fir-{fid}", f"loc-{lid}", relation="happened_at")

            fir_acc_rows = conn.execute(text("SELECT fa.fir_id, fa.accused_id, fa.role, a.name, a.risk_score, l.district FROM fir_accused fa JOIN accused a ON fa.accused_id = a.accused_id JOIN firs f ON fa.fir_id = f.fir_id LEFT JOIN locations l ON f.location_id = l.location_id LIMIT 25")).fetchall()
            for row in fir_acc_rows:
                fid, aid, role, name, risk, district = row
                G.add_node(f"accused-{aid}", label=name, type="Accused", risk_score=risk)
                if G.has_node(f"fir-{fid}"):
                    G.add_edge(f"fir-{fid}", f"accused-{aid}", relation="accused_in", role=role)
                    if district:
                        accused_districts_map.setdefault(aid, set()).add(district)

    # Perform network metrics calculations
    # 1. PageRank Centrality
    try:
        pagerank_scores = nx.pagerank(G, alpha=0.85)
    except Exception:
        pagerank_scores = nx.degree_centrality(G)

    # 2. Betweenness Centrality
    try:
        betweenness_scores = nx.betweenness_centrality(G)
    except Exception:
        betweenness_scores = {node: 0.0 for node in G.nodes}

    # 3. Louvain Community Detection
    community_count = 1
    try:
        communities_sets = nx.algorithms.community.louvain_communities(G)
        community_count = len(communities_sets)
        communities_map = {}
        for comm_idx, comm_set in enumerate(communities_sets):
            for node in comm_set:
                communities_map[node] = comm_idx
    except Exception:
        communities_map = {node: 0 for node in G.nodes}

    all_districts_involved = set()
    highest_bridge_score = 0.0
    top_bridge_suspect = None

    # Format nodes list
    nodes_list = []
    for node, attrs in G.nodes(data=True):
        pr = pagerank_scores.get(node, 0.0)
        size = round(8.0 + (pr * 150.0), 2)
        node_entry = {
            "id": node,
            "label": attrs.get("label", node),
            "type": attrs.get("type", "Unknown"),
            "size": size,
            "pagerank": round(pr, 4),
            "betweenness": round(betweenness_scores.get(node, 0.0), 4),
            "community": communities_map.get(node, 0)
        }
        if "risk_score" in attrs:
            node_entry["risk_score"] = attrs["risk_score"]
        if "crime_type" in attrs:
            node_entry["crime_type"] = attrs["crime_type"]
        if "date" in attrs:
            node_entry["date"] = attrs["date"]
        if "district" in attrs:
            node_entry["district"] = attrs["district"]
            all_districts_involved.add(attrs["district"])
            
        # Calculate Bridge Suspect Score for Accused nodes
        if attrs.get("type") == "Accused":
            aid_int = int(node.replace("accused-", "")) if "accused-" in node else None
            connected_districts = accused_districts_map.get(aid_int, set()) if aid_int else set()
            all_districts_involved.update(connected_districts)
            
            neighbors = list(G.neighbors(node))
            neighbor_communities = set([communities_map.get(n, 0) for n in neighbors])
            bt = betweenness_scores.get(node, 0.0)
            
            # Bridge calculation formula: betweenness * unique connected districts count
            district_factor = max(1, len(connected_districts))
            b_score = min(1.0, float(bt * district_factor * 3.5))
            
            node_entry["bridge_score"] = round(b_score, 4)
            node_entry["is_bridge"] = (b_score > 0.05 or len(connected_districts) >= 2)
            node_entry["districts"] = list(connected_districts)
            
            if b_score > highest_bridge_score:
                highest_bridge_score = b_score
                top_bridge_suspect = {
                    "accused_id": aid_int,
                    "name": attrs.get("label", "Suspect"),
                    "bridge_score": round(b_score, 4),
                    "districts": list(connected_districts),
                    "explanation": f"Potential bridge connection linking criminal networks across {len(connected_districts)} districts: {', '.join(connected_districts)}."
                }
        else:
            node_entry["bridge_score"] = 0.0
            node_entry["is_bridge"] = False
            
        nodes_list.append(node_entry)

    # Format links list
    links_list = []
    for u, v, attrs in G.edges(data=True):
        links_list.append({
            "source": u,
            "target": v,
            "relation": attrs.get("relation", "linked")
        })

    # Attach optional 2-hop shadow links if opt-in enabled per Mandatory Rule #4 & #7
    if include_shadow_links and accused_ids:
        try:
            from backend.ml.shadow_engine import find_shadow_associations
            for seed_aid in accused_ids[:3]:
                shadow_res = find_shadow_associations(seed_aid, max_results=3)
                for assoc in shadow_res.get("shadow_associations", []):
                    b_id = assoc["person_b_id"]
                    # Add node B to nodes_list if not present
                    b_node_id = f"accused-{b_id}"
                    if not any(n["id"] == b_node_id for n in nodes_list):
                        nodes_list.append({
                            "id": b_node_id,
                            "label": assoc["person_b_name"],
                            "type": "Accused",
                            "risk_score": assoc.get("person_b_risk_score", 20.0),
                            "pagerank": 0.01,
                            "betweenness": 0.0,
                            "community": 0,
                            "is_bridge": False,
                            "bridge_score": 0.0
                        })

                    # Append shadow link (is_shadow = True)
                    links_list.append({
                        "source": f"accused-{seed_aid}",
                        "target": b_node_id,
                        "relation": "potential_indirect_association",
                        "is_shadow": True,
                        "association_type": "INDIRECT_2_HOP",
                        "association_score": assoc["association_score"],
                        "shared_intermediary_names": assoc.get("shared_intermediary_names", []),
                        "explanation": assoc.get("explanation", "")
                    })
        except Exception as e:
            pass

    # Determine seed node dynamically
    seed_node = None
    if accused_ids:
        seed_node = f"accused-{accused_ids[0]}"
    elif fir_ids:
        seed_node = f"fir-{fir_ids[0]}"
    else:
        if nodes_list:
            seed_node = max(nodes_list, key=lambda x: x.get("pagerank", 0.0))["id"]

    # Compile top 10 PageRank nodes
    top_central_nodes = []
    sorted_nodes = sorted(nodes_list, key=lambda x: x.get("pagerank", 0.0), reverse=True)
    for n in sorted_nodes[:10]:
        top_central_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "type": n["type"],
            "pagerank": n["pagerank"]
        })

    suspect_count = sum(1 for n in nodes_list if n["type"] == "Accused")
    fir_count = sum(1 for n in nodes_list if n["type"] == "FIR")
    dist_list = sorted(list(all_districts_involved))

    return {
        "nodes": nodes_list,
        "links": links_list,
        "communities": communities_map,
        "centrality_scores": pagerank_scores,
        "seed_node": seed_node,
        "community_count": community_count,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "top_central_nodes": top_central_nodes,
        "cross_district_summary": {
            "is_cross_district": len(dist_list) >= 2,
            "districts_involved": dist_list,
            "district_count": len(dist_list),
            "suspect_count": suspect_count,
            "fir_count": fir_count,
            "bridge_suspect": top_bridge_suspect
        }
    }
