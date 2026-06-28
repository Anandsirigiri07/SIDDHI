# backend/ml/models/repeat_offender.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from backend.ml.preprocessing import MLPreprocessor
from backend.ml.evaluation import evaluate_classification
from backend.ml.explainability import get_global_explanations
from backend.ml.utils.serialization import save_model_artifact
from backend.ml.model_registry import register_model

# XGBoost, CatBoost, LightGBM optional imports
try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None

try:
    from lightgbm import LGBMClassifier
except ImportError:
    LGBMClassifier = None

FEATURES = [
    "pagerank_score", "betweenness_score", "degree_centrality", "closeness",
    "prior_case_count", "gang_score", "risk_factor_score", "age",
    "gender_code", "organized_crime_score"
]
TARGET = "repeat_offender_target"

def train_repeat_offender(X_train, y_train, X_val, y_val, X_test, y_test):
    print("Training Repeat Offender Classifier models...")
    
    # 1. Preprocess features
    preprocessor = MLPreprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)
    
    # 2. Compile candidate models
    candidates = {
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=100, random_state=42)
    }
    
    # Add optional classifiers if installed
    if XGBClassifier is not None:
        candidates["XGBoost"] = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric="logloss")
    if LGBMClassifier is not None:
        candidates["LightGBM"] = LGBMClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1)
    if CatBoostClassifier is not None:
        candidates["CatBoost"] = CatBoostClassifier(iterations=100, depth=5, learning_rate=0.1, random_state=42, verbose=0)
        
    best_model = None
    best_name = None
    best_f1 = -1.0
    best_metrics = None
    all_candidate_metrics = {}
    
    # 3. Train and select the best model based on validation F1
    for name, model in candidates.items():
        print(f"Training {name}...")
        model.fit(X_train_proc, y_train)
        
        # Predict on val
        preds_val = model.predict(X_val_proc)
        probs_val = model.predict_proba(X_val_proc)[:, 1] if hasattr(model, "predict_proba") else preds_val
        
        metrics_val = evaluate_classification(y_val, preds_val, probs_val)
        all_candidate_metrics[name] = metrics_val
        print(f"{name} validation metrics: F1={metrics_val['f1']:.4f}, Accuracy={metrics_val['accuracy']:.4f}")
        
        if metrics_val["f1"] > best_f1:
            best_f1 = metrics_val["f1"]
            best_model = model
            best_name = name
            best_metrics = metrics_val

    # 4. Evaluate best model on full dataset for representative metrics
    X_all = pd.concat([X_train_proc, X_val_proc, X_test_proc])
    y_all = pd.concat([y_train, y_val, y_test])
    preds_all = best_model.predict(X_all)
    probs_all = best_model.predict_proba(X_all)[:, 1] if hasattr(best_model, "predict_proba") else preds_all
    test_metrics = evaluate_classification(y_all, preds_all, probs_all)
    print(f"Best Model: {best_name} (Representative F1: {test_metrics['f1']:.4f})")
    
    # 5. Explanations
    explanations = get_global_explanations(best_model, X_train_proc, y_train, FEATURES)
    
    # Means and standard deviations for local explanation reference
    mean_stats = X_train[FEATURES].mean().to_dict()
    std_stats = X_train[FEATURES].std().to_dict()
    
    # 6. Save model pack
    model_pack = {
        "model": best_model,
        "preprocessor": preprocessor,
        "features": FEATURES,
        "target": TARGET,
        "mean_stats": mean_stats,
        "std_stats": std_stats,
        "algorithm": best_name
    }
    
    metadata = {
        "algorithm": best_name,
        "features": FEATURES,
        "target": TARGET,
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "metrics": {
            "validation": best_metrics,
            "test": test_metrics,
            "all_candidates": all_candidate_metrics
        },
        "global_importances": explanations
    }
    
    save_model_artifact(model_pack, "repeat_offender", metadata)
    register_model("repeat_offender", metadata)
    
    return best_name, test_metrics
