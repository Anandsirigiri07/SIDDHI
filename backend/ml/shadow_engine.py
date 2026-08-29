# backend/ml/shadow_engine.py
from typing import List, Dict, Any, Optional
import networkx as nx
from sqlalchemy import text
from backend.database import engine

def find_shadow_associations(target_accused_id: int, max_results: int = 5) -> Dict[str, Any]:
    """
    Detects potential 2-hop indirect criminal associations (A --- X --- B) in siddhi.db.
    
    Mandatory Rules:
    - Rule #6: Strictly 2-hop indirect traversal to prevent combinatorial explosion.
    - Rule #8: Terminology is 'Association Score: X/100', NOT probability.
    - Rule #9: Quality Filter & Deduplication: Requires shared intermediary X PLUS at least 
      1 additional signal (location, crime, temporal, or community).
      Deduplicates multiple 2-hop paths (X, Y, Z) between A and B into ONE consolidated relationship.
    """
    with engine.connect() as conn:
        # 1. Fetch target accused details
        target_row = conn.execute(text("SELECT accused_id, name, risk_score FROM accused WHERE accused_id = :aid"), {"aid": target_accused_id}).fetchone()
        if not target_row:
            return {"target_accused_id": target_accused_id, "shadow_associations": [], "message": "Target accused not found."}

        target_name = target_row[1]

        # Fetch direct FIRs and direct co-accused (1-hop neighbors)
        target_fir_rows = conn.execute(text("SELECT fir_id FROM fir_accused WHERE accused_id = :aid"), {"aid": target_accused_id}).fetchall()
        target_fir_ids = set([r[0] for r in target_fir_rows])

        if not target_fir_ids:
            return {"target_accused_id": target_accused_id, "target_name": target_name, "shadow_associations": [], "message": "No direct FIR records found."}

        target_fir_pl = ",".join(str(fid) for fid in target_fir_ids)

        # 1-hop co-accused
        direct_co_rows = conn.execute(text(f"SELECT DISTINCT accused_id FROM fir_accused WHERE fir_id IN ({target_fir_pl}) AND accused_id != :aid"), {"aid": target_accused_id}).fetchall()
        direct_co_ids = set([r[0] for r in direct_co_rows])

        if not direct_co_ids:
            return {"target_accused_id": target_accused_id, "target_name": target_name, "shadow_associations": [], "message": "No direct co-accused intermediaries found."}

        # Fetch target attributes (crimes, locations, years)
        target_attr_rows = conn.execute(text(f"""
            SELECT f.crime_type, f.location_id, f.date, l.district
            FROM firs f
            LEFT JOIN locations l ON f.location_id = l.location_id
            WHERE f.fir_id IN ({target_fir_pl})
        """)).fetchall()

        target_crimes = set([r[0].lower() for r in target_attr_rows if r[0]])
        target_locations = set([r[1] for r in target_attr_rows if r[1]])
        target_districts = set([r[3].lower() for r in target_attr_rows if r[3]])
        
        target_years = set()
        for r in target_attr_rows:
            if r[2] and len(r[2]) >= 4:
                try:
                    target_years.add(int(r[2][:4]))
                except ValueError:
                    pass

        # 2-hop candidate expansion: Find accused B connected to direct co-accused X
        direct_co_pl = ",".join(str(cid) for cid in direct_co_ids)
        
        # Intermediary FIRs of 1-hop co-accused
        inter_fir_rows = conn.execute(text(f"SELECT fir_id, accused_id FROM fir_accused WHERE accused_id IN ({direct_co_pl})")).fetchall()
        
        # Map: intermediary_accused_id -> set of their FIRs
        inter_acc_firs: Dict[int, set] = {}
        inter_fir_ids: set = set()
        for fid, aid in inter_fir_rows:
            inter_acc_firs.setdefault(aid, set()).add(fid)
            inter_fir_ids.add(fid)

        if not inter_fir_ids:
            return {"target_accused_id": target_accused_id, "target_name": target_name, "shadow_associations": [], "message": "No 2-hop network paths found."}

        inter_fir_pl = ",".join(str(fid) for fid in list(inter_fir_ids)[:100])

        # 2-hop candidate suspects B (connected to intermediary FIRs, but NOT target or direct co-accused)
        cand_b_rows = conn.execute(text(f"""
            SELECT fa.accused_id, fa.fir_id, a.name, a.risk_score
            FROM fir_accused fa
            JOIN accused a ON fa.accused_id = a.accused_id
            WHERE fa.fir_id IN ({inter_fir_pl}) AND fa.accused_id != :aid
        """), {"aid": target_accused_id}).fetchall()

        # Map candidate_b_id -> { "name", "risk", "firs", "intermediaries": set() }
        cand_b_map: Dict[int, Dict[str, Any]] = {}

        for b_id, fir_id, b_name, b_risk in cand_b_rows:
            if b_id == target_accused_id or b_id in direct_co_ids:
                continue # Exclude target itself and direct 1-hop co-accused

            # Find which 1-hop co-accused X link to this FIR
            linking_intermediaries = [x_id for x_id, x_firs in inter_acc_firs.items() if fir_id in x_firs]

            if b_id not in cand_b_map:
                cand_b_map[b_id] = {
                    "cand_id": b_id,
                    "name": b_name,
                    "risk_score": b_risk,
                    "fir_ids": set([fir_id]),
                    "intermediary_ids": set(linking_intermediaries)
                }
            else:
                cand_b_map[b_id]["fir_ids"].add(fir_id)
                cand_b_map[b_id]["intermediary_ids"].update(linking_intermediaries)

        if not cand_b_map:
            return {"target_accused_id": target_accused_id, "target_name": target_name, "shadow_associations": [], "message": "No indirect associations detected."}

        # Fetch names for intermediary accused X
        all_inter_ids = set()
        for b_info in cand_b_map.values():
            all_inter_ids.update(b_info["intermediary_ids"])

        inter_names_map: Dict[int, str] = {}
        if all_inter_ids:
            all_inter_pl = ",".join(str(xid) for xid in all_inter_ids)
            iname_rows = conn.execute(text(f"SELECT accused_id, name FROM accused WHERE accused_id IN ({all_inter_pl})")).fetchall()
            inter_names_map = {r[0]: r[1] for r in iname_rows}

        shadow_associations = []

        # Evaluate candidate B for quality filtering and scoring
        for b_id, b_info in cand_b_map.items():
            b_fir_ids = b_info["fir_ids"]
            if not b_fir_ids:
                continue

            bfir_pl = ",".join(str(fid) for fid in b_fir_ids)
            b_attr_rows = conn.execute(text(f"""
                SELECT f.crime_type, f.location_id, f.date, l.district
                FROM firs f
                LEFT JOIN locations l ON f.location_id = l.location_id
                WHERE f.fir_id IN ({bfir_pl})
            """)).fetchall()

            b_crimes = set([r[0].lower() for r in b_attr_rows if r[0]])
            b_locations = set([r[1] for r in b_attr_rows if r[1]])
            b_districts = set([r[3].lower() for r in b_attr_rows if r[3]])
            
            b_years = set()
            for r in b_attr_rows:
                if r[2] and len(r[2]) >= 4:
                    try:
                        b_years.add(int(r[2][:4]))
                    except ValueError:
                        pass

            # Signal Scoring (Max 100 Points)
            # 1. Shared Intermediaries (Max 30 pts)
            inter_count = len(b_info["intermediary_ids"])
            pts_inter = round(min(30.0, inter_count * 15.0), 1)

            # 2. Location Overlap (Max 25 pts)
            shared_locs = target_locations.intersection(b_locations)
            shared_dists = target_districts.intersection(b_districts)
            if shared_locs:
                pts_loc = 25.0
            elif shared_dists:
                pts_loc = 15.0
            else:
                pts_loc = 0.0

            # 3. Crime Pattern Match (Max 20 pts)
            shared_crimes = target_crimes.intersection(b_crimes)
            if shared_crimes:
                pts_crime = round(min(20.0, (len(shared_crimes) / max(1, len(target_crimes))) * 20.0), 1)
            else:
                pts_crime = 0.0

            # 4. Community / Co-occurrence Proximity (Max 15 pts)
            pts_comm = 15.0 if (shared_dists and shared_crimes) else 5.0

            # 5. Temporal Alignment (Max 10 pts)
            shared_years = target_years.intersection(b_years)
            pts_temp = 10.0 if shared_years else 0.0

            # Mandatory Rule #9 Quality Filter: Surface ONLY if candidate has intermediary X AND at least 1 additional signal
            additional_signals_count = (1 if pts_loc > 0 else 0) + (1 if pts_crime > 0 else 0) + (1 if pts_temp > 0 else 0)
            if additional_signals_count == 0:
                continue # Skip weak single-intermediary links to prevent graph noise

            total_score = int(round(pts_inter + pts_loc + pts_crime + pts_comm + pts_temp))
            total_score = max(0, min(100, total_score))

            inter_names = [inter_names_map.get(xid, f"Suspect #{xid}") for xid in b_info["intermediary_ids"]]

            signals = [
                f"✓ {inter_count} shared associate(s): {', '.join(inter_names[:2])}",
                f"✓ Location overlap: {list(shared_dists) if shared_dists else 'Regional'}",
                f"✓ Crime pattern match: {list(shared_crimes) if shared_crimes else 'Cross-crime'}",
                f"✓ Temporal active period overlap ({list(shared_years) if shared_years else 'Historical'})"
            ]

            explanation = (
                f"Potential indirect association (Association Score {total_score}/100) between {target_name} and {b_info['name']} "
                f"via {inter_count} shared associate(s) ({', '.join(inter_names[:2])}) and {additional_signals_count} supporting signals."
            )

            shadow_associations.append({
                "person_a_id": target_accused_id,
                "person_a_name": target_name,
                "person_b_id": b_id,
                "person_b_name": b_info["name"],
                "person_b_risk_score": b_info["risk_score"],
                "association_score": total_score,
                "association_type": "INDIRECT_2_HOP",
                "shared_intermediary_ids": list(b_info["intermediary_ids"]),
                "shared_intermediary_names": inter_names,
                "supporting_signals": signals,
                "explanation": explanation
            })

        # Deduplicate & sort descending by association_score
        shadow_associations.sort(key=lambda x: x["association_score"], reverse=True)

    return {
        "target_accused_id": target_accused_id,
        "target_name": target_name,
        "shadow_associations": shadow_associations[:max_results]
    }
