# backend/ml/model_registry.py
import os
import json
from datetime import datetime

REGISTRY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts/model_registry.json"))

def get_registry():
    if not os.path.exists(REGISTRY_PATH):
        os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump({"models": {}, "last_updated": datetime.now().isoformat()}, f, indent=4)
            
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"models": {}, "last_updated": datetime.now().isoformat()}

def register_model(task_name, metadata):
    registry = get_registry()
    
    registry["models"][task_name] = {
        **metadata,
        "registered_at": datetime.now().isoformat()
    }
    registry["last_updated"] = datetime.now().isoformat()
    
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)
        
    print(f"Model successfully registered for task '{task_name}'")
    return registry
