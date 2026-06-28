# backend/ml/feature_selector.py
import pandas as pd
import numpy as np
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.ensemble import RandomForestClassifier

def perform_feature_selection(X, y, is_classification=True):
    """
    Computes multiple feature importance metrics and returns a sorted rank.
    """
    results = {}
    
    # 1. Correlation with target
    corrs = []
    for col in X.columns:
        corr_val = pd.Series(y).corr(X[col])
        corrs.append(0.0 if np.isnan(corr_val) else corr_val)
    results["correlation"] = corrs
    
    # 2. Mutual Information
    if is_classification:
        mi = mutual_info_classif(X, y, random_state=42)
    else:
        mi = mutual_info_regression(X, y, random_state=42)
    results["mutual_info"] = list(mi)
    
    # 3. Random Forest Feature Importance
    rf = RandomForestClassifier(n_estimators=50, random_state=42) if is_classification else RandomForestClassifier(n_estimators=50, random_state=42) # Regressor fallback
    if not is_classification:
        from sklearn.ensemble import RandomForestRegressor
        rf = RandomForestRegressor(n_estimators=50, random_state=42)
        
    rf.fit(X, y)
    results["tree_importance"] = list(rf.feature_importances_)
    
    # Compile dataframe
    df_rank = pd.DataFrame(results, index=X.columns)
    df_rank["mean_rank"] = df_rank.mean(axis=1)
    df_rank = df_rank.sort_values(by="mean_rank", ascending=False)
    
    return df_rank
