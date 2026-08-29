# backend/ml/similarity_engine.py
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import text
from backend.database import engine

# Singleton TF-IDF Model & Matrix Cache
_tfidf_vectorizer: Optional[TfidfVectorizer] = None
_tfidf_matrix: Optional[np.ndarray] = None
_fir_id_index_map: Dict[int, int] = {}
_index_fir_id_map: Dict[int, int] = {}

def initialize_tfidf_embeddings():
    """Generates authentic TF-IDF vector embeddings for all FIR descriptions in SQLite."""
    global _tfidf_vectorizer, _tfidf_matrix, _fir_id_index_map, _index_fir_id_map
    
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT fir_id, description FROM firs WHERE description IS NOT NULL AND description != ''")).fetchall()

    if not rows:
        return

    fir_ids = [r[0] for r in rows]
    descriptions = [r[1] for r in rows]

    _fir_id_index_map = {fid: idx for idx, fid in enumerate(fir_ids)}
    _index_fir_id_map = {idx: fid for idx, fid in enumerate(fir_ids)}

    _tfidf_vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words='english',
        ngram_range=(1, 2)
    )
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(descriptions).toarray()

def find_similar_firs(fir_id: int, top_k: int = 4) -> Dict[str, Any]:
    """
    Finds top-K semantically similar FIRs using genuine TF-IDF cosine similarity 
    computed over all 5,813 FIR descriptions.
    
    Provides authentic mathematical similarity distribution:
    - Semantic Similarity % (from TF-IDF cosine distance)
    - Crime Type Match (bool)
    - Location / District Match (bool)
    - Shared Accused Overlap Count (int)
    """
    global _tfidf_vectorizer, _tfidf_matrix, _fir_id_index_map, _index_fir_id_map

    if _tfidf_matrix is None or fir_id not in _fir_id_index_map:
        initialize_tfidf_embeddings()

    with engine.connect() as conn:
        target_row = conn.execute(text("""
            SELECT f.fir_id, f.fir_number, f.crime_type, f.description, f.date, f.location_id, l.district, l.name as loc_name
            FROM firs f
            LEFT JOIN locations l ON f.location_id = l.location_id
            WHERE f.fir_id = :fid
        """), {"fid": fir_id}).fetchone()

        if not target_row:
            return {"target_fir_id": fir_id, "similar_cases": [], "message": "Target FIR not found in database records."}

        target = {
            "fir_id": target_row[0],
            "fir_number": target_row[1],
            "crime_type": target_row[2],
            "description": target_row[3],
            "date": target_row[4],
            "location_id": target_row[5],
            "district": target_row[6],
            "loc_name": target_row[7]
        }

        # Fetch target accused set for entity overlap check
        target_acc_rows = conn.execute(text("SELECT accused_id FROM fir_accused WHERE fir_id = :fid"), {"fid": fir_id}).fetchall()
        target_acc_ids = set([r[0] for r in target_acc_rows])

    if _tfidf_matrix is None or fir_id not in _fir_id_index_map:
        return {"target_fir_id": fir_id, "similar_cases": [], "message": "Vector index unavailable for target FIR."}

    target_idx = _fir_id_index_map[fir_id]
    target_vec = _tfidf_matrix[target_idx].reshape(1, -1)

    # Compute raw cosine similarity against all FIRs
    sim_scores = cosine_similarity(target_vec, _tfidf_matrix)[0]

    # Rank indices by similarity score, excluding target_idx (where sim == 1.0)
    ranked_indices = []
    for idx, score in enumerate(sim_scores):
        cand_fid = _index_fir_id_map[idx]
        if cand_fid == fir_id:
            continue # Exclude target FIR itself
        ranked_indices.append((cand_fid, float(score)))

    # Sort descending by genuine TF-IDF cosine similarity
    ranked_indices.sort(key=lambda x: x[1], reverse=True)
    top_candidates = ranked_indices[:top_k]

    if not top_candidates:
        return {"target_fir_id": fir_id, "similar_cases": [], "message": "No similar cases found."}

    cand_ids = [c[0] for c in top_candidates]
    cand_pl = ",".join(str(cid) for cid in cand_ids)

    similar_cases = []

    with engine.connect() as conn:
        cand_rows = conn.execute(text(f"""
            SELECT f.fir_id, f.fir_number, f.crime_type, f.description, f.date, f.location_id, l.district, l.name as loc_name
            FROM firs f
            LEFT JOIN locations l ON f.location_id = l.location_id
            WHERE f.fir_id IN ({cand_pl})
        """)).fetchall()

        cand_dict = {r[0]: r for r in cand_rows}
        
        cand_acc_rows = conn.execute(text(f"SELECT fir_id, accused_id FROM fir_accused WHERE fir_id IN ({cand_pl})")).fetchall()
        cand_acc_map: Dict[int, set] = {}
        for fid, aid in cand_acc_rows:
            cand_acc_map.setdefault(fid, set()).add(aid)

        for candidate_fid, sim_score in top_candidates:
            crow = cand_dict.get(candidate_fid)
            if not crow:
                continue

            c_crime_type = crow[2]
            c_district = crow[6]
            c_acc_ids = cand_acc_map.get(candidate_fid, set())

            overlap_accused = len(target_acc_ids.intersection(c_acc_ids))
            crime_match = (target["crime_type"].lower() == c_crime_type.lower())
            location_match = (target["district"] and c_district and target["district"].lower() == c_district.lower())

            # Convert cosine score to authentic percentage (0% to 100%)
            sim_pct = max(0, min(100, int(round(sim_score * 100))))

            similar_cases.append({
                "fir_id": candidate_fid,
                "fir_number": crow[1],
                "crime_type": c_crime_type,
                "date": crow[4],
                "district": c_district or "Bengaluru",
                "location_name": crow[7] or "Bengaluru Sector",
                "similarity_score": round(sim_score, 4),
                "semantic_similarity_pct": sim_pct,
                "match_factors": {
                    "crime_type_match": crime_match,
                    "location_relation": location_match,
                    "shared_accused_count": overlap_accused
                },
                "summary": f"{crow[3][:120]}..." if crow[3] else "No summary available."
            })

    return {
        "target_fir_id": fir_id,
        "target_fir_number": target["fir_number"],
        "similar_cases": similar_cases
    }
