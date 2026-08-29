# backend/ml/chrono_engine.py
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from backend.database import engine

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def get_chrono_matrix(
    crime_type: Optional[str] = None,
    district: Optional[str] = None,
    location_id: Optional[int] = None,
    accused_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Computes Day-of-Week x Crime Category Temporal Matrix from siddhi.db FIR records.
    
    Mandatory Rule #2: FIR records contain date-only timestamps (YYYY-MM-DD).
    This engine NEVER manufactures hours/shifts. It aggregates date-only records into 
    Day-of-Week frequencies and seasonal trends, returning explicit date-only disclaimers.
    """
    query_parts = ["""
        SELECT f.fir_id, f.date, f.crime_type, f.location_id, l.district, l.name as loc_name, f.description
        FROM firs f
        LEFT JOIN locations l ON f.location_id = l.location_id
    """]
    conds = []
    params: Dict[str, Any] = {}

    if accused_id:
        query_parts.append("JOIN fir_accused fa ON f.fir_id = fa.fir_id")
        conds.append("fa.accused_id = :aid")
        params["aid"] = accused_id

    if crime_type:
        conds.append("LOWER(f.crime_type) = :ctype")
        params["ctype"] = crime_type.lower()

    if district:
        conds.append("LOWER(l.district) LIKE :dist")
        params["dist"] = f"%{district.lower()}%"

    if location_id:
        conds.append("f.location_id = :lid")
        params["lid"] = location_id

    if conds:
        query_parts.append("WHERE " + " AND ".join(conds))

    query_sql = " ".join(query_parts)

    with engine.connect() as conn:
        rows = conn.execute(text(query_sql), params).fetchall()

    if not rows:
        return {
            "total_incidents_analyzed": 0,
            "day_of_week_matrix": [],
            "peak_day": None,
            "temporal_concentration": "LOW",
            "disclaimer": "Time-of-day breakdown unavailable (FIR records contain date-only timestamps).",
            "message": "No matching FIR records for temporal analysis."
        }

    # Initialize Day-of-Week frequency counter
    day_counts: Dict[str, int] = {d: 0 for d in DAYS_OF_WEEK}
    crime_type_counts: Dict[str, int] = {}
    day_crime_matrix: Dict[str, Dict[str, int]] = {d: {} for d in DAYS_OF_WEEK}
    active_years: set = set()

    for r in rows:
        date_str = r[1]
        c_type = r[2].replace("_", " ").title() if r[2] else "General Crime"
        crime_type_counts[c_type] = crime_type_counts.get(c_type, 0) + 1

        if date_str and len(date_str) >= 10:
            try:
                dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                dow = DAYS_OF_WEEK[dt.weekday()]
                day_counts[dow] += 1
                day_crime_matrix[dow][c_type] = day_crime_matrix[dow].get(c_type, 0) + 1
                active_years.add(dt.year)
            except ValueError:
                pass

    total_incidents = len(rows)
    sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)
    peak_day, peak_count = sorted_days[0] if sorted_days else ("N/A", 0)
    peak_pct = round((peak_count / max(1, total_incidents)) * 100.0, 1)

    # Determine Temporal Concentration (Gini/Entropy approximation)
    if peak_pct >= 25.0:
        concentration = "HIGH"
    elif peak_pct >= 18.0:
        concentration = "MODERATE"
    else:
        concentration = "BALANCED"

    # Build response matrix format
    matrix_cells = []
    for dow in DAYS_OF_WEEK:
        cnt = day_counts[dow]
        pct = round((cnt / max(1, total_incidents)) * 100.0, 1)
        matrix_cells.append({
            "day": dow,
            "incident_count": cnt,
            "percentage": pct,
            "crime_breakdown": day_crime_matrix[dow]
        })

    year_range_str = f"{min(active_years)}–{max(active_years)}" if active_years else "Active Period"

    # Pattern summary with defensible wording per Mandatory Rule #3 & #10
    summary_text = (
        f"Observed historical pattern across {total_incidents} FIR records ({year_range_str}): "
        f"Peak activity occurs on {peak_day}s ({peak_count} incidents, {peak_pct}% of total). "
        f"Overall temporal concentration is {concentration}."
    )

    return {
        "total_incidents_analyzed": total_incidents,
        "active_year_range": year_range_str,
        "peak_day": peak_day,
        "peak_day_incident_count": peak_count,
        "peak_day_percentage": peak_pct,
        "temporal_concentration": concentration,
        "day_of_week_matrix": matrix_cells,
        "summary": summary_text,
        "disclaimer": "Time-of-day breakdown unavailable (FIR records contain date-only timestamps)."
    }
