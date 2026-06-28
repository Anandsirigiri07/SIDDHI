# backend/features/compute_hotspot_features.py
import datetime
import math
import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models import FIR, HotspotCluster
from backend.config.crime_weights import CRIME_SEVERITY

def to_date(dt):
    import datetime
    if isinstance(dt, str):
        return datetime.datetime.strptime(dt.split()[0], "%Y-%m-%d").date()
    if isinstance(dt, datetime.datetime):
        return dt.date()
    return dt

def compute_hotspot_features_all(db: Session) -> dict:
    """
    Computes spatial hotspot clusters using DBSCAN,
    calculates density, trends, and future growth targets,
    and persists them to hotspot_clusters.
    """
    # Clear existing hotspot clusters
    db.execute(text("DELETE FROM hotspot_clusters"))
    db.commit()

    # 1. Fetch all cases with locations
    cases = db.query(FIR).filter(FIR.latitude.isnot(None), FIR.longitude.isnot(None)).all()
    if not cases:
        return {}

    # Define MLOps split point for target label calculation
    # Latest date in seeder is 2026-06-07. Let's split at 2026-05-31.
    T_ref = datetime.date(2026, 5, 31)
    
    current_cases = []
    future_cases = []
    
    for c in cases:
        reg_date = to_date(c.CrimeRegisteredDate)
        if reg_date <= T_ref:
            current_cases.append(c)
        elif reg_date <= T_ref + datetime.timedelta(days=7):
            future_cases.append(c)

    if not current_cases:
        current_cases = cases # fallback

    # Extract coordinates
    coords = np.array([[c.latitude, c.longitude] for c in current_cases])
    
    # Run DBSCAN (eps = 500 meters = 0.5 km)
    kms_per_radian = 6371.0
    epsilon = 0.5 / kms_per_radian
    coords_rad = np.radians(coords)
    
    db_scan = DBSCAN(eps=epsilon, min_samples=10, metric='haversine').fit(coords_rad)
    labels = db_scan.labels_
    
    unique_labels = set(labels)
    if -1 in unique_labels:
        unique_labels.remove(-1) # ignore noise
        
    results = {}
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Map repeat suspects
    repeat_suspects = set()
    rep_rows = db.execute(text("""
        SELECT accused_id FROM fir_accused 
        GROUP BY accused_id HAVING COUNT(fir_id) >= 3
    """)).fetchall()
    for (aid,) in rep_rows:
        repeat_suspects.add(aid)

    def get_haversine_dist(lat1, lng1, lat2, lng2):
        d_lat = math.radians(lat2 - lat1)
        d_lng = math.radians(lng2 - lng1)
        a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return 6371.0 * c

    for label in unique_labels:
        # Get all incidents in this cluster
        indices = np.where(labels == label)[0]
        cluster_incidents = [current_cases[i] for i in indices]
        
        # Compute Centroid
        cluster_coords = coords[indices]
        centroid_lat = float(np.mean(cluster_coords[:, 0]))
        centroid_lng = float(np.mean(cluster_coords[:, 1]))
        
        c_size = len(cluster_incidents)
        
        # Estimate area: convex hull or bounding box. Let's use variance radius area
        lats = cluster_coords[:, 0]
        lngs = cluster_coords[:, 1]
        lat_range = max(lats) - min(lats)
        lng_range = max(lngs) - min(lngs)
        # Approximate area of bounding box in km
        area_km2 = max(0.05, (lat_range * 111.0) * (lng_range * 111.0 * math.cos(math.radians(centroid_lat))))
        density = float(c_size / area_km2)
        
        # Mean severity
        sev_density = float(np.mean([CRIME_SEVERITY.get(c.crime_type, 4.0) for c in cluster_incidents]))
        
        # Repeat offender density
        accused_in_cluster = []
        for c in cluster_incidents:
            acc_rows = db.execute(text(f"SELECT accused_id FROM fir_accused WHERE fir_id = {c.fir_id}")).fetchall()
            accused_in_cluster.extend([row[0] for row in acc_rows])
            
        rep_density = 0.0
        if accused_in_cluster:
            rep_cnt = sum(1 for aid in accused_in_cluster if aid in repeat_suspects)
            rep_density = float(rep_cnt / len(accused_in_cluster))
            
        # Cluster risk
        risk = float(c_size * 0.4 + density * 0.2 + sev_density * 0.3 + rep_density * 0.1 * 10.0)
        
        # Historical baseline weekly crimes (approx 3 years / 156 weeks)
        hist_baseline = float(c_size / 156.0)
        
        # Weekly change (crimes in the last 7 days of historical part, i.e. 2026-05-24 to 2026-05-31)
        w_crimes = sum(1 for c in cluster_incidents if T_ref - datetime.timedelta(days=7) <= to_date(c.CrimeRegisteredDate) <= T_ref)
        w_change = float(w_crimes - hist_baseline)
        
        # Emerging hotspot score
        emerging = 1.0 if w_change >= 2.0 * hist_baseline else 0.0
        
        # Target label: future crimes in the next 7 days in the cluster area (centroid + 0.5 km radius)
        f_size = 0
        for fc in future_cases:
            dist = get_haversine_dist(centroid_lat, centroid_lng, fc.latitude, fc.longitude)
            if dist <= 0.5:
                f_size += 1
                
        f_growth = f_size - w_crimes
        
        # Save to database
        db_cluster = HotspotCluster(
            cluster_id=int(label),
            cluster_size=int(c_size),
            crime_density=density,
            centroid_lat=centroid_lat,
            centroid_lng=centroid_lng,
            cluster_risk=risk,
            repeat_offender_density=rep_density,
            severity_density=sev_density,
            emerging_hotspot_score=emerging,
            historical_baseline=hist_baseline,
            weekly_change=w_change,
            future_cluster_size=int(f_size),
            weekly_growth=int(f_growth),
            updated_at=now_str
        )
        db.add(db_cluster)
        
        results[int(label)] = {
            "cluster_size": float(c_size),
            "crime_density": density,
            "cluster_risk": risk,
            "repeat_offender_density": rep_density,
            "severity_density": sev_density,
            "historical_baseline": hist_baseline,
            "weekly_change": w_change,
            "emerging_cluster": emerging,
            "future_cluster_size": float(f_size),
            "weekly_growth": float(f_growth),
            "hotspot_growth_target": float(f_growth)
        }
        
    db.commit()
    return results
