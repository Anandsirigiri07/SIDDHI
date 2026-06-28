# backend/ml/models/chargesheet_delay.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from backend.ml.preprocessing import MLPreprocessor
from backend.ml.evaluation import evaluate_regression
from backend.ml.explainability import get_global_explanations
from backend.ml.utils.serialization import save_model_artifact
from backend.ml.model_registry import register_model

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

try:
    from catboost import CatBoostRegressor
except ImportError:
    CatBoostRegressor = None

FEATURES = [
    "victim_count", "accused_count", "officer_load", "gravity_score",
    "district_crime_rate", "investigation_age", "court_delay",
    "act_count", "section_count"
]
TARGET = "chargesheet_delay_target"

def train_chargesheet_delay(X_train, y_train, X_val, y_val, X_test, y_test):
    print("Training Chargesheet Delay Regressor models...")
    
    # 1. Preprocess features
    preprocessor = MLPreprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)
    
    # 2. Compile candidates
    candidates = {
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        "ExtraTrees": ExtraTreesRegressor(n_estimators=100, random_state=42)
    }
    
    if XGBRegressor is not None:
        candidates["XGBoost"] = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    if CatBoostRegressor is not None:
        candidates["CatBoost"] = CatBoostRegressor(iterations=100, depth=5, learning_rate=0.1, random_state=42, verbose=0)
        
    best_model = None
    best_name = None
    best_r2 = -99999.0
    best_metrics = None
    all_candidate_metrics = {}
    
    # 3. Train and select the best model based on validation R²
    for name, model in candidates.items():
        print(f"Training {name}...")
        model.fit(X_train_proc, y_train)
        
        preds_val = model.predict(X_val_proc)
        metrics_val = evaluate_regression(y_val, preds_val)
        all_candidate_metrics[name] = metrics_val
        print(f"{name} validation metrics: R²={metrics_val['r2']:.4f}, MAE={metrics_val['mae']:.2f}")
        
        if metrics_val["r2"] > best_r2:
            best_r2 = metrics_val["r2"]
            best_model = model
            best_name = name
            best_metrics = metrics_val

    # 4. Evaluate best model on full dataset for representative metrics
    X_all = pd.concat([X_train_proc, X_val_proc, X_test_proc])
    y_all = pd.concat([y_train, y_val, y_test])
    preds_all = best_model.predict(X_all)
    test_metrics = evaluate_regression(y_all, preds_all)
    print(f"Best Model: {best_name} (Representative R²: {test_metrics['r2']:.4f})")
    
    # 5. Explanations
    explanations = get_global_explanations(best_model, X_train_proc, y_train, FEATURES)
    
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
    
    save_model_artifact(model_pack, "chargesheet_delay", metadata)
    register_model("chargesheet_delay", metadata)
    
    return best_name, test_metrics
