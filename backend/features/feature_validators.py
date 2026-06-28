# backend/features/feature_validators.py
import math
from typing import Dict, List, Any, Tuple
from backend.features.feature_registry import FEATURE_REGISTRY

def validate_feature_bounds(entity_type: str, features_dict: Dict[str, Dict[str, float]]) -> Tuple[int, int, List[str]]:
    """
    Validates features against registered bounds.
    Returns: (passed_count, failed_count, warnings_list)
    """
    passed = 0
    failed = 0
    warnings = []
    
    for ent_id, feats in features_dict.items():
        for fname, fval in feats.items():
            reg = FEATURE_REGISTRY.get(fname)
            if not reg:
                warnings.append(f"Unregistered feature '{fname}' for entity '{ent_id}'")
                continue
                
            if fval is None or math.isnan(fval):
                failed += 1
                warnings.append(f"Null/NaN value in feature '{fname}' for entity '{ent_id}'")
                continue
                
            if not (reg.lower_bound <= fval <= reg.upper_bound):
                failed += 1
                warnings.append(f"Value {fval} out of bounds [{reg.lower_bound}, {reg.upper_bound}] for feature '{fname}' (entity '{ent_id}')")
            else:
                passed += 1
                
    return passed, failed, warnings

def detect_zscore_outliers(features_dict: Dict[str, Dict[str, float]], threshold: float = 3.0) -> List[str]:
    """
    Detects outliers using simple rolling mean & std deviation (Z-score anomaly).
    Returns list of outlier descriptions.
    """
    outliers = []
    # Transpose dict to group by feature name: { fname: [values] }
    values_by_feature = {}
    for ent_id, feats in features_dict.items():
        for fname, fval in feats.items():
            if fval is not None and not math.isnan(fval):
                values_by_feature.setdefault(fname, []).append((ent_id, fval))
                
    for fname, val_list in values_by_feature.items():
        if len(val_list) < 10:
            continue # skip small groups
            
        vals = [v for _, v in val_list]
        mean = sum(vals) / len(vals)
        variance = sum((x - mean) ** 2 for x in vals) / len(vals)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            continue
            
        for ent_id, val in val_list:
            z_score = abs(val - mean) / std_dev
            if z_score > threshold:
                outliers.append(f"Outlier detected for '{fname}' in entity '{ent_id}': value={val:.4f} (mean={mean:.4f}, std={std_dev:.4f}, z={z_score:.2f})")
                
    return outliers
