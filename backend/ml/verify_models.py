# backend/ml/verify_models.py
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.ml.inference import (
    predict_repeat_offender, predict_delay, predict_priority,
    predict_hotspot, predict_classification
)

DATASETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "datasets"))
ARTIFACTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts"))

def run_verification():
    print("=========================================")
    print("RUNNING SIDDHI V2 ML MODELS VERIFICATION")
    print("=========================================")
    errors = []
    
    # 1. Check Datasets
    print("\n1. Verifying dataset CSV files...")
    required_datasets = [
        "repeat_offender.csv", "delay_prediction.csv",
        "priority_prediction.csv", "hotspot_prediction.csv",
        "crime_classification.csv"
    ]
    for dname in required_datasets:
        path = os.path.join(DATASETS_DIR, dname)
        if os.path.exists(path):
            print(f"  [OK] Dataset exists: {dname} (Size: {os.path.getsize(path)} bytes)")
        else:
            print(f"  [ERROR] Dataset missing: {dname}")
            errors.append(f"Missing dataset: {dname}")
            
    # 2. Check Model Artifacts
    print("\n2. Verifying serialized model PKL files...")
    required_models = [
        "repeat_offender.pkl", "chargesheet_delay.pkl",
        "priority_predictor.pkl", "hotspot_forecast.pkl",
        "crime_classifier.pkl"
    ]
    for mname in required_models:
        path = os.path.join(ARTIFACTS_DIR, mname)
        if os.path.exists(path):
            print(f"  [OK] Model artifact exists: {mname}")
        else:
            print(f"  [ERROR] Model artifact missing: {mname}")
            errors.append(f"Missing model artifact: {mname}")
            
    # 3. Test Inference Functions
    print("\n3. Testing inference outputs with sample payloads...")
    
    # Repeat Offender test
    try:
        sample_suspect = {
            "pagerank_score": 0.05, "betweenness_score": 0.02, "degree_centrality": 0.1, "closeness": 0.3,
            "prior_case_count": 4.0, "gang_score": 0.8, "risk_factor_score": 12.0, "age": 28.0,
            "gender_code": 0.0, "organized_crime_score": 0.75
        }
        res = predict_repeat_offender(sample_suspect)
        assert "repeat_offender_probability" in res
        assert "risk_band" in res
        assert "top_factors" in res
        print(f"  [OK] Repeat Offender Inference: Prob={res['repeat_offender_probability']:.4f}, Band={res['risk_band']}")
    except Exception as e:
        print(f"  [ERROR] Repeat Offender Inference failed: {e}")
        errors.append(f"Repeat Offender Inference error: {e}")
        
    # Chargesheet Delay test
    try:
        sample_case_delay = {
            "victim_count": 2.0, "accused_count": 3.0, "officer_load": 4.0, "gravity_score": 1.0,
            "district_crime_rate": 250.0, "investigation_age": 45.0, "court_delay": 120.0,
            "act_count": 2.0, "section_count": 4.0
        }
        res = predict_delay(sample_case_delay)
        assert "predicted_days" in res
        assert "confidence_score" in res
        print(f"  [OK] Chargesheet Delay Inference: Predicted Days={res['predicted_days']:.1f}, Conf={res['confidence_score']:.2f}")
    except Exception as e:
        print(f"  [ERROR] Chargesheet Delay Inference failed: {e}")
        errors.append(f"Chargesheet Delay Inference error: {e}")
        
    # Priority test
    try:
        sample_case_priority = {
            "gravity_score": 1.0, "women_involved": 1.0, "children_involved": 0.0,
            "repeat_offender_presence": 1.0, "gang_score": 0.8, "victim_vulnerability": 0.5,
            "weapon_usage": 1.0, "community_risk": 45.0, "organized_crime_score": 0.75
        }
        res = predict_priority(sample_case_priority)
        assert "priority_score" in res
        assert "risk_category" in res
        print(f"  [OK] Priority Inference: Score={res['priority_score']:.1f}, Category={res['risk_category']}")
    except Exception as e:
        print(f"  [ERROR] Priority Inference failed: {e}")
        errors.append(f"Priority Inference error: {e}")
        
    # Hotspot test
    try:
        sample_hotspot = {
            "crime_density": 45.2, "cluster_risk": 150.0, "repeat_offender_density": 0.45,
            "severity_density": 6.5, "historical_baseline": 3.2, "weekly_change": 1.5,
            "emerging_cluster": 1.0, "cluster_size": 250.0
        }
        res = predict_hotspot(sample_hotspot)
        assert "predicted_cluster_growth" in res
        assert "future_cluster_size" in res
        print(f"  [OK] Hotspot Forecast Inference: Growth={res['predicted_cluster_growth']:.2f}, Future Size={res['future_cluster_size']}")
    except Exception as e:
        print(f"  [ERROR] Hotspot Forecast Inference failed: {e}")
        errors.append(f"Hotspot Forecast Inference error: {e}")
        
    # Classification test
    try:
        sample_text = "Accused forced entry into the house at night and stole gold jewelry and cash while owners were away."
        res = predict_classification(sample_text)
        assert "predicted_crime_head" in res
        assert "predicted_crime_subhead" in res
        assert "suggested_acts" in res
        assert "suggested_sections" in res
        print(f"  [OK] Crime Head Classification Inference: Head={res['predicted_crime_head']}, Subhead={res['predicted_crime_subhead']}")
    except Exception as e:
        print(f"  [ERROR] Crime Classification Inference failed: {e}")
        errors.append(f"Crime Classification Inference error: {e}")
        
    print("\n=========================================")
    if not errors:
        print("VERIFICATION COMPLETED SUCCESSFULLY [PASS]")
        print("=========================================")
        return True
    else:
        print(f"VERIFICATION FAILED [FAIL] with {len(errors)} errors:")
        for err in errors:
            print(f" - {err}")
        print("=========================================")
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
