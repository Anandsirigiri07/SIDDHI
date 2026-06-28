# backend/ml/evaluation.py
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.calibration import calibration_curve

def evaluate_classification(y_true, y_pred, y_prob=None):
    """Computes standard classification evaluation metrics."""
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0))
    }
    
    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except Exception:
            metrics["roc_auc"] = 0.5
            
        # Calibration curve
        try:
            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=5)
            metrics["calibration"] = {
                "true_probs": [float(x) for x in prob_true],
                "pred_probs": [float(x) for x in prob_pred]
            }
        except Exception:
            metrics["calibration"] = None
            
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics["confusion_matrix"] = cm.tolist()
    
    return metrics

def evaluate_regression(y_true, y_pred):
    """Computes standard regression evaluation metrics."""
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    residuals = (y_true - y_pred).tolist()
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "residuals": residuals[:200] # limit to 200 items for json size
    }
