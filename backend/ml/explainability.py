# backend/ml/explainability.py
import pandas as pd
import numpy as np
from sklearn.inspection import permutation_importance

def get_global_explanations(model, X_train, y_train, features):
    """
    Computes global feature importances using model's native attribute
    and permutation importance.
    """
    importances = {}
    
    # 1. Native importance
    if hasattr(model, "feature_importances_"):
        importances["native"] = list(model.feature_importances_)
    else:
        importances["native"] = [0.0] * len(features)
        
    # 2. Permutation importance (limited to 50 samples for speed)
    try:
        sample_size = min(len(X_train), 50)
        perm = permutation_importance(model, X_train.iloc[:sample_size], y_train.iloc[:sample_size], n_repeats=3, random_state=42)
        importances["permutation"] = list(perm.importances_mean)
    except Exception:
        importances["permutation"] = importances["native"]
        
    df_imp = pd.DataFrame(importances, index=features)
    df_imp["composite"] = df_imp.mean(axis=1)
    df_imp = df_imp.sort_values(by="composite", ascending=False)
    
    return df_imp.to_dict(orient="index")

def get_local_explanation(model, X_row, X_mean, X_std, features, is_classification=True):
    """
    Generates a SHAP-like local prediction explanation.
    It estimates feature contributions by calculating the directional distance
    of the row features from the mean, scaled by standard deviation and global feature importance.
    """
    # Load global importances
    if hasattr(model, "feature_importances_"):
        global_imp = model.feature_importances_
    else:
        global_imp = np.array([1.0 / len(features)] * len(features))
        
    contributions = []
    
    for i, col in enumerate(features):
        val = X_row[col].values[0] if isinstance(X_row, pd.DataFrame) else X_row[i]
        mean_val = X_mean[col]
        std_val = X_std[col] if X_std[col] > 0 else 1.0
        
        # Calculate deviation (z-score like)
        z = (val - mean_val) / std_val
        
        # Contribution score
        contrib = z * global_imp[i]
        
        contributions.append({
            "feature": col,
            "value": float(val),
            "deviation": float(z),
            "contribution": float(contrib)
        })
        
    # Sort contributions by magnitude
    contributions = sorted(contributions, key=lambda x: abs(x["contribution"]), reverse=True)
    return contributions[:5] # Top 5 factors
