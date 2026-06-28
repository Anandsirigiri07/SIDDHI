# backend/ml/pipeline.py
import os
import sys
import json
import time

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.ml.dataset_builder import build_datasets
from backend.ml.data_loader import load_task_dataset
from backend.ml.models.repeat_offender import train_repeat_offender, FEATURES as REP_FEATS
from backend.ml.models.chargesheet_delay import train_chargesheet_delay, FEATURES as DELAY_FEATS
from backend.ml.models.priority_predictor import train_priority_predictor, FEATURES as PRIORITY_FEATS
from backend.ml.models.hotspot_forecast import train_hotspot_forecast, FEATURES as HOTSPOT_FEATS
from backend.ml.models.crime_classifier import train_crime_classifier

BRAIN_DIR = r"C:\Users\trivi\.gemini\antigravity\brain\778851e5-df3d-4ba0-8ee3-d5fc7eb5eabe"

def run_training_pipeline():
    print("=========================================")
    print("STARTING SIDDHI V2 ML TRAINING PIPELINE")
    print("=========================================")
    start_time = time.time()
    
    # Step 1: Rebuild datasets from feature store
    build_success = build_datasets()
    if not build_success:
        print("Dataset building failed. Aborting pipeline.")
        return False
        
    registry_summary = {}
    
    # Step 2: Train Repeat Offender Model
    print("\n--- Training Task 1: Repeat Offender ---")
    X_tr, y_tr, X_val, y_val, X_te, y_te = load_task_dataset("repeat_offender", REP_FEATS, "repeat_offender_target")
    rep_alg, rep_metrics = train_repeat_offender(X_tr, y_tr, X_val, y_val, X_te, y_te)
    registry_summary["repeat_offender"] = {"algorithm": rep_alg, "test_metrics": rep_metrics}
    
    # Step 3: Train Chargesheet Delay Model
    print("\n--- Training Task 2: Chargesheet Delay ---")
    X_tr, y_tr, X_val, y_val, X_te, y_te = load_task_dataset("delay_prediction", DELAY_FEATS, "chargesheet_delay_target")
    delay_alg, delay_metrics = train_chargesheet_delay(X_tr, y_tr, X_val, y_val, X_te, y_te)
    registry_summary["chargesheet_delay"] = {"algorithm": delay_alg, "test_metrics": delay_metrics}
    
    # Step 4: Train Priority Prediction Model
    print("\n--- Training Task 3: Case Priority ---")
    X_tr, y_tr, X_val, y_val, X_te, y_te = load_task_dataset("priority_prediction", PRIORITY_FEATS, "priority_target")
    pri_alg, pri_metrics = train_priority_predictor(X_tr, y_tr, X_val, y_val, X_te, y_te)
    registry_summary["priority_predictor"] = {"algorithm": pri_alg, "test_metrics": pri_metrics}
    
    # Step 5: Train Hotspot Forecasting Model
    print("\n--- Training Task 4: Hotspot Forecast ---")
    X_tr, y_tr, X_val, y_val, X_te, y_te = load_task_dataset("hotspot_prediction", HOTSPOT_FEATS, "hotspot_growth_target")
    hot_alg, hot_metrics = train_hotspot_forecast(X_tr, y_tr, X_val, y_val, X_te, y_te)
    registry_summary["hotspot_forecast"] = {"algorithm": hot_alg, "test_metrics": hot_metrics}
    
    # Step 6: Train Crime Classification Model
    print("\n--- Training Task 5: Crime Classifier (NLP) ---")
    import pandas as pd
    class_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "datasets/crime_classification.csv"))
    train_df = class_df[class_df["split"] == "train"]
    val_df = class_df[class_df["split"] == "val"]
    test_df = class_df[class_df["split"] == "test"]
    
    class_alg, class_metrics = train_crime_classifier(
        train_df["BriefFacts"], train_df["crime_head"], train_df["crime_subhead"],
        val_df["BriefFacts"], val_df["crime_head"], val_df["crime_subhead"],
        test_df["BriefFacts"], test_df["crime_head"], test_df["crime_subhead"],
        test_df
    )
    registry_summary["crime_classifier"] = {"algorithm": class_alg, "test_metrics": class_metrics}
    
    # Save a metrics_dashboard.json in the artifacts directory
    dash_path = os.path.join(os.path.dirname(__file__), "artifacts/metrics_dashboard.json")
    with open(dash_path, "w", encoding="utf-8") as f:
        json.dump(registry_summary, f, indent=4)
        
    print("\n=========================================")
    print(f"PIPELINE COMPLETED IN {time.time() - start_time:.2f} SECONDS")
    print("=========================================")
    
    # Step 7: Write Markdown Reports
    write_reports(registry_summary)
    return True

def write_reports(summary):
    # Retrieve detail metrics from registry metadata
    reg_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    
    def get_meta(name):
        p = os.path.join(reg_dir, f"{name}_metadata.json")
        if os.path.exists(p):
            with open(p, "r") as f: return json.load(f)
        return {}
        
    meta_rep = get_meta("repeat_offender")
    meta_delay = get_meta("chargesheet_delay")
    meta_pri = get_meta("priority_predictor")
    meta_hot = get_meta("hotspot_forecast")
    meta_class = get_meta("crime_classifier")
    
    # 1. MODEL_REPORT.md
    report_md = f"""# MODEL REPORT — PREDICTIVE CRIME INTELLIGENCE LAYER

This document contains detailed evaluation reports, test metrics, and baseline checks for the active predictive models in SIDDHI V2.

---

## 1. Repeat Offender Classification
* **Algorithm:** {meta_rep.get("algorithm", "N/A")}
* **Dataset Size:** Train={meta_rep.get("train_size", 0)}, Val={meta_rep.get("val_size", 0)}, Test={meta_rep.get("test_size", 0)}
* **Test Performance:**
  - Accuracy: {meta_rep.get("metrics", {}).get("test", {}).get("accuracy", 0.0):.4f}
  - Precision: {meta_rep.get("metrics", {}).get("test", {}).get("precision", 0.0):.4f}
  - Recall: {meta_rep.get("metrics", {}).get("test", {}).get("recall", 0.0):.4f}
  - **F1 Score:** {meta_rep.get("metrics", {}).get("test", {}).get("f1", 0.0):.4f} (Target: >0.80)
  - ROC-AUC: {meta_rep.get("metrics", {}).get("test", {}).get("roc_auc", 0.0):.4f}

---

## 2. Chargesheet Delay Regression
* **Algorithm:** {meta_delay.get("algorithm", "N/A")}
* **Dataset Size:** Train={meta_delay.get("train_size", 0)}, Val={meta_delay.get("val_size", 0)}, Test={meta_delay.get("test_size", 0)}
* **Test Performance:**
  - MAE: {meta_delay.get("metrics", {}).get("test", {}).get("mae", 0.0):.2f} days
  - RMSE: {meta_delay.get("metrics", {}).get("test", {}).get("rmse", 0.0):.2f} days
  - **R² Score:** {meta_delay.get("metrics", {}).get("test", {}).get("r2", 0.0):.4f} (Target: >0.75)

---

## 3. Priority Prediction
* **Algorithm:** {meta_pri.get("algorithm", "N/A")}
* **Dataset Size:** Train={meta_pri.get("train_size", 0)}, Val={meta_pri.get("val_size", 0)}, Test={meta_pri.get("test_size", 0)}
* **Test Performance:**
  - **MAE:** {meta_pri.get("metrics", {}).get("test", {}).get("mae", 0.0):.4f} score points (Target: <10.0)
  - RMSE: {meta_pri.get("metrics", {}).get("test", {}).get("rmse", 0.0):.4f}

---

## 4. Hotspot Forecasting
* **Algorithm:** {meta_hot.get("algorithm", "N/A")}
* **Dataset Size:** Train={meta_hot.get("train_size", 0)}, Val={meta_hot.get("val_size", 0)}, Test={meta_hot.get("test_size", 0)}
* **Test Performance:**
  - MAE: {meta_hot.get("metrics", {}).get("test", {}).get("mae", 0.0):.2f}
  - RMSE: {meta_hot.get("metrics", {}).get("test", {}).get("rmse", 0.0):.2f}
  - **MAPE:** {meta_hot.get("metrics", {}).get("test", {}).get("mape", 0.0):.2f}% (Target: <15.0%)

---

## 5. Crime Head & Subhead Classification
* **Algorithm:** {meta_class.get("algorithm", "N/A")}
* **Dataset Size:** Train={meta_class.get("train_size", 0)}, Val={meta_class.get("val_size", 0)}, Test={meta_class.get("test_size", 0)}
* **Test Performance:**
  - **Top-1 Accuracy:** {meta_class.get("metrics", {}).get("test", {}).get("top_1_accuracy", 0.0)*100.0:.2f}%
  - **Top-3 Accuracy:** {meta_class.get("metrics", {}).get("test", {}).get("top_3_accuracy", 0.0)*100.0:.2f}% (Target: >85.0%)
"""
    with open(os.path.join(BRAIN_DIR, "MODEL_REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report_md)
        
    # 2. MODEL_SUMMARY.md
    summary_md = f"""# MODEL SUMMARY — PERFORMANCE METRIC CHECKLIST

| Model Task | Best Algorithm | Primary Evaluation Metric | Target Threshold | Achieved Metric | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Repeat Offender** | {meta_rep.get("algorithm", "N/A")} | F1-Score | > 0.80 | {meta_rep.get("metrics", {}).get("test", {}).get("f1", 0.0):.4f} | {'✅ PASS' if meta_rep.get("metrics", {}).get("test", {}).get("f1", 0.0) >= 0.80 else '⚠️ WARN'} |
| **Chargesheet Delay** | {meta_delay.get("algorithm", "N/A")} | R² Score | > 0.75 | {meta_delay.get("metrics", {}).get("test", {}).get("r2", 0.0):.4f} | {'✅ PASS' if meta_delay.get("metrics", {}).get("test", {}).get("r2", 0.0) >= 0.75 else '⚠️ WARN'} |
| **Priority Predictor** | {meta_pri.get("algorithm", "N/A")} | Mean Absolute Error | < 10.0 | {meta_pri.get("metrics", {}).get("test", {}).get("mae", 0.0):.4f} | {'✅ PASS' if meta_pri.get("metrics", {}).get("test", {}).get("mae", 0.0) <= 10.0 else '⚠️ WARN'} |
| **Hotspot Forecast** | {meta_hot.get("algorithm", "N/A")} | MAPE | < 15.0% | {meta_hot.get("metrics", {}).get("test", {}).get("mape", 0.0):.2f}% | {'✅ PASS' if meta_hot.get("metrics", {}).get("test", {}).get("mape", 0.0) <= 15.0 else '⚠️ WARN'} |
| **Crime Head Classifier** | {meta_class.get("algorithm", "N/A")} | Top-3 Accuracy | > 85.0% | {meta_class.get("metrics", {}).get("test", {}).get("top_3_accuracy", 0.0)*100.0:.2f}% | {'✅ PASS' if meta_class.get("metrics", {}).get("test", {}).get("top_3_accuracy", 0.0) >= 0.85 else '⚠️ WARN'} |
"""
    with open(os.path.join(BRAIN_DIR, "MODEL_SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write(summary_md)

    # 3. MODEL_COMPARISON.md
    comp_md = """# MODEL COMPARISON — ALGORITHM BENCHMARKING

Detailed performance scores across candidates:

### A. Repeat Offender Candidates
| Model Algorithm | Accuracy | Precision | Recall | F1 Score |
| :--- | :--- | :--- | :--- | :--- |
"""
    for name, m in meta_rep.get("metrics", {}).get("all_candidates", {}).items():
        comp_md += f"| {name:<15} | {m['accuracy']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} |\n"
        
    comp_md += "\n### B. Chargesheet Delay Candidates\n| Model Algorithm | MAE (days) | RMSE (days) | R² Score |\n| :--- | :--- | :--- | :--- |\n"
    for name, m in meta_delay.get("metrics", {}).get("all_candidates", {}).items():
        comp_md += f"| {name:<15} | {m['mae']:.2f} | {m['rmse']:.2f} | {m['r2']:.4f} |\n"

    comp_md += "\n### C. Priority Predictor Candidates\n| Model Algorithm | MAE | RMSE | R² |\n| :--- | :--- | :--- | :--- |\n"
    for name, m in meta_pri.get("metrics", {}).get("all_candidates", {}).items():
        comp_md += f"| {name:<15} | {m['mae']:.4f} | {m['rmse']:.4f} | {m['r2']:.4f} |\n"
        
    with open(os.path.join(BRAIN_DIR, "MODEL_COMPARISON.md"), "w", encoding="utf-8") as f:
        f.write(comp_md)

    # 4. FEATURE_IMPORTANCE.md
    feat_md = """# FEATURE IMPORTANCE — ATTRIBUTION AND EXPLAINABILITY

Key contributing features across each model:

### A. Repeat Offender Predictor
| Feature Name | Tree Importance | Permutation Importance |
| :--- | :--- | :--- |
"""
    for fname, details in meta_rep.get("global_importances", {}).items():
        feat_md += f"| {fname:<25} | {details.get('native', 0.0):.4f} | {details.get('permutation', 0.0):.4f} |\n"

    feat_md += "\n### B. Chargesheet Delay Predictor\n| Feature Name | Tree Importance | Permutation Importance |\n| :--- | :--- | :--- |\n"
    for fname, details in meta_delay.get("global_importances", {}).items():
        feat_md += f"| {fname:<25} | {details.get('native', 0.0):.4f} | {details.get('permutation', 0.0):.4f} |\n"

    feat_md += "\n### C. Priority Predictor\n| Feature Name | Tree Importance | Permutation Importance |\n| :--- | :--- | :--- |\n"
    for fname, details in meta_pri.get("global_importances", {}).items():
        feat_md += f"| {fname:<25} | {details.get('native', 0.0):.4f} | {details.get('permutation', 0.0):.4f} |\n"

    with open(os.path.join(BRAIN_DIR, "FEATURE_IMPORTANCE.md"), "w", encoding="utf-8") as f:
        f.write(feat_md)
        
    print("All Phase 4 markdown reports successfully written to the brain directory.")

if __name__ == "__main__":
    run_training_pipeline()
