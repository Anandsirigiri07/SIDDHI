# backend/features/verify_intelligence.py
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database import SessionLocal
from backend.features.intelligence_service import (
    build_suspect_intelligence_json, build_case_priority_json,
    build_district_intelligence_json, build_executive_briefing_json
)

def run_verification():
    print("=========================================")
    print("RUNNING SIDDHI V2 INTELLIGENCE LAYER VERIFICATION")
    print("=========================================")
    errors = []
    db = SessionLocal()
    
    try:
        # Get a valid suspect ID from the database
        sus_id = db.execute(text("SELECT accused_id FROM accused LIMIT 1")).scalar()
        case_id = db.execute(text("SELECT fir_id FROM firs LIMIT 1")).scalar()
        
        if not sus_id or not case_id:
            print("  [ERROR] Database has no suspect or case entries to test.")
            errors.append("No database records found.")
            return False
            
        print(f"\n1. Verifying Suspect Dossier JSON (ID: {sus_id})...")
        sus_json = build_suspect_intelligence_json(str(sus_id), db)
        assert "suspect_id" in sus_json
        assert "name" in sus_json
        assert "network_metrics" in sus_json
        assert "pagerank_score" in sus_json["network_metrics"]
        assert "predictions" in sus_json
        assert "repeat_offender_probability" in sus_json["predictions"]
        assert "risk_band" in sus_json["predictions"]
        assert "recommendations" in sus_json
        assert "confidence_score" in sus_json
        print(f"  [OK] Suspect JSON generated. Recidivism Prob: {sus_json['predictions']['repeat_offender_probability']:.4f}, Confidence: {sus_json['confidence_score']:.1f}%")
        
        print(f"\n2. Verifying Case Priority Dossier JSON (ID: {case_id})...")
        case_json = build_case_priority_json(str(case_id), db)
        assert "case_id" in case_json
        assert "fir_number" in case_json
        assert "priority_assessment" in case_json
        assert "priority_score" in case_json["priority_assessment"]
        assert "chargesheet_delay_forecast" in case_json
        assert "predicted_days" in case_json["chargesheet_delay_forecast"]
        assert "confidence_interval_95" in case_json["chargesheet_delay_forecast"]
        assert "recommendations" in case_json
        print(f"  [OK] Case Priority JSON generated. Priority Score: {case_json['priority_assessment']['priority_score']:.1f}/100, Delay Forecast: {case_json['chargesheet_delay_forecast']['predicted_days']:.1f} days")
        
        print("\n3. Verifying District Intelligence (Bengaluru East)...")
        dist_json = build_district_intelligence_json("Bengaluru East", db)
        assert "district_name" in dist_json
        assert "total_cases" in dist_json
        assert "district_ranking" in dist_json
        assert "hotspot_movement_analysis" in dist_json
        assert "centroid_shift_degree" in dist_json["hotspot_movement_analysis"]
        assert "active_hotspots" in dist_json
        print(f"  [OK] District JSON generated. Cases: {dist_json['total_cases']}, Centroid Shift: {dist_json['hotspot_movement_analysis']['centroid_shift_degree']:.6f} degrees")
        
        print("\n4. Verifying Executive Briefing City-Wide Payload...")
        exec_json = build_executive_briefing_json(db)
        assert "city_wide_summary" in exec_json
        assert "top_repeat_offenders" in exec_json
        assert len(exec_json["top_repeat_offenders"]) > 0
        assert "district_rankings" in exec_json
        print(f"  [OK] Executive JSON generated. Total Cases: {exec_json['city_wide_summary']['total_cases']}, Top Suspect: {exec_json['top_repeat_offenders'][0]['name']}")
        
    except Exception as e:
        print(f"  [ERROR] Verification execution crashed: {e}")
        errors.append(f"Crashed with: {e}")
    finally:
        db.close()
        
    print("\n=========================================")
    if not errors:
        print("INTELLIGENCE VERIFICATION SUCCESSFULLY [PASS]")
        print("=========================================")
        return True
    else:
        print("INTELLIGENCE VERIFICATION FAILED [FAIL]")
        for err in errors:
            print(f" - {err}")
        print("=========================================")
        return False

if __name__ == "__main__":
    from sqlalchemy import text
    success = run_verification()
    sys.exit(0 if success else 1)
