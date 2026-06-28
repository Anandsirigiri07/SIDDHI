# backend/ml/dataset_builder.py
import os
import sys
import pandas as pd
from datetime import datetime

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database import SessionLocal
from backend.models import FeatureStore, FIR, Accused, HotspotCluster
from sqlalchemy import text

DATASETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "datasets"))
os.makedirs(DATASETS_DIR, exist_ok=True)

def get_split(date_str):
    if not date_str:
        return "train"
    try:
        year = int(date_str.split("-")[0])
        if year <= 2024:
            return "train"
        elif year == 2025:
            return "val"
        else:
            return "test"
    except Exception:
        return "train"

def build_datasets():
    print("Building pivoted machine learning datasets...")
    db = SessionLocal()
    
    try:
        # Load all features from the feature store
        features = db.query(FeatureStore).all()
        if not features:
            print("Feature store is empty. Please run verify_features.py first.")
            return False
            
        df_store = pd.DataFrame([{
            "entity_type": f.entity_type,
            "entity_id": f.entity_id,
            "feature_name": f.feature_name,
            "feature_value": f.feature_value
        } for f in features])
        
        # 1. Pivot each entity type
        entity_dfs = {}
        for etype in df_store["entity_type"].unique():
            df_sub = df_store[df_store["entity_type"] == etype]
            df_pivot = df_sub.pivot(index="entity_id", columns="feature_name", values="feature_value").reset_index()
            entity_dfs[etype] = df_pivot
            
        print(f"Pivoted entity sets: {list(entity_dfs.keys())}")
        
        # --- A. REPEAT OFFENDER DATASET (Suspects) ---
        df_suspect = entity_dfs.get("suspect")
        if df_suspect is not None:
            # Join with accused details (age, occupation) and find split year
            accused_rows = db.execute(text("SELECT accused_id, age, gender FROM accused")).fetchall()
            df_acc = pd.DataFrame(accused_rows, columns=["entity_id", "age", "gender"])
            df_acc["entity_id"] = df_acc["entity_id"].astype(str)
            df_suspect = df_suspect.merge(df_acc, on="entity_id", how="left")
            
            # Find earliest case date for each suspect to determine split
            sus_dates = db.execute(text("""
                SELECT fa.accused_id, MIN(f.date) as min_date 
                FROM fir_accused fa
                JOIN firs f ON fa.fir_id = f.fir_id
                GROUP BY fa.accused_id
            """)).fetchall()
            df_sus_dates = pd.DataFrame(sus_dates, columns=["entity_id", "min_date"])
            df_sus_dates["entity_id"] = df_sus_dates["entity_id"].astype(str)
            df_suspect = df_suspect.merge(df_sus_dates, on="entity_id", how="left")
            
            df_suspect["split"] = df_suspect["min_date"].apply(get_split)
            # Impute missing demographic fields
            df_suspect["age"] = df_suspect["age"].fillna(32.0)
            df_suspect["gender"] = df_suspect["gender"].fillna("Male")
            # Map categorical variables
            df_suspect["gender_code"] = df_suspect["gender"].map({"Male": 0, "Female": 1, "Transgender": 2}).fillna(0)
            
            repeat_path = os.path.join(DATASETS_DIR, "repeat_offender.csv")
            df_suspect.to_csv(repeat_path, index=False)
            print(f"Saved Repeat Offender dataset to {repeat_path} (Shape: {df_suspect.shape})")

        # --- B. CHARGESHEET DELAY DATASET (Cases) ---
        df_case = entity_dfs.get("case")
        if df_case is not None:
            # Join with FIR date to find split and officer link
            fir_dates = db.execute(text("SELECT fir_id, date, crime_type, officer_id FROM firs")).fetchall()
            df_f_dates = pd.DataFrame(fir_dates, columns=["entity_id", "date", "crime_type", "officer_id"])
            df_f_dates["entity_id"] = df_f_dates["entity_id"].astype(str)
            df_f_dates["officer_id"] = df_f_dates["officer_id"].astype(str)
            df_case = df_case.merge(df_f_dates, on="entity_id", how="left")
            
            # Merge with pivoted officer features to get officer_load
            df_officer = entity_dfs.get("officer")
            if df_officer is not None:
                df_off_sub = df_officer[["entity_id", "officer_load"]].copy()
                df_off_sub.columns = ["officer_id", "officer_load"]
                df_off_sub["officer_id"] = df_off_sub["officer_id"].astype(str)
                df_case = df_case.merge(df_off_sub, on="officer_id", how="left")
            
            df_case["officer_load"] = df_case["officer_load"].fillna(5.0)
            df_case["split"] = df_case["date"].apply(get_split)
            
            # --- Dynamic Enrichment of Priority features ---
            print("Enriching case features with victim and suspect details...")
            # 1. Fetch victims details per case
            victims = db.execute(text("SELECT fir_id, age, gender FROM victims")).fetchall()
            victim_groups = {}
            for fid, age, gender in victims:
                victim_groups.setdefault(str(fid), []).append({"age": age, "gender": gender})
                
            # 2. Fetch accused details per case
            case_accused = db.execute(text("SELECT fir_id, accused_id FROM fir_accused")).fetchall()
            case_accused_groups = {}
            for fid, aid in case_accused:
                case_accused_groups.setdefault(str(fid), []).append(str(aid))
                
            # Pre-calculate suspect mapping dictionary from df_suspect for fast lookup
            suspect_mapping = {}
            if df_suspect is not None:
                for _, row in df_suspect.iterrows():
                    suspect_mapping[str(row["entity_id"])] = {
                        "prior_case_count": row.get("prior_case_count", 0.0),
                        "gang_score": row.get("gang_score", 0.0),
                        "organized_crime_score": row.get("organized_crime_score", 0.0)
                    }
            
            # Compute lists
            women_involved_list = []
            children_involved_list = []
            repeat_offender_presence_list = []
            gang_score_list = []
            organized_crime_score_list = []
            victim_vuln_list = []
            weapon_usage_list = []
            community_risk_list = []
            
            for _, row in df_case.iterrows():
                fid = str(row["entity_id"])
                crime_type = str(row.get("crime_type", ""))
                
                # Victims check
                v_list = victim_groups.get(fid, [])
                w_inv = 1.0 if (crime_type == "women_crime" or any(v["gender"] == "Female" for v in v_list)) else 0.0
                c_inv = 1.0 if any(v["age"] < 18 for v in v_list) else 0.0
                
                women_involved_list.append(w_inv)
                children_involved_list.append(c_inv)
                victim_vuln_list.append(w_inv * 0.5 + c_inv * 0.5)
                
                # Accused check
                a_list = case_accused_groups.get(fid, [])
                has_repeat = 0.0
                max_gang = 0.0
                max_org = 0.0
                for aid in a_list:
                    sus_data = suspect_mapping.get(aid, {})
                    if sus_data.get("prior_case_count", 0.0) >= 1.0:
                        has_repeat = 1.0
                    max_gang = max(max_gang, sus_data.get("gang_score", 0.0))
                    max_org = max(max_org, sus_data.get("organized_crime_score", 0.0))
                    
                repeat_offender_presence_list.append(has_repeat)
                gang_score_list.append(max_gang)
                organized_crime_score_list.append(max_org)
                
                # Weapon usage
                weap = 1.0 if crime_type in ["robbery", "assault", "murder"] else 0.0
                weapon_usage_list.append(weap)
                
                # Community risk (combination of gang and repeat offender features)
                community_risk_list.append(max_gang * 50.0 + has_repeat * 20.0)
                
            # Assign features to df_case
            df_case["women_involved"] = women_involved_list
            df_case["children_involved"] = children_involved_list
            df_case["repeat_offender_presence"] = repeat_offender_presence_list
            df_case["gang_score"] = gang_score_list
            df_case["organized_crime_score"] = organized_crime_score_list
            df_case["victim_vulnerability"] = victim_vuln_list
            df_case["weapon_usage"] = weapon_usage_list
            df_case["community_risk"] = community_risk_list
            
            # Save delay prediction subset (filter cases with chargesheets, i.e., delay >= 0)
            # Wait, chargesheet_delay_target is -1.0 if not chargesheeted.
            df_delay = df_case[df_case["chargesheet_delay_target"] >= 0.0].copy()
            delay_path = os.path.join(DATASETS_DIR, "delay_prediction.csv")
            df_delay.to_csv(delay_path, index=False)
            print(f"Saved Delay Prediction dataset to {delay_path} (Shape: {df_delay.shape})")
            
            # --- C. PRIORITY PREDICTION DATASET (Cases) ---
            priority_path = os.path.join(DATASETS_DIR, "priority_prediction.csv")
            df_case.to_csv(priority_path, index=False)
            print(f"Saved Priority Prediction dataset to {priority_path} (Shape: {df_case.shape})")

        # --- D. HOTSPOT FORECAST DATASET (Hotspots) ---
        df_hotspot = entity_dfs.get("hotspot")
        if df_hotspot is not None:
            # Since hotspots are aggregations, we can assign 70% train, 15% val, 15% test temporally or by index
            # Let's assign based on cluster ID split:
            # ID 0-6 -> train, 7-8 -> val, 9 -> test
            df_hotspot["split"] = "train"
            df_hotspot.loc[df_hotspot["entity_id"].astype(int).isin([7, 8]), "split"] = "val"
            df_hotspot.loc[df_hotspot["entity_id"].astype(int) == 9, "split"] = "test"
            
            hotspot_path = os.path.join(DATASETS_DIR, "hotspot_prediction.csv")
            df_hotspot.to_csv(hotspot_path, index=False)
            print(f"Saved Hotspot Prediction dataset to {hotspot_path} (Shape: {df_hotspot.shape})")

        # --- E. CRIME CLASSIFICATION DATASET (BriefFacts) ---
        fir_text_rows = db.execute(text("SELECT fir_id, date, crime_type, BriefFacts FROM firs")).fetchall()
        df_text = pd.DataFrame(fir_text_rows, columns=["entity_id", "date", "crime_head", "BriefFacts"])
        df_text["entity_id"] = df_text["entity_id"].astype(str)
        df_text["split"] = df_text["date"].apply(get_split)
        
        # Subhead maps
        subhead_rows = db.execute(text("""
            SELECT f.fir_id, s.SectionDescription 
            FROM firs f
            JOIN ActSectionAssociation asa ON f.fir_id = asa.CaseMasterID
            JOIN Section s ON asa.SectionID = s.SectionCode AND asa.ActID = s.ActCode
            GROUP BY f.fir_id
        """)).fetchall()
        df_sub = pd.DataFrame(subhead_rows, columns=["entity_id", "crime_subhead"])
        df_sub["entity_id"] = df_sub["entity_id"].astype(str)
        df_text = df_text.merge(df_sub, on="entity_id", how="left")
        df_text["crime_subhead"] = df_text["crime_subhead"].fillna("General IPC Section")
        
        # Acts & sections suggestion list
        act_sec_rows = db.execute(text("""
            SELECT asa.CaseMasterID, a.ActDescription, s.SectionCode 
            FROM ActSectionAssociation asa
            JOIN Act a ON asa.ActID = a.ActCode
            JOIN Section s ON asa.SectionID = s.SectionCode AND asa.ActID = s.ActCode
        """)).fetchall()
        
        act_mapping = {}
        for cid, act_desc, sec_name in act_sec_rows:
            sid = str(cid)
            act_mapping.setdefault(sid, {"acts": set(), "sections": set()})
            if act_desc: act_mapping[sid]["acts"].add(act_desc)
            if sec_name: act_mapping[sid]["sections"].add(sec_name)
            
        df_text["suggested_acts"] = df_text["entity_id"].apply(lambda x: ";".join(act_mapping.get(x, {}).get("acts", ["Indian Penal Code"])))
        df_text["suggested_sections"] = df_text["entity_id"].apply(lambda x: ";".join(act_mapping.get(x, {}).get("sections", ["Section 379 IPC"])))
        
        class_path = os.path.join(DATASETS_DIR, "crime_classification.csv")
        df_text.to_csv(class_path, index=False)
        print(f"Saved Crime Classification dataset to {class_path} (Shape: {df_text.shape})")
        
        return True
    except Exception as e:
        print(f"Failed to build datasets: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    build_datasets()
