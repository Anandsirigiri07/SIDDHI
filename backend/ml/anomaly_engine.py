# backend/ml/anomaly_engine.py
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import text
from backend.database import engine

def detect_crime_anomalies(district_filter: str = None) -> List[Dict[str, Any]]:
    """
    Detects spatial locations where recent 7-day crime activity is unusually high 
    compared to their historical 30-day baseline (Z-Score > 1.75).
    Distinguishes 'Unusually High Crime' (Anomalous Spike) from simple high volume.
    """
    query = """
        SELECT f.fir_id, f.date, f.crime_type, l.location_id, l.name as loc_name, l.district, l.lat, l.lng
        FROM firs f
        JOIN locations l ON f.location_id = l.location_id
    """
    if district_filter:
        query += " WHERE LOWER(l.district) = LOWER(:district)"
        
    with engine.connect() as conn:
        params = {"district": district_filter} if district_filter else {}
        rows = conn.execute(text(query), params).fetchall()

    if not rows:
        return []

    # System evaluation date reference
    ref_date = datetime(2026, 6, 7)
    seven_days_ago = ref_date - timedelta(days=7)
    thirty_days_ago = ref_date - timedelta(days=30)

    # Group incidents by location_id
    loc_incidents: Dict[int, List[Dict[str, Any]]] = {}
    for r in rows:
        try:
            d = datetime.strptime(r[1], "%Y-%m-%d")
        except Exception:
            continue
            
        lid = r[3]
        if lid not in loc_incidents:
            loc_incidents[lid] = []
            
        loc_incidents[lid].append({
            "fir_id": r[0],
            "date": d,
            "crime_type": r[2],
            "loc_name": r[4],
            "district": r[5],
            "lat": float(r[6]),
            "lng": float(r[7])
        })

    anomalies = []

    for lid, items in loc_incidents.items():
        # Current 7-day window
        recent_7d = [i for i in items if i["date"] >= seven_days_ago]
        current_count = len(recent_7d)
        
        # Historical baseline window (30 days prior)
        historical_items = [i for i in items if thirty_days_ago <= i["date"] < seven_days_ago]
        
        # Weekly incident counts in historical period (3 weeks)
        # Calculate weekly mean (mu) and standard deviation (sigma)
        total_historical = len(historical_items)
        weekly_mu = max(0.5, total_historical / 3.0)
        
        # Approximate standard deviation from 3 weekly buckets
        w1 = sum(1 for i in historical_items if thirty_days_ago <= i["date"] < thirty_days_ago + timedelta(days=7))
        w2 = sum(1 for i in historical_items if thirty_days_ago + timedelta(days=7) <= i["date"] < thirty_days_ago + timedelta(days=14))
        w3 = sum(1 for i in historical_items if thirty_days_ago + timedelta(days=14) <= i["date"] < thirty_days_ago + timedelta(days=21))
        
        weekly_counts = [w1, w2, w3]
        raw_sigma = float(np.std(weekly_counts)) if len(weekly_counts) > 0 else 1.0
        sigma = max(raw_sigma, 1.2, 0.25 * weekly_mu) # Effective standard deviation floor
        
        # Z-Score Calculation (clamped to 5.0 max display bounds)
        raw_z = (current_count - weekly_mu) / sigma
        z_score = round(min(5.0, float(raw_z)), 2)
        deviation_pct = round(((current_count - weekly_mu) / weekly_mu) * 100.0, 1) if weekly_mu > 0 else 100.0

        # Anomaly threshold: current_count >= 3 AND Z-Score >= 1.75
        if current_count >= 3 and z_score >= 1.75:
            # Determine primary crime type driver
            crime_counts: Dict[str, int] = {}
            for i in recent_7d:
                crime_counts[i["crime_type"]] = crime_counts.get(i["crime_type"], 0) + 1
            primary_driver = max(crime_counts, key=crime_counts.get).replace("_", " ").title() if crime_counts else "General Offense"
            
            severity = "CRITICAL" if z_score >= 2.5 else "MODERATE"
            
            anomalies.append({
                "location_id": lid,
                "location_name": items[0]["loc_name"],
                "district": items[0]["district"],
                "lat": items[0]["lat"],
                "lng": items[0]["lng"],
                "current_7d_incidents": current_count,
                "historical_weekly_avg": round(weekly_mu, 1),
                "deviation_pct": max(0.0, deviation_pct),
                "z_score": round(float(z_score), 2),
                "severity": severity,
                "primary_driver": primary_driver,
                "supporting_fir_ids": [i["fir_id"] for i in recent_7d],
                "explanation": f"{items[0]['loc_name']} has recorded {current_count} incidents in the last 7 days (+{deviation_pct}% over historical weekly avg of {weekly_mu:.1f}). Primary driver: {primary_driver}."
            })

    # Sort highest Z-score first
    anomalies.sort(key=lambda x: x["z_score"], reverse=True)
    return anomalies
