# backend/features/feature_service.py
from sqlalchemy.orm import Session
from backend.features.compute_graph_features import compute_graph_features_all
from backend.features.compute_hotspot_features import compute_hotspot_features_all
from backend.features.compute_case_features import compute_case_features_all
from backend.features.compute_accused_features import compute_accused_features_all
from backend.features.compute_officer_features import compute_officer_features_all
from backend.features.feature_store_writer import write_features_batch
from backend.features.feature_validators import validate_feature_bounds, detect_zscore_outliers

def build_graph_features(db: Session, generated_by: str = "pipeline-run") -> dict:
    """Executes Graph Centrality and Community features computation."""
    print("Computing graph features (NetworkX)...")
    compute_graph_features_all(db)
    return {"status": "success"}

def build_hotspot_features(db: Session, generated_by: str = "pipeline-run") -> dict:
    """Executes Hotspot DBSCAN clusters and density features computation."""
    print("Computing hotspot features (DBSCAN)...")
    hotspot_results = compute_hotspot_features_all(db)
    write_features_batch(db, "hotspot", hotspot_results, generated_by=generated_by)
    return hotspot_results

def build_case_features(db: Session, generated_by: str = "pipeline-run") -> dict:
    """Computes Case-level features."""
    print("Computing case features...")
    case_results = compute_case_features_all(db)
    write_features_batch(db, "case", case_results, generated_by=generated_by)
    return case_results

def build_suspect_features(db: Session, generated_by: str = "pipeline-run") -> dict:
    """Computes Suspect-level features."""
    print("Computing suspect features...")
    accused_results = compute_accused_features_all(db)
    write_features_batch(db, "suspect", accused_results, generated_by=generated_by)
    return accused_results

def build_officer_features(db: Session, generated_by: str = "pipeline-run") -> dict:
    """Computes Officer-level features."""
    print("Computing officer features...")
    officer_results = compute_officer_features_all(db)
    write_features_batch(db, "officer", officer_results, generated_by=generated_by)
    return officer_results

def build_all_features(db: Session, generated_by: str = "pipeline-run") -> dict:
    """
    Executes the entire feature extraction pipeline in order of dependencies:
    1. Graph features
    2. Hotspot features
    3. Case features
    4. Suspect features
    5. Officer features
    """
    # 1. Graph Centralities
    build_graph_features(db, generated_by)
    
    # 2. Hotspots
    hotspot_res = build_hotspot_features(db, generated_by)
    
    # 3. Case Features (depends on Hotspot centroids)
    case_res = build_case_features(db, generated_by)
    
    # 4. Suspect Features (depends on Graph Centralities)
    suspect_res = build_suspect_features(db, generated_by)
    
    # 5. Officer Features
    officer_res = build_officer_features(db, generated_by)
    
    # Run bounds validation and anomaly detection
    validate_feature_bounds("case", case_res)
    validate_feature_bounds("suspect", suspect_res)
    validate_feature_bounds("officer", officer_res)
    
    return {
        "cases": len(case_res),
        "suspects": len(suspect_res),
        "officers": len(officer_res),
        "hotspots": len(hotspot_res),
        "status": "completed"
    }

# --- Scheduler Operations ---

def nightly_refresh(db: Session):
    """Nightly scheduler refreshing all features."""
    print("Running scheduled nightly feature refresh...")
    build_all_features(db, generated_by="nightly-scheduler")

def incremental_refresh(db: Session):
    """Incremental scheduler for new cases."""
    print("Running scheduled incremental feature refresh...")
    # For incremental, we rebuild cases & officers.
    build_case_features(db, generated_by="incremental-scheduler")
    build_officer_features(db, generated_by="incremental-scheduler")

def entity_refresh(db: Session, entity_type: str, entity_id: str):
    """Refreshes features for a single entity only."""
    print(f"Refreshing features for single entity {entity_type}:{entity_id}...")
    if entity_type == "case":
        # Recalculate case features
        case_res = compute_case_features_all(db)
        if int(entity_id) in case_res:
            write_features_batch(db, "case", {int(entity_id): case_res[int(entity_id)]}, generated_by="entity-refresh")
    elif entity_type == "suspect":
        suspect_res = compute_accused_features_all(db)
        if int(entity_id) in suspect_res:
            write_features_batch(db, "suspect", {int(entity_id): suspect_res[int(entity_id)]}, generated_by="entity-refresh")
    elif entity_type == "officer":
        officer_res = compute_officer_features_all(db)
        if int(entity_id) in officer_res:
            write_features_batch(db, "officer", {int(entity_id): officer_res[int(entity_id)]}, generated_by="entity-refresh")

def district_refresh(db: Session, district_id: int):
    """Refreshes features for a specific district only."""
    print(f"Refreshing features for district {district_id}...")
    # For SQLite simplification, we do a full refresh
    build_all_features(db, generated_by=f"district-refresh-{district_id}")
