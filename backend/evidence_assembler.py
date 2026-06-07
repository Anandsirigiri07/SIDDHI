# backend/evidence_assembler.py
import re
from typing import List, Dict, Any, Tuple

def attach_fir_citations(answer: str, sql_results: List[Dict[str, Any]]) -> Tuple[str, List[str], List[int]]:
    """
    Scans the answer for citation patterns like [FIR-2024-00102] using regex.
    Cross-references with actual SQL results to verify and compile a clean list of
    citations and database FIR IDs. Removes invalid citations from the text.
    """
    # Find citations matching [FIR-YYYY-XXXXX] or [FIR-YYYY-SPIKEXX]
    citation_regex = r'\[FIR-\d{4}-[A-Za-z0-9]+\]'
    found_citations = list(set(re.findall(citation_regex, answer)))
    
    # Extract FIR numbers and IDs present in the SQL results
    db_fir_map = {} # Maps FIR Number -> FIR ID
    for row in sql_results:
        fnum = row.get("fir_number")
        fid = row.get("fir_id") or row.get("id")
        if fnum and fid:
            db_fir_map[fnum] = fid

    verified_citations = []
    fir_ids = []

    # Map parsed text citations to database IDs and remove invalid ones from the text
    for cit in found_citations:
        fnum = cit.strip("[]")
        if fnum in db_fir_map:
            verified_citations.append(fnum)
            fir_ids.append(db_fir_map[fnum])
        else:
            # Remove invalid/hallucinated citation from text
            answer = answer.replace(cit, "")

    # Clean up any duplicated or trailing spaces caused by removal
    answer = re.sub(r'\s+', ' ', answer).strip()

    # If the answer fails to explicitly cite, but we have SQL results, append citation badges
    # to the end of the text to ensure evidence trail integrity
    if not verified_citations and db_fir_map:
        extra_citations = []
        # Append up to 5 citations to keep output clean
        for fnum, fid in list(db_fir_map.items())[:5]:
            extra_citations.append(f"[{fnum}]")
            verified_citations.append(fnum)
            fir_ids.append(fid)
        if extra_citations:
            answer = f"{answer}\n\nEvidence Trail: " + ", ".join(extra_citations)

    return answer, list(set(verified_citations)), list(set(fir_ids))

def build_evidence_payload(sql_query: str, explanation: str) -> Dict[str, Any]:
    """Wraps raw SQL and explanation metadata for explainability."""
    return {
        "sql_executed": sql_query,
        "explanation": explanation
    }

def create_audit_record(user_id: int, query_text: str, sql_executed: str, summary: str) -> Dict[str, Any]:
    """Generates the dictionary payload for logging to the database audit_logs table."""
    from datetime import datetime
    return {
        "user_id": user_id,
        "query_text": query_text,
        "sql_executed": sql_executed,
        "summary": summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_final_response(
    answer: str,
    sql_results: List[Dict[str, Any]],
    graph_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    sql_query: str,
    explanation: str
) -> Dict[str, Any]:
    """
    Merges analytical outputs (conversational answer, graph structures, heatmap hotspots)
    into the unified Triple-Lens API response contracts.
    """
    clean_answer, citations, fir_ids = attach_fir_citations(answer, sql_results)
    
    evidence = build_evidence_payload(sql_query, explanation)
    alerts = pattern_data.get("alerts", [])
    
    return {
        "answer": clean_answer,
        "graph": graph_data,
        "heatmap": pattern_data.get("geojson", {"type": "FeatureCollection", "features": []}),
        "alerts": alerts,
        "citations": citations,
        "fir_ids": fir_ids,
        "evidence": evidence,
        "sql_executed": sql_query
    }
