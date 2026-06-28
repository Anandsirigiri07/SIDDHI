# backend/features/compute_officer_features.py
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models import Officer, FIR

def compute_officer_features_all(db: Session) -> dict:
    """
    Computes all officer-level features.
    """
    officers = db.query(Officer).all()
    results = {}
    
    now = datetime.date(2026, 6, 7) # anchor date
    
    # 1. Fetch active cases (Open / Under Investigation)
    active_cnts = {}
    active_rows = db.execute(text("""
        SELECT officer_id, COUNT(fir_id) FROM firs 
        WHERE status IN ('Open', 'Under Investigation') 
        GROUP BY officer_id
    """)).fetchall()
    for oid, cnt in active_rows:
        active_cnts[oid] = int(cnt)
        
    # 2. Fetch closed cases (Chargesheet Filed / Closed)
    closed_cnts = {}
    closed_rows = db.execute(text("""
        SELECT officer_id, COUNT(fir_id) FROM firs 
        WHERE status IN ('Chargesheet Filed', 'Closed') 
        GROUP BY officer_id
    """)).fetchall()
    for oid, cnt in closed_rows:
        closed_cnts[oid] = int(cnt)

    # 3. Calculate average chargesheet delay per officer
    cs_delays = {}
    cs_rows = db.execute(text("""
        SELECT f.officer_id, AVG(JULIANDAY(c.csdate) - JULIANDAY(f.CrimeRegisteredDate)) 
        FROM firs f 
        JOIN ChargesheetDetails c ON f.fir_id = c.CaseMasterID 
        GROUP BY f.officer_id
    """)).fetchall()
    for oid, avg_d in cs_rows:
        if avg_d:
            cs_delays[oid] = float(avg_d)
            
    # 4. Calculate average investigation duration (closed duration)
    inv_durations = {}
    inv_rows = db.execute(text("""
        SELECT f.officer_id, AVG(JULIANDAY(c.csdate) - JULIANDAY(f.CrimeRegisteredDate)) 
        FROM firs f 
        JOIN ChargesheetDetails c ON f.fir_id = c.CaseMasterID 
        WHERE f.status = 'Closed' OR f.status = 'Chargesheet Filed'
        GROUP BY f.officer_id
    """)).fetchall()
    for oid, avg_d in inv_rows:
        if avg_d:
            inv_durations[oid] = float(avg_d)
            
    # 5. Fetch backlog cases (>90 days old and active)
    backlog_cnts = {}
    backlog_rows = db.execute(text("""
        SELECT officer_id, COUNT(fir_id) FROM firs 
        WHERE status IN ('Open', 'Under Investigation') 
        AND (JULIANDAY('2026-06-07') - JULIANDAY(CrimeRegisteredDate)) > 90
        GROUP BY officer_id
    """)).fetchall()
    for oid, cnt in backlog_rows:
        backlog_cnts[oid] = int(cnt)

    # 6. Fetch risk active cases (Heinous active cases)
    risk_active_cnts = {}
    risk_rows = db.execute(text("""
        SELECT officer_id, COUNT(fir_id) FROM firs 
        WHERE status IN ('Open', 'Under Investigation') 
        AND crime_type IN ('murder', 'robbery', 'women_crime')
        GROUP BY officer_id
    """)).fetchall()
    for oid, cnt in risk_rows:
        risk_active_cnts[oid] = int(cnt)

    # Calculate global average active cases to determine officer load ratio
    active_vals = list(active_cnts.values())
    global_avg_active = sum(active_vals) / len(active_vals) if active_vals else 1.0

    for o in officers:
        oid = o.officer_id
        
        act = float(active_cnts.get(oid, 0.0))
        cls = float(closed_cnts.get(oid, 0.0))
        
        tot = act + cls
        crate = cls / tot if tot > 0 else 0.0
        
        cs_del = float(cs_delays.get(oid, -1.0))
        inv_dur = float(inv_durations.get(oid, -1.0))
        
        load = act / global_avg_active if global_avg_active > 0 else 1.0
        backlog = float(backlog_cnts.get(oid, 0.0))
        
        risk_active = float(risk_active_cnts.get(oid, 0.0))
        risk_ratio = risk_active / act if act > 0 else 0.0
        
        results[oid] = {
            "active_cases": act,
            "closed_cases": cls,
            "average_chargesheet_delay": cs_del,
            "average_investigation_duration": inv_dur,
            "officer_load": load,
            "clearance_rate": crate,
            "case_backlog": backlog,
            "risk_case_ratio": risk_ratio
        }
        
    return results
