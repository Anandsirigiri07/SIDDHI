# backend/graph_engine.py
from typing import List, Dict, Any, Tuple
import networkx as nx
from sqlalchemy import text
from backend.database import engine

def extract_ids_from_results(sql_results: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """Helper to extract fir_ids and accused_ids from raw SQL results."""
    fir_ids = []
    accused_ids = []
    for row in sql_results:
        for k, v in row.items():
            if not isinstance(v, int):
                continue
            k_lower = k.lower()
            if k_lower == "fir_id":
                fir_ids.append(v)
            elif "accused_id" in k_lower or "accusedmasterid" in k_lower or k_lower == "accused_id":
                accused_ids.append(v)
            elif k_lower == "id":
                if "fir" in str(row.get("fir_number", "")).lower():
                    fir_ids.append(v)
                elif "name" in row:
                    accused_ids.append(v)
    return list(set(fir_ids)), list(set(accused_ids))

def build_network_graph(sql_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Constructs a NetworkX graph centered around the query results.
    Performs a strict 2-hop relationship expansion starting from the query seed:
    Seed node -> Associated FIRs -> Co-Accused & Locations.
    Computes PageRank, Betweenness Centrality, and Louvain communities.
    """
    fir_ids, accused_ids = extract_ids_from_results(sql_results)
    
    G = nx.Graph()
    
    # We will fetch relationships from database using direct SQL queries
    with engine.connect() as conn:
        # If we have accused_ids, expand starting from accused
        if accused_ids:
            # 1. Fetch seed accused details
            acc_placeholder = ",".join(str(aid) for aid in accused_ids)
            acc_rows = conn.execute(text(f"SELECT accused_id, name, risk_score FROM accused WHERE accused_id IN ({acc_placeholder})")).fetchall()
            for row in acc_rows:
                aid, name, risk = row
                G.add_node(f"accused-{aid}", label=name, type="Accused", risk_score=risk)
                
            fir_acc_rows = conn.execute(text(f"SELECT fir_id, accused_id, role FROM fir_accused WHERE accused_id IN ({acc_placeholder})")).fetchall()
            associated_fir_ids = list(set([row[0] for row in fir_acc_rows]))
            if len(associated_fir_ids) > 6:
                associated_fir_ids = associated_fir_ids[:6]
            
            if associated_fir_ids:
                fir_pl = ",".join(str(fid) for fid in associated_fir_ids)
                fir_rows = conn.execute(text(f"""
                    SELECT f.fir_id, f.fir_number, f.crime_type, f.location_id, l.name as loc_name, f.date 
                    FROM firs f 
                    LEFT JOIN locations l ON f.location_id = l.location_id
                    WHERE f.fir_id IN ({fir_pl})
                """)).fetchall()
                
                for row in fir_rows:
                    fid, fnum, ctype, lid, lname, fdate = row
                    G.add_node(f"fir-{fid}", label=fnum, type="FIR", crime_type=ctype, date=fdate)
                    
                    # Link to seed accused
                    for fa_row in fir_acc_rows:
                        if fa_row[0] == fid:
                            G.add_edge(f"fir-{fid}", f"accused-{fa_row[1]}", relation="accused_in", role=fa_row[2])
                            
                    if lid:
                        G.add_node(f"loc-{lid}", label=lname, type="Location")
                        G.add_edge(f"fir-{fid}", f"loc-{lid}", relation="happened_at")
                
                # 3. Find co-accused in those FIRs (2-hop)
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
            # Expand starting from FIRs
            fir_pl = ",".join(str(fid) for fid in fir_ids)
            fir_rows = conn.execute(text(f"""
                SELECT f.fir_id, f.fir_number, f.crime_type, f.location_id, l.name as loc_name, f.date 
                FROM firs f 
                LEFT JOIN locations l ON f.location_id = l.location_id
                WHERE f.fir_id IN ({fir_pl})
            """)).fetchall()
            
            for row in fir_rows:
                fid, fnum, ctype, lid, lname, fdate = row
                G.add_node(f"fir-{fid}", label=fnum, type="FIR", crime_type=ctype, date=fdate)
                if lid:
                    G.add_node(f"loc-{lid}", label=lname, type="Location")
                    G.add_edge(f"fir-{fid}", f"loc-{lid}", relation="happened_at")
            
            # Find accused in those FIRs (1-hop)
            fir_acc_rows = conn.execute(text(f"""
                SELECT fa.fir_id, fa.accused_id, fa.role, a.name, a.risk_score 
                FROM fir_accused fa
                JOIN accused a ON fa.accused_id = a.accused_id
                WHERE fa.fir_id IN ({fir_pl})
            """)).fetchall()
            
            accused_found_ids = set()
            for row in fir_acc_rows:
                fid, aid, role, name, risk = row
                accused_found_ids.add(aid)
                G.add_node(f"accused-{aid}", label=name, type="Accused", risk_score=risk)
                G.add_edge(f"fir-{fid}", f"accused-{aid}", relation="accused_in", role=role)
                
            # Find other FIRs of these accused (2-hop) to show links, but limit to prevent explosion
            if accused_found_ids:
                acc_pl = ",".join(str(aid) for aid in accused_found_ids)
                other_fir_acc_rows = conn.execute(text(f"""
                    SELECT fa.fir_id, fa.accused_id, fa.role, f.fir_number, f.crime_type, f.date 
                    FROM fir_accused fa
                    JOIN firs f ON fa.fir_id = f.fir_id
                    WHERE fa.accused_id IN ({acc_pl}) AND fa.fir_id NOT IN ({fir_pl})
                    LIMIT 20
                """)).fetchall()
                
                for row in other_fir_acc_rows:
                    fid, aid, role, fnum, ctype, fdate = row
                    G.add_node(f"fir-{fid}", label=fnum, type="FIR", crime_type=ctype, date=fdate)
                    G.add_edge(f"fir-{fid}", f"accused-{aid}", relation="accused_in", role=role)

    # If the constructed graph has no nodes, return empty payload
    if G.number_of_nodes() == 0:
        return {
            "nodes": [], 
            "links": [], 
            "communities": {}, 
            "centrality_scores": {},
            "seed_node": None,
            "community_count": 0,
            "node_count": 0,
            "edge_count": 0,
            "top_central_nodes": []
        }

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

    # Format nodes list (sizing proportional to PageRank score)
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
            
        # Calculate bridge suspect score (only for Accused nodes)
        if attrs.get("type") == "Accused":
            neighbors = list(G.neighbors(node))
            neighbor_communities = set([communities_map.get(n, 0) for n in neighbors])
            bt = betweenness_scores.get(node, 0.0)
            
            if len(neighbor_communities) > 1 and bt > 0.0:
                # Suspect connects FIRs in multiple Louvain communities
                bridge_score = min(1.0, bt * len(neighbor_communities) * 3)
            else:
                bridge_score = 0.0
                
            node_entry["bridge_score"] = round(bridge_score, 4)
            node_entry["is_bridge"] = bridge_score > 0.05 or (len(neighbor_communities) > 1 and bt > 0.01)
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

    return {
        "nodes": nodes_list,
        "links": links_list,
        "communities": communities_map,
        "centrality_scores": pagerank_scores,
        "seed_node": seed_node,
        "community_count": community_count,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "top_central_nodes": top_central_nodes
    }
