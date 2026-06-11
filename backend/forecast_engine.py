# backend/forecast_engine.py
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from sklearn.cluster import DBSCAN
from sqlalchemy import text
from backend.database import engine
from backend.config.crime_weights import CRIME_SEVERITY

SMOOTHING_ALPHA = 0.4   # Exponential smoothing factor (recent weeks weigh more)
EPS_DEGREES = 0.0045    # ~0.5km, matches pattern_engine clustering
TREND_THRESHOLD = 0.15  # +/-15% vs historical average marks Rising/Declining

def _weekly_counts(dates: List[datetime], start: datetime, end: datetime) -> List[int]:
    """Buckets incident dates into consecutive 7-day windows from start to end."""
    n_weeks = max(1, int(np.ceil(((end - start).days + 1) / 7.0)))
    counts = [0] * n_weeks
    for d in dates:
        idx = min(n_weeks - 1, (d - start).days // 7)
        counts[idx] += 1
    return counts

def _exponential_smoothing(counts: List[int], alpha: float = SMOOTHING_ALPHA) -> float:
    """Forecasts the next value using simple exponential smoothing."""
    level = float(counts[0])
    for c in counts[1:]:
        level = alpha * c + (1 - alpha) * level
    return level

def forecast_hotspots(horizon_days: int = 7) -> Dict[str, Any]:
    """
    Predicts next-week hotspot intensity per spatial cluster.
    Clusters all FIRs with DBSCAN, builds a weekly time series per cluster,
    and forecasts the coming week via exponential smoothing (baseline model;
    see issue #3 for planned heavier temporal models).
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT f.fir_id, f.date, f.crime_type, l.lat, l.lng, l.name
            FROM firs f
            JOIN locations l ON f.location_id = l.location_id
        """)).fetchall()

    incidents = []
    for r in rows:
        try:
            incidents.append({
                "fir_id": r[0],
                "date": datetime.strptime(r[1], "%Y-%m-%d"),
                "crime_type": r[2],
                "lat": float(r[3]),
                "lng": float(r[4]),
                "loc_name": r[5],
            })
        except (TypeError, ValueError):
            continue

    if not incidents:
        return {
            "type": "FeatureCollection",
            "features": [],
            "generated_at": datetime.now().isoformat(),
            "horizon_days": horizon_days,
        }

    coords = np.array([[i["lat"], i["lng"]] for i in incidents])
    labels = DBSCAN(eps=EPS_DEGREES, min_samples=min(3, len(coords))).fit(coords).labels_

    clusters: Dict[int, List[Dict[str, Any]]] = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue  # Noise points carry no temporal signal worth forecasting
        clusters.setdefault(int(label), []).append(incidents[idx])

    start = min(i["date"] for i in incidents)
    end = max(i["date"] for i in incidents)

    features = []
    for label, items in clusters.items():
        dates = [i["date"] for i in items]
        counts = _weekly_counts(dates, start, end)
        historical_avg = float(np.mean(counts))
        predicted = _exponential_smoothing(counts)

        if historical_avg > 0 and predicted > historical_avg * (1 + TREND_THRESHOLD):
            trend = "Rising"
        elif historical_avg > 0 and predicted < historical_avg * (1 - TREND_THRESHOLD):
            trend = "Declining"
        else:
            trend = "Stable"

        severities = [CRIME_SEVERITY.get(i["crime_type"], 2) for i in items]
        severity_weight = float(np.mean(severities)) if severities else 2.0
        predicted_risk = round(predicted * severity_weight, 2)

        crime_counts: Dict[str, int] = {}
        for i in items:
            crime_counts[i["crime_type"]] = crime_counts.get(i["crime_type"], 0) + 1
        dominant_crime = max(crime_counts, key=crime_counts.get).replace("_", " ").title()

        centroid = np.array([[i["lat"], i["lng"]] for i in items]).mean(axis=0)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(centroid[1]), float(centroid[0])]  # GeoJSON [lng, lat]
            },
            "properties": {
                "cluster_id": label,
                "location_name": items[0]["loc_name"],
                "dominant_crime": dominant_crime,
                "historical_weekly_avg": round(historical_avg, 2),
                "predicted_weekly_incidents": round(predicted, 2),
                "predicted_risk_score": predicted_risk,
                "trend": trend,
                "observation_weeks": len(counts),
            }
        })

    # Highest predicted risk first
    features.sort(key=lambda f: f["properties"]["predicted_risk_score"], reverse=True)

    return {
        "type": "FeatureCollection",
        "features": features,
        "generated_at": datetime.now().isoformat(),
        "horizon_days": horizon_days,
    }
