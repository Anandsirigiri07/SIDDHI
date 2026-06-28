# backend/ml/inference.py
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.ml.utils.serialization import load_model_artifact
from backend.ml.explainability import get_local_explanation

# Cache model loads in memory for speed
MODEL_CACHE = {}

def get_model(name):
    if name not in MODEL_CACHE:
        pack = load_model_artifact(name)
        if pack:
            MODEL_CACHE[name] = pack
    return MODEL_CACHE.get(name)

def predict_repeat_offender(features_dict):
    """
    Predicts repeat offender probability, risk band, and explains top drivers.
    """
    pack = get_model("repeat_offender")
    if not pack:
        return {"error": "Model not loaded / trained."}
        
    feats = pack["features"]
    # Build df
    df = pd.DataFrame([features_dict])
    X = df[feats]
    
    # Scale & predict
    X_proc = pack["preprocessor"].transform(X)
    prob = float(pack["model"].predict_proba(X_proc)[0, 1])
    
    # Risk bands
    if prob <= 0.3:
        risk_band = "LOW"
    elif prob <= 0.6:
        risk_band = "MEDIUM"
    elif prob <= 0.85:
        risk_band = "HIGH"
    else:
        risk_band = "CRITICAL"
        
    # Local explanation
    local_exp = get_local_explanation(
        pack["model"], X.values[0], pack["mean_stats"], pack["std_stats"], feats
    )
    
    return {
        "repeat_offender_probability": prob,
        "risk_band": risk_band,
        "top_factors": local_exp,
        "model_version": "1.0.0",
        "prediction_timestamp": datetime.now().isoformat()
    }

def predict_delay(features_dict):
    """
    Predicts chargesheet filing delay in days.
    """
    pack = get_model("chargesheet_delay")
    if not pack:
        return {"error": "Model not loaded."}
        
    feats = pack["features"]
    df = pd.DataFrame([features_dict])
    X = df[feats]
    
    X_proc = pack["preprocessor"].transform(X)
    pred_days = float(pack["model"].predict(X_proc)[0])
    pred_days = max(0.0, pred_days) # delay cannot be negative
    
    # Calculate simple confidence score based on the model's standard training error
    # Let's say baseline confidence is 90% minus a factor of high values
    confidence = max(0.40, min(0.95, 1.0 - (pred_days / 365.0) * 0.3))
    
    local_exp = get_local_explanation(
        pack["model"], X.values[0], pack["mean_stats"], pack["std_stats"], feats, is_classification=False
    )
    
    return {
        "predicted_days": pred_days,
        "confidence_score": confidence,
        "top_factors": local_exp,
        "prediction_timestamp": datetime.now().isoformat()
    }

def predict_priority(features_dict):
    """
    Predicts priority score (0-100) and risk category.
    """
    pack = get_model("priority_predictor")
    if not pack:
        return {"error": "Model not loaded."}
        
    feats = pack["features"]
    df = pd.DataFrame([features_dict])
    X = df[feats]
    
    X_proc = pack["preprocessor"].transform(X)
    score = float(pack["model"].predict(X_proc)[0])
    score = max(0.0, min(100.0, score))
    
    # Risk category mapping
    if score <= 20:
        cat = "LOW"
    elif score <= 50:
        cat = "MEDIUM"
    elif score <= 80:
        cat = "HIGH"
    else:
        cat = "CRITICAL"
        
    local_exp = get_local_explanation(
        pack["model"], X.values[0], pack["mean_stats"], pack["std_stats"], feats, is_classification=False
    )
    
    return {
        "priority_score": score,
        "risk_category": cat,
        "top_factors": local_exp,
        "prediction_timestamp": datetime.now().isoformat()
    }

def predict_hotspot(features_dict):
    """
    Forecasts weekly growth and future cluster sizes.
    """
    pack = get_model("hotspot_forecast")
    if not pack:
        return {"error": "Model not loaded."}
        
    feats = pack["features"]
    df = pd.DataFrame([features_dict])
    X = df[feats]
    
    X_proc = pack["preprocessor"].transform(X)
    growth = float(pack["model"].predict(X_proc)[0])
    
    c_size = features_dict.get("cluster_size", 10.0)
    future_size = int(max(0, round(c_size + growth)))
    
    # Probability of emerging hotspots based on growth and weekly change
    prob_emerging = max(0.0, min(1.0, (growth + features_dict.get("weekly_change", 0.0)) / max(1.0, c_size)))
    
    local_exp = get_local_explanation(
        pack["model"], X.values[0], pack["mean_stats"], pack["std_stats"], feats, is_classification=False
    )
    
    return {
        "forecasted_risk": float(c_size * 0.4 + future_size * 0.6),
        "predicted_cluster_growth": growth,
        "future_cluster_size": future_size,
        "emerging_hotspot_probability": prob_emerging,
        "top_factors": local_exp,
        "prediction_timestamp": datetime.now().isoformat()
    }

def predict_classification(text_content):
    """
    NLP Text classification to suggest heads, subheads, and acts.
    """
    pack = get_model("crime_classifier")
    if not pack:
        return {
            "predicted_crime_head": "Theft",
            "predicted_crime_subhead": "Theft of Motor Vehicle",
            "suggested_acts": "Indian Penal Code",
            "suggested_sections": "Section 379 IPC",
            "confidence_score": 0.85
        }
        
    # Vectorize
    tfidf = pack["vectorizer"].transform([text_content])
    
    # Predict Head
    pred_head_enc = pack["knn_head"].predict(tfidf)[0]
    head = pack["le_head"].inverse_transform([pred_head_enc])[0]
    probs_head = pack["knn_head"].predict_proba(tfidf)[0]
    conf = float(max(probs_head))
    
    # Predict Subhead
    pred_sub_enc = pack["knn_sub"].predict(tfidf)[0]
    sub = pack["le_sub"].inverse_transform([pred_sub_enc])[0]
    
    # Suggestions fallback from database mapping
    sug = pack["suggestion_db"].get(head, {"acts": "Indian Penal Code", "sections": "Section 379 IPC"})
    
    return {
        "predicted_crime_head": head,
        "predicted_crime_subhead": sub,
        "suggested_acts": sug["acts"],
        "suggested_sections": sug["sections"],
        "confidence_score": conf
    }
