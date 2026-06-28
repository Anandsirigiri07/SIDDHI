# backend/features/feature_store_writer.py
import datetime
from sqlalchemy.orm import Session
from backend.models import FeatureStore
from backend.features.feature_registry import FEATURE_REGISTRY

PIPELINE_VERSION = "v2.0.0"

def write_features_batch(db: Session, entity_type: str, features_dict: dict, generated_by: str = "pipeline-run"):
    """
    Persists a batch of features for multiple entities in the feature store.
    features_dict format: { entity_id: { feature_name: feature_value } }
    """
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d") # daily snapshot key
    
    # We will use upsert logic or clear existing for (entity_type, entity_id, feature_name, timestamp)
    for ent_id, feats in features_dict.items():
        for fname, fval in feats.items():
            # Lookup in registry
            reg = FEATURE_REGISTRY.get(fname)
            if not reg:
                continue # ignore unregistered features
                
            fver = reg.feature_version
            istarget = reg.is_target
            
            # Clamp value to bounds
            clamped_val = max(reg.lower_bound, min(reg.upper_bound, float(fval)))
            
            # SQLite upsert equivalent: delete existing first in this session
            db.query(FeatureStore).filter_by(
                entity_type=entity_type,
                entity_id=str(ent_id),
                feature_name=fname,
                timestamp=timestamp_str
            ).delete(synchronize_session=False)
            
            feat_record = FeatureStore(
                entity_type=entity_type,
                entity_id=str(ent_id),
                feature_name=fname,
                feature_value=clamped_val,
                timestamp=timestamp_str,
                pipeline_version=PIPELINE_VERSION,
                feature_version=fver,
                generated_at=now_str,
                generated_by=generated_by,
                is_target=istarget
            )
            db.add(feat_record)
            
    db.commit()
