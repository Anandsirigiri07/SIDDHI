# backend/features/verify_features.py
import os
import sys
import math

# Add root directory to path to allow importing backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database import SessionLocal
from backend.features.feature_service import build_all_features
from backend.features.feature_validators import detect_zscore_outliers
from backend.models import FeatureStore, FIR, Accused, Officer, HotspotCluster

BRAIN_DIR = r"C:\Users\trivi\.gemini\antigravity\brain\778851e5-df3d-4ba0-8ee3-d5fc7eb5eabe"

def run_verification():
    print("Initializing verification DB session...")
    db = SessionLocal()
    
    try:
        # 1. Run the full feature extraction pipeline
        print("Running full feature extraction pipeline...")
        stats = build_all_features(db, generated_by="verification-script")
        print(f"Pipeline executed successfully: {stats}")
        
        # 2. Query stats from feature store
        total_records = db.query(FeatureStore).count()
        print(f"Total features persisted: {total_records}")
        
        # Check coverage/completeness for each entity type
        entity_types = ["case", "suspect", "officer", "hotspot"]
        completeness = {}
        features_by_type = {}
        
        for etype in entity_types:
            # Fetch all distinct features for this entity type in the store
            feats = db.query(FeatureStore.feature_name).filter_by(entity_type=etype).distinct().all()
            feats = [f[0] for f in feats]
            
            # Fetch total entities of this type in core DB
            if etype == "case":
                total_entities = db.query(FIR).count()
            elif etype == "suspect":
                total_entities = db.query(Accused).count()
            elif etype == "officer":
                total_entities = db.query(Officer).count()
            elif etype == "hotspot":
                total_entities = db.query(HotspotCluster).count()
            else:
                total_entities = 0
                
            # Fetch count of unique entities in feature store
            store_entities = db.query(FeatureStore.entity_id).filter_by(entity_type=etype).distinct().count()
            
            coverage = (store_entities / total_entities * 100.0) if total_entities > 0 else 0.0
            completeness[etype] = {
                "total_entities": total_entities,
                "store_entities": store_entities,
                "coverage_pct": coverage,
                "feature_count": len(feats),
                "feature_names": feats
            }
            
            # Group values to check Z-score outliers
            features_by_type[etype] = {}
            store_rows = db.query(FeatureStore.entity_id, FeatureStore.feature_name, FeatureStore.feature_value).filter_by(entity_type=etype).all()
            for ent_id, fname, fval in store_rows:
                features_by_type[etype].setdefault(ent_id, {})[fname] = fval

        # 3. Detect Z-score outliers across all types
        all_outliers = []
        for etype in entity_types:
            outliers = detect_zscore_outliers(features_by_type[etype], threshold=3.0)
            all_outliers.extend([(etype, o) for o in outliers])
            
        # 4. Fetch lists of top suspects, overloaded officers, etc.
        # Top repeat offenders
        top_suspects = db.query(FeatureStore.entity_id, FeatureStore.feature_value)\
            .filter_by(entity_type="suspect", feature_name="prior_case_count")\
            .order_by(FeatureStore.feature_value.desc()).limit(5).all()
            
        suspect_details = []
        for sid, val in top_suspects:
            s_name = db.query(Accused.name).filter_by(accused_id=int(sid)).scalar() or "Unknown"
            suspect_details.append(f"- **{s_name}** (ID: {sid}): {int(val)} cases")

        # Top PageRank suspects
        top_pagerank = db.query(FeatureStore.entity_id, FeatureStore.feature_value)\
            .filter_by(entity_type="suspect", feature_name="pagerank_score")\
            .order_by(FeatureStore.feature_value.desc()).limit(5).all()
            
        pr_details = []
        for sid, val in top_pagerank:
            s_name = db.query(Accused.name).filter_by(accused_id=int(sid)).scalar() or "Unknown"
            pr_details.append(f"- **{s_name}** (ID: {sid}): PageRank = {val:.5f}")

        # Top overloaded officers
        top_officers = db.query(FeatureStore.entity_id, FeatureStore.feature_value)\
            .filter_by(entity_type="officer", feature_name="active_cases")\
            .order_by(FeatureStore.feature_value.desc()).limit(5).all()
            
        officer_details = []
        for oid, val in top_officers:
            o_name = db.query(Officer.name).filter_by(officer_id=int(oid)).scalar() or "Unknown"
            officer_details.append(f"- **{o_name}** (ID: {oid}): {int(val)} active cases")

        # Hotspot statistics
        hotspot_clusters = db.query(HotspotCluster).order_by(HotspotCluster.cluster_size.desc()).all()
        hotspot_details = []
        for h in hotspot_clusters:
            hotspot_details.append(
                f"- **Cluster {h.cluster_id}**: Centroid=({h.centroid_lat:.4f}, {h.centroid_lng:.4f}), "
                f"Size={h.cluster_size}, GrowthTarget={h.future_cluster_size}, Risk={h.cluster_risk:.2f}"
            )

        # 5. Write the markdown report to the brain folder
        report_path = os.path.join(BRAIN_DIR, "verification_report.md")
        
        md_content = f"""# FEATURE STORE VERIFICATION REPORT

This report evaluates the completeness, outlier density, and statistics of features persisted in the SIDDHI V2 Analytical layer.

---

## 1. Feature Coverage & Completeness Metrics

| Entity Type | Total Entities | Persisted in Store | Coverage % | Unique Features |
| :--- | :--- | :--- | :--- | :--- |
| **Case** | {completeness["case"]["total_entities"]} | {completeness["case"]["store_entities"]} | {completeness["case"]["coverage_pct"]:.2f}% | {completeness["case"]["feature_count"]} |
| **Suspect** | {completeness["suspect"]["total_entities"]} | {completeness["suspect"]["store_entities"]} | {completeness["suspect"]["coverage_pct"]:.2f}% | {completeness["suspect"]["feature_count"]} |
| **Officer** | {completeness["officer"]["total_entities"]} | {completeness["officer"]["store_entities"]} | {completeness["officer"]["coverage_pct"]:.2f}% | {completeness["officer"]["feature_count"]} |
| **Hotspot** | {completeness["hotspot"]["total_entities"]} | {completeness["hotspot"]["store_entities"]} | {completeness["hotspot"]["coverage_pct"]:.2f}% | {completeness["hotspot"]["feature_count"]} |

---

## 2. Statistical Highlights

### Top Suspects (Repeat Offenders)
{chr(10).join(suspect_details)}

### Top High-Value Suspect Nodes (PageRank)
{chr(10).join(pr_details)}

### Top Overloaded Officers
{chr(10).join(officer_details)}

### Hotspot Cluster Risk Profiles
{chr(10).join(hotspot_details)}

---

## 3. Z-Score Outlier Analysis ($\ge 3\sigma$)
* **Total anomalies detected:** {len(all_outliers)}
* **Outlier Details:**
"""
        if all_outliers:
            for etype, o in all_outliers[:20]:
                md_content += f"- **[{etype.upper()}]** {o}\n"
            if len(all_outliers) > 20:
                md_content += f"- *And {len(all_outliers) - 20} more outliers...*\n"
        else:
            md_content += "- No severe Z-score outliers detected in this run.\n"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"Verification report successfully written to: {report_path}")
        
    except Exception as e:
        print(f"Verification run failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
