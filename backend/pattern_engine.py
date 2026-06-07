# backend/pattern_engine.py
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sklearn.cluster import DBSCAN
from sqlalchemy import text
from backend.database import engine
from backend.config.crime_weights import CRIME_SEVERITY

def calculate_weekly_baseline(total_crimes: int, start_date_str: str, end_date_str: str) -> float:
    """Calculates expected average weekly crime count over the historical range."""
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d")
        days = (end - start).days
        weeks = max(1.0, days / 7.0)
        return float(total_crimes / weeks)
    except Exception:
        return 1.0

def detect_hotspots(sql_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Groups crime incidents using DBSCAN spatial clustering on query-filtered results (eps=0.5km).
    Enriches coordinates from locations if missing.
    Calculates hotspot risk scores and early warning alerts.
    """
    if not sql_results:
        return {"geojson": {"type": "FeatureCollection", "features": []}, "alerts": []}

    # Step 1: Ensure all rows have lat, lng, and loc_name by querying locations mapping if missing
    enriched_results = []
    
    with engine.connect() as conn:
        # Get locations mapping
        loc_res = conn.execute(text("SELECT location_id, lat, lng, name FROM locations")).fetchall()
        loc_map = {row[0]: {"lat": row[1], "lng": row[2], "loc_name": row[3]} for row in loc_res}
        
        # Get repeat offender list
        repeat_accused_query = conn.execute(text("SELECT accused_id FROM fir_accused GROUP BY accused_id HAVING COUNT(fir_id) > 1")).fetchall()
        repeat_accused_ids = set([row[0] for row in repeat_accused_query])
        
        # Get accused mapping for each FIR
        fir_acc_res = conn.execute(text("SELECT fir_id, accused_id FROM fir_accused")).fetchall()
        fir_accused_map = {}
        for row in fir_acc_res:
            fid, aid = row
            if fid not in fir_accused_map:
                fir_accused_map[fid] = []
            fir_accused_map[fid].append(aid)

    for row in sql_results:
        # Extract location_id from row
        lid = row.get("location_id")
        lat = row.get("lat")
        lng = row.get("lng")
        loc_name = row.get("loc_name") or row.get("name")
        
        # If coordinates are missing, try to resolve via location_id or loc_name
        if (lat is None or lng is None) and lid in loc_map:
            lat = loc_map[lid]["lat"]
            lng = loc_map[lid]["lng"]
            loc_name = loc_map[lid]["loc_name"]
        elif (lat is None or lng is None) and loc_name:
            # Try to match loc_name in loc_map
            for l_info in loc_map.values():
                if loc_name.lower() in l_info["loc_name"].lower():
                    lat = l_info["lat"]
                    lng = l_info["lng"]
                    loc_name = l_info["loc_name"]
                    break

        # If we still don't have coordinates, skip this row for spatial clustering
        if lat is None or lng is None:
            continue
            
        enriched_row = {
            "fir_id": row.get("fir_id") or row.get("id"),
            "fir_number": row.get("fir_number"),
            "date": row.get("date") or "2026-06-01",
            "crime_type": row.get("crime_type") or "burglary",
            "lat": float(lat),
            "lng": float(lng),
            "loc_name": loc_name or "Unknown Location"
        }
        enriched_results.append(enriched_row)

    if not enriched_results:
        return {"geojson": {"type": "FeatureCollection", "features": []}, "alerts": []}

    # Extract coordinates for DBSCAN
    coords = np.array([[f["lat"], f["lng"]] for f in enriched_results])
    
    # 0.5km is approximately 0.0045 degrees
    eps_degrees = 0.0045
    min_samples = min(3, len(coords))
    if min_samples < 1:
        min_samples = 1

    dbscan = DBSCAN(eps=eps_degrees, min_samples=min_samples).fit(coords)
    labels = dbscan.labels_

    # Group enriched incidents by cluster labels
    clusters: Dict[int, List[Dict[str, Any]]] = {}
    for idx, label in enumerate(labels):
        if label == -1 and len(coords) >= 3:
            continue # Noise points are ignored ONLY if there are enough points to form real clusters
        # If len(coords) < 3, labels will be 0 or -1, but we treat them all as clusters to show them on the map
        actual_label = label if label != -1 else 0
        if actual_label not in clusters:
            clusters[actual_label] = []
        clusters[actual_label].append(enriched_results[idx])

    geojson_features = []
    alerts = []
    
    current_date = datetime(2026, 6, 7) # Fixed current date from system metadata
    thirty_days_ago = current_date - timedelta(days=30)
    seven_days_ago = current_date - timedelta(days=7)

    # Global range for baseline calculations
    dates = [datetime.strptime(f["date"], "%Y-%m-%d") for f in enriched_results]
    min_date = min(dates).strftime("%Y-%m-%d")
    max_date = max(dates).strftime("%Y-%m-%d")

    # Process each cluster
    for label, fir_list in clusters.items():
        cluster_coords = np.array([[f["lat"], f["lng"]] for f in fir_list])
        centroid = cluster_coords.mean(axis=0)

        # 1. Incident Count
        incident_count = len(fir_list)

        # 2. Frequency Weight
        recent_count = sum(1 for f in fir_list if datetime.strptime(f["date"], "%Y-%m-%d") >= thirty_days_ago)
        frequency_weight = 1.0 + (recent_count / 10.0)

        # 3. Crime Severity Weight
        severities = [CRIME_SEVERITY.get(f["crime_type"], 2) for f in fir_list]
        severity_weight = float(np.mean(severities)) if severities else 2.0

        # 4. Repeat Offender Weight
        cluster_accused_ids = set()
        for f in fir_list:
            a_ids = fir_accused_map.get(f["fir_id"], [])
            cluster_accused_ids.update(a_ids)
            
        cluster_repeat_accused_count = sum(1 for aid in cluster_accused_ids if aid in repeat_accused_ids)
        repeat_offender_weight = 1.0 + (0.5 * cluster_repeat_accused_count)

        # Calculate Risk Score
        risk_score = round(incident_count * frequency_weight * severity_weight * repeat_offender_weight, 2)

        # Categorize Severity Level
        if risk_score > 100:
            severity_level = "High"
        elif risk_score > 30:
            severity_level = "Amber"
        else:
            severity_level = "Low"

        # Determine dominant crime
        crime_counts = {}
        for f in fir_list:
            crime_counts[f["crime_type"]] = crime_counts.get(f["crime_type"], 0) + 1
        dominant_crime = max(crime_counts, key=crime_counts.get).replace("_", " ").title()

        f_ids = [f["fir_id"] for f in fir_list]
        loc_name = fir_list[0]["loc_name"]

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(centroid[1]), float(centroid[0])] # GeoJSON [lng, lat]
            },
            "properties": {
                "cluster_id": int(label),
                "location_name": loc_name,
                "risk_score": risk_score,
                "crime_count": incident_count,
                "dominant_crime": dominant_crime,
                "severity": severity_level,
                "fir_ids": f_ids,
                "date_range": f"{min(f['date'] for f in fir_list)} to {max(f['date'] for f in fir_list)}"
            }
        }
        geojson_features.append(feature)

        # --- Spike Detection Check ---
        last_7_days_crimes = sum(1 for f in fir_list if datetime.strptime(f["date"], "%Y-%m-%d") >= seven_days_ago)
        expected_weekly_baseline = calculate_weekly_baseline(incident_count, min_date, max_date)
        
        # Trigger spike alerts if 7-day crime exceeds baseline significantly
        if last_7_days_crimes >= 2 and last_7_days_crimes > 1.8 * expected_weekly_baseline:
            alerts.append({
                "type": "SPIKE",
                "message": f"{loc_name} cluster spike detected: {last_7_days_crimes} crimes in the last 7 days exceeds baseline of {expected_weekly_baseline:.1f}.",
                "severity": "High" if last_7_days_crimes >= 4 else "Medium"
            })

    geojson = {
        "type": "FeatureCollection",
        "features": geojson_features
    }

    return {
        "geojson": geojson,
        "alerts": alerts
    }
