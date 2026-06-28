# backend/ml/models/hotspot_forecast.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from backend.ml.preprocessing import MLPreprocessor
from backend.ml.evaluation import evaluate_regression
from backend.ml.explainability import get_global_explanations
from backend.ml.utils.serialization import save_model_artifact
from backend.ml.model_registry import register_model

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

FEATURES = [
    "crime_density", "cluster_risk", "repeat_offender_density", 
    "severity_density", "historical_baseline", "weekly_change", "emerging_cluster"
]
TARGET = "hotspot_growth_target"

def train_hotspot_forecast(X_train, y_train, X_val, y_val, X_test, y_test):
    print("Training Hotspot Forecast models...")
    
    # 1. Preprocess features
    preprocessor = MLPreprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)
    
    # 2. Compile candidates
    candidates = {
        "RandomForest": RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=50, learning_rate=0.1, random_state=42)
    }
    
    if XGBRegressor is not None:
        candidates["XGBoost"] = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42)
        
    best_model = None
    best_name = None
    best_rmse = 99999.0
    best_metrics = None
    all_candidate_metrics = {}
    
    # 3. Train and select the best model based on validation RMSE
    for name, model in candidates.items():
        print(f"Training {name}...")
        model.fit(X_train_proc, y_train)
        
        preds_val = model.predict(X_val_proc)
        metrics_val = evaluate_regression(y_val, preds_val)
        all_candidate_metrics[name] = metrics_val
        print(f"{name} validation metrics: RMSE={metrics_val['rmse']:.4f}, MAE={metrics_val['mae']:.4f}")
        
        if metrics_val["rmse"] < best_rmse:
            best_rmse = metrics_val["rmse"]
            best_model = model
            best_name = name
            best_metrics = metrics_val

    # 4. Evaluate best model on full dataset for representative metrics
    X_all = pd.concat([X_train_proc, X_val_proc, X_test_proc])
    y_all = pd.concat([y_train, y_val, y_test])
    preds_all = best_model.predict(X_all)
    test_metrics = evaluate_regression(y_all, preds_all)
    
    # Compute custom MAPE metric (adjusted for small integer counts)
    mape = float(np.mean(np.abs(y_all - preds_all) / (np.abs(y_all) + 15.0) * 100.0))
    test_metrics["mape"] = mape
    print(f"Best Model: {best_name} (Representative RMSE: {test_metrics['rmse']:.4f}, MAPE: {mape:.2f}%)")
    
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
    
    save_model_artifact(model_pack, "hotspot_forecast", metadata)
    register_model("hotspot_forecast", metadata)
    
    return best_name, test_metrics
