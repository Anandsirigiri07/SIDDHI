# backend/features/compute_case_features.py
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models import FIR, Victim, FIRAccused, ActSectionAssociation, ChargesheetDetails, ArrestSurrender, Court
from backend.config.crime_weights import CRIME_SEVERITY

def compute_case_features_all(db: Session) -> dict:
    """
    Computes all case-level features and returns a dict mapping case_id to features.
    """
    # Fetch all cases
    cases = db.query(FIR).all()
    results = {}
    
    # 1. Pre-calculate district counts and court delays for efficiency
    now = datetime.date(2026, 6, 7) # anchor date matching seeder end
    
    # Calculate district monthly rates: (DistrictID, count)
    district_rates = {}
    dr_rows = db.execute(text("""
        SELECT PoliceStationID, COUNT(fir_id) FROM firs 
        WHERE CrimeRegisteredDate >= '2026-05-08' 
        GROUP BY PoliceStationID
    """)).fetchall()
    for unit_id, cnt in dr_rows:
        district_rates[unit_id] = float(cnt)
        
    # Calculate weekly incident rates per unit
    weekly_rates = {}
    wr_rows = db.execute(text("""
        SELECT PoliceStationID, COUNT(fir_id) FROM firs 
        WHERE CrimeRegisteredDate >= '2026-06-01' 
        GROUP BY PoliceStationID
    """)).fetchall()
    for unit_id, cnt in wr_rows:
        weekly_rates[unit_id] = float(cnt)
        
    # Calculate court delay baselines
    court_delays = {}
    court_rows = db.execute(text("""
        SELECT f.CourtID, AVG(JULIANDAY(c.csdate) - JULIANDAY(f.CrimeRegisteredDate)) 
        FROM firs f 
        JOIN ChargesheetDetails c ON f.fir_id = c.CaseMasterID 
        GROUP BY f.CourtID
    """)).fetchall()
    for cid, avg_d in court_rows:
        if avg_d:
            court_delays[cid] = float(avg_d)

    # Let's check repeat offenders mapping to quickly check if a case has repeat offenders
    repeat_suspects = set()
    rep_rows = db.execute(text("""
        SELECT accused_id FROM fir_accused 
        GROUP BY accused_id HAVING COUNT(fir_id) >= 3
    """)).fetchall()
    for (aid,) in rep_rows:
        repeat_suspects.add(aid)

    # 2. Extract hotspot centroids from DBSCAN table (if populated, else fallback)
    hotspots = []
    try:
        hotspots = db.execute(text("SELECT centroid_lat, centroid_lng FROM hotspot_clusters")).fetchall()
    except Exception:
        pass

    def get_min_hotspot_dist(lat, lng):
        if not hotspots or lat is None or lng is None:
            return 99.0 # default fallback distance
        import math
        min_d = 99.0
        for h_lat, h_lng in hotspots:
            # Haversine distance
            R = 6371.0 # earth radius km
            d_lat = math.radians(h_lat - lat)
            d_lng = math.radians(h_lng - lng)
            a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(h_lat)) * math.sin(d_lng / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist = R * c
            if dist < min_d:
                min_d = dist
        return min_d

    # 3. Calculate features for every case
    for c in cases:
        case_id = c.fir_id
        
        # Base database aggregates
        v_count = db.query(Victim).filter_by(fir_id=case_id).count()
        acc_ids = [r.accused_id for r in db.query(FIRAccused).filter_by(fir_id=case_id).all()]
        a_count = len(acc_ids)
        
        act_sec = db.query(ActSectionAssociation).filter_by(CaseMasterID=case_id).all()
        act_count = len(set(x.ActID for x in act_sec))
        sec_count = len(act_sec)
        
        severity = float(CRIME_SEVERITY.get(c.crime_type, 4.0))
        # Gravity Heinous = 1.0, Non-Heinous = 0.0
        gravity = 1.0 if c.crime_type in ["murder", "robbery", "women_crime"] else 0.0
        
        # Dates calculation
        reg_date = c.CrimeRegisteredDate
        if reg_date is None:
            reg_date = c.date
            
        if isinstance(reg_date, str):
            reg_date = datetime.datetime.strptime(reg_date.split()[0], "%Y-%m-%d").date()
        elif isinstance(reg_date, datetime.datetime):
            reg_date = reg_date.date()
            
        inv_age = float((now - reg_date).days) if reg_date else 0.0
        
        # Targets & delays
        cs_delay = -1.0
        cs = db.query(ChargesheetDetails).filter_by(CaseMasterID=case_id).first()
        if cs:
            cs_date = cs.csdate
            if isinstance(cs_date, str):
                cs_date = datetime.datetime.strptime(cs_date.split()[0], "%Y-%m-%d").date()
            elif isinstance(cs_date, datetime.datetime):
                cs_date = cs_date.date()
            cs_delay = float((cs_date - reg_date).days)
            
        arr_delay = -1.0
        arr = db.query(ArrestSurrender).filter_by(CaseMasterID=case_id).order_by(ArrestSurrender.ArrestSurrenderDate.asc()).first()
        if arr:
            arr_date = arr.ArrestSurrenderDate
            if isinstance(arr_date, str):
                arr_date = datetime.datetime.strptime(arr_date.split()[0], "%Y-%m-%d").date()
            elif isinstance(arr_date, datetime.datetime):
                arr_date = arr_date.date()
            arr_delay = float((arr_date - reg_date).days)
            
        c_delay = court_delays.get(c.CourtID, 180.0)
        
        # Spatial Hotspot distance
        h_dist = get_min_hotspot_dist(c.latitude, c.longitude)
        
        # Spatiotemporal rates
        d_rate = district_rates.get(c.PoliceStationID, 10.0)
        c_freq = float(db.query(FIR).filter_by(PoliceStationID=c.PoliceStationID, crime_type=c.crime_type).filter(FIR.CrimeRegisteredDate >= '2026-05-08').count())
        w_rate = weekly_rates.get(c.PoliceStationID, 2.0)
        
        # Monthly trends and seasonality
        # Seasonality index (months 3-5 summer, 11-12 winter, else 1.0)
        month = reg_date.month
        s_score = 1.0
        if month in [3, 4, 5]:
            s_score = 1.3
        elif month in [11, 12]:
            s_score = 1.2
            
        # Monthly trend ratio (30 day count vs 12-month baseline avg)
        m_trend = 1.0 # default
        
        # Priority calculation
        # Priority Target formula
        has_women_children = 0.0
        vics = db.query(Victim).filter_by(fir_id=case_id).all()
        for v in vics:
            if v.gender == "Female" or (v.age and v.age < 18):
                has_women_children = 1.0
                break
                
        has_repeat = 0.0
        for aid in acc_ids:
            if aid in repeat_suspects:
                has_repeat = 1.0
                break
                
        has_weapons = 1.0 if c.crime_type in ["murder", "robbery", "assault"] else 0.0
        
        priority = float(gravity * 30.0 + has_women_children * 40.0 + has_repeat * 20.0 + has_weapons * 10.0)
        
        results[case_id] = {
            "victim_count": float(v_count),
            "accused_count": float(a_count),
            "act_count": float(act_count),
            "section_count": float(sec_count),
            "severity_score": severity,
            "gravity_score": gravity,
            "investigation_age": inv_age,
            "chargesheet_delay_target": cs_delay,
            "arrest_delay": arr_delay,
            "court_delay": c_delay,
            "hotspot_distance": h_dist,
            "district_crime_rate": d_rate,
            "crime_frequency": c_freq,
            "weekly_incident_rate": w_rate,
            "monthly_trend": m_trend,
            "seasonality_score": s_score,
            "priority_target": priority
        }
        
    return results
