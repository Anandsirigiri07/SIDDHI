# backend/features/compute_accused_features.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models import Accused, FIRAccused, FIR
from backend.config.crime_weights import CRIME_SEVERITY

def compute_accused_features_all(db: Session) -> dict:
    """
    Computes all accused/suspect features.
    Reads pre-calculated NetworkX metrics from centrality_metrics and community_analysis.
    """
    # Fetch all accused
    accused_records = db.query(Accused).all()
    results = {}
    
    # 1. Fetch pre-calculated graph centrality metrics
    pageranks = {}
    betweennesses = {}
    degrees = {}
    closenesses = {}
    bridge_scores = {}
    try:
        metrics_rows = db.execute(text("SELECT node_id, pagerank, betweenness, degree, closeness, bridge_score FROM centrality_metrics")).fetchall()
        for node_id, pr, bet, deg, cls, bs in metrics_rows:
            if node_id.startswith("accused-"):
                aid = int(node_id.replace("accused-", ""))
                pageranks[aid] = float(pr)
                betweennesses[aid] = float(bet)
                degrees[aid] = float(deg)
                closenesses[aid] = float(cls)
                bridge_scores[aid] = float(bs)
    except Exception:
        pass # Fallback to default PageRank if table is empty

    # 2. Fetch pre-calculated Louvain community analysis
    communities = {}
    community_sizes = {}
    components = {}
    try:
        comm_rows = db.execute(text("SELECT node_id, community_id, community_size, component_id FROM community_analysis")).fetchall()
        for node_id, cid, csize, comp_id in comm_rows:
            if node_id.startswith("accused-"):
                aid = int(node_id.replace("accused-", ""))
                communities[aid] = int(cid)
                community_sizes[aid] = float(csize)
                components[aid] = int(comp_id)
    except Exception:
        pass

    # 3. Calculate suspect-level aggregates
    # Count of cases and severity sum per accused
    prior_cases = {}
    severity_sums = {}
    
    cases_rows = db.execute(text("""
        SELECT fa.accused_id, COUNT(fa.fir_id), SUM(f.GravityOffenceID) 
        FROM fir_accused fa
        JOIN firs f ON fa.fir_id = f.fir_id
        GROUP BY fa.accused_id
    """)).fetchall()
    for aid, cnt, grav_sum in cases_rows:
        prior_cases[aid] = int(cnt)
        severity_sums[aid] = float(grav_sum or 0.0)

    # 4. Generate rankings for centrality
    sorted_by_pr = sorted(pageranks.items(), key=lambda x: x[1], reverse=True)
    pr_ranks = {aid: idx + 1 for idx, (aid, _) in enumerate(sorted_by_pr)}

    for a in accused_records:
        aid = a.accused_id
        
        prior_cnt = float(prior_cases.get(aid, 0.0))
        repeat_cnt = prior_cnt
        repeat_target = 1.0 if prior_cnt >= 3.0 else 0.0
        
        # Load from graph tables
        pr = pageranks.get(aid, 0.0)
        bet = betweennesses.get(aid, 0.0)
        deg = degrees.get(aid, 0.0)
        cls = closenesses.get(aid, 0.0)
        bs = bridge_scores.get(aid, 0.0)
        comm = float(communities.get(aid, -1))
        comm_size = float(community_sizes.get(aid, 0.0))
        comp = float(components.get(aid, -1))
        
        # Rankings
        rank = float(pr_ranks.get(aid, 99999.0))
        
        # Custom risk/gang scores
        gang = min(1.0, pr * 10.0 + comm_size * 0.05)
        risk = prior_cnt * 1.5 + severity_sums.get(aid, 0.0) * 0.5
        org_crime = min(1.0, gang * 0.7 + bs * 0.3)
        
        results[aid] = {
            "prior_case_count": prior_cnt,
            "repeat_offender_count": repeat_cnt,
            "community_score": comm,
            "community_size": comm_size,
            "pagerank_score": pr,
            "betweenness_score": bet,
            "degree_centrality": deg,
            "closeness": cls,
            "component_id": comp,
            "bridge_score": bs,
            "gang_score": gang,
            "risk_factor_score": risk,
            "organized_crime_score": org_crime,
            "centrality_rank": rank,
            "repeat_offender_target": repeat_target
        }
        
    return results
