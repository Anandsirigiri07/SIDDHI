# backend/storage/sqlite_adapter.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any, Dict, List, Optional
import json

from backend.storage.repository import (
    CaseMasterRepository,
    FeatureStoreRepository,
    PredictionsRepository,
    HotspotsRepository,
    CommunitiesRepository,
    RiskScoresRepository,
    DossiersRepository,
    ModelRegistryRepository
)

class SQLiteCaseMasterRepository(CaseMasterRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT fir_number, date, crime_type, description, officer_id FROM firs WHERE fir_id = :id"),
            {"id": int(case_id)}
        ).fetchone()
        if row:
            return {
                "fir_number": row[0],
                "date": row[1],
                "crime_type": row[2],
                "description": row[3],
                "officer_id": row[4]
            }
        return None

class SQLiteFeatureStoreRepository(FeatureStoreRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_features(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        row = self.db.execute(
            text("SELECT feature_data FROM feature_store WHERE entity_type = :type AND entity_id = :id"),
            {"type": entity_type, "id": entity_id}
        ).fetchone()
        if row:
            return json.loads(row[0])
        return {}

class SQLitePredictionsRepository(PredictionsRepository):
    def __init__(self, db: Session):
        self.db = db

    def save_prediction(self, model_name: str, entity_id: str, prediction: Dict[str, Any]) -> None:
        # Save or log prediction history for model auditing
        pass

class SQLiteHotspotsRepository(HotspotsRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_active_hotspots(self) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            text("SELECT hotspot_id, centroid_lat, centroid_lon, cluster_size, emerging FROM hotspots")
        ).fetchall()
        return [
            {
                "id": r[0],
                "lat": r[1],
                "lon": r[2],
                "size": r[3],
                "emerging": bool(r[4])
            }
            for r in rows
        ]

class SQLiteCommunitiesRepository(CommunitiesRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_community_members(self, community_id: int) -> List[str]:
        rows = self.db.execute(
            text("SELECT name FROM accused WHERE community_id = :cid"),
            {"cid": community_id}
        ).fetchall()
        return [r[0] for r in rows]

class SQLiteRiskScoresRepository(RiskScoresRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_suspect_risk(self, suspect_id: str) -> Optional[float]:
        # Return PageRank score from accused or features table
        val = self.db.execute(
            text("SELECT pagerank FROM accused WHERE accused_id = :id"),
            {"id": int(suspect_id)}
        ).scalar()
        return float(val) if val else None

class SQLiteDossiersRepository(DossiersRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_dossier_text(self, entity_type: str, entity_id: str) -> Optional[str]:
        # Local cached dossiers
        return None

class SQLiteModelRegistryRepository(ModelRegistryRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_model_metadata(self, model_name: str) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("SELECT metadata FROM model_registry WHERE model_name = :name"),
            {"name": model_name}
        ).fetchone()
        if row:
            return json.loads(row[0])
        return None
