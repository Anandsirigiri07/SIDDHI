# backend/features/compute_graph_features.py
import datetime
import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models import CentralityMetrics, CommunityAnalysis

def compute_graph_features_all(db: Session):
    """
    Builds the co-accused network graph, computes centrality and community metrics,
    and persists them to centrality_metrics and community_analysis.
    """
    # 1. Fetch all co-accused relations
    # We find all pairs of accused who share the same fir_id
    rows = db.execute(text("""
        SELECT t1.accused_id, t2.accused_id, t1.fir_id 
        FROM fir_accused t1
        JOIN fir_accused t2 ON t1.fir_id = t2.fir_id
        WHERE t1.accused_id < t2.accused_id
    """)).fetchall()
    
    # Also fetch all unique accused to ensure disjoint nodes are included
    all_accused = db.execute(text("SELECT accused_id FROM accused")).fetchall()
    
    G = nx.Graph()
    for (aid,) in all_accused:
        G.add_node(f"accused-{aid}")
        
    for a1, a2, fid in rows:
        G.add_edge(f"accused-{a1}", f"accused-{a2}", fir_id=fid)
        
    # 2. Compute centralities
    pr = nx.pagerank(G, alpha=0.85) if len(G) > 0 else {}
    bet = nx.betweenness_centrality(G) if len(G) > 0 else {}
    deg = nx.degree_centrality(G) if len(G) > 0 else {}
    cls = nx.closeness_centrality(G) if len(G) > 0 else {}
    
    # 3. Compute connected components
    components = list(nx.connected_components(G))
    comp_map = {}
    for comp_idx, comp in enumerate(components):
        for node in comp:
            comp_map[node] = comp_idx
            
    # 4. Compute Louvain communities
    # louvain_communities returns a list of sets of nodes
    try:
        communities_sets = list(nx.community.louvain_communities(G))
    except Exception:
        # Fallback to connected components if Louvain fails or G is empty
        communities_sets = components
        
    comm_map = {}
    comm_sizes = {}
    for comm_idx, comm_set in enumerate(communities_sets):
        comm_sizes[comm_idx] = len(comm_set)
        for node in comm_set:
            comm_map[node] = comm_idx
            
    # 5. Compute Bridge Suspect score
    # Bridge score = betweenness * (number of neighbors in different communities)
    bridge_scores = {}
    for node in G.nodes():
        node_comm = comm_map.get(node, -1)
        neighbors = list(G.neighbors(node))
        neighbor_comms = set(comm_map.get(nbr, -1) for nbr in neighbors if comm_map.get(nbr, -1) != node_comm)
        bridge_scores[node] = float(bet.get(node, 0.0) * len(neighbor_comms))

    # 6. Save results to centrality_metrics and community_analysis tables
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Clear tables first
    db.execute(text("DELETE FROM centrality_metrics"))
    db.execute(text("DELETE FROM community_analysis"))
    db.commit()
    
    for node in G.nodes():
        node_pr = float(pr.get(node, 0.0))
        node_bet = float(bet.get(node, 0.0))
        node_deg = float(deg.get(node, 0.0))
        node_cls = float(cls.get(node, 0.0))
        node_bs = float(bridge_scores.get(node, 0.0))
        
        c_metrics = CentralityMetrics(
            node_id=node,
            pagerank=node_pr,
            betweenness=node_bet,
            degree=node_deg,
            closeness=node_cls,
            bridge_score=node_bs,
            updated_at=now_str
        )
        db.add(c_metrics)
        
        node_comm = int(comm_map.get(node, -1))
        node_csize = int(comm_sizes.get(node_comm, 0))
        node_comp = int(comp_map.get(node, -1))
        
        c_analysis = CommunityAnalysis(
            node_id=node,
            community_id=node_comm,
            community_size=node_csize,
            modularity=0.0, # Louvain modularity metric
            component_id=node_comp,
            updated_at=now_str
        )
        db.add(c_analysis)
        
    db.commit()
