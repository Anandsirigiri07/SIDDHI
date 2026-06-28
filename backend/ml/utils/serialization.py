# backend/ml/utils/serialization.py
import os
import joblib
import json
from datetime import datetime

ARTIFACTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../artifacts"))
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def save_model_artifact(model, name, metadata):
    """Saves model pkl and metadata json."""
    model_path = os.path.join(ARTIFACTS_DIR, f"{name}.pkl")
    meta_path = os.path.join(ARTIFACTS_DIR, f"{name}_metadata.json")
    
    joblib.dump(model, model_path)
    
    metadata_full = {
        **metadata,
        "saved_at": datetime.now().isoformat(),
        "model_file": f"{name}.pkl"
    }
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_full, f, indent=4)
        
    print(f"Model saved successfully: {model_path}")
    return model_path

def load_model_artifact(name):
    """Loads model from artifacts directory."""
    model_path = os.path.join(ARTIFACTS_DIR, f"{name}.pkl")
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)
