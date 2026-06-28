# backend/storage/datastore_adapter.py
from typing import Any, Dict, List, Optional
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
from backend.storage.sqlite_adapter import (
    SQLiteCaseMasterRepository,
    SQLiteFeatureStoreRepository,
    SQLitePredictionsRepository,
    SQLiteHotspotsRepository,
    SQLiteCommunitiesRepository,
    SQLiteRiskScoresRepository,
    SQLiteDossiersRepository,
    SQLiteModelRegistryRepository
)
from backend.config.catalyst_config import USE_LOCAL_FALLBACK

class CatalystDataStoreAdapter(
    CaseMasterRepository,
    FeatureStoreRepository,
    PredictionsRepository,
    HotspotsRepository,
    CommunitiesRepository,
    RiskScoresRepository,
    DossiersRepository,
    ModelRegistryRepository
):
    def __init__(self, db_session):
        self.db_session = db_session
        self.sqlite_fallback = SQLiteCaseMasterRepository(db_session)
        self.sqlite_feats = SQLiteFeatureStoreRepository(db_session)
        self.sqlite_hot = SQLiteHotspotsRepository(db_session)
        self.sqlite_comm = SQLiteCommunitiesRepository(db_session)
        self.sqlite_risk = SQLiteRiskScoresRepository(db_session)
        self.sqlite_dossier = SQLiteDossiersRepository(db_session)
        self.sqlite_model = SQLiteModelRegistryRepository(db_session)

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        # Mock Catalyst Relational Data Store API query:
        # datastore = catalyst.datastore()
        # table = datastore.table('CaseMaster')
        # row = table.get_row_by_id(case_id)
        if USE_LOCAL_FALLBACK:
            return self.sqlite_fallback.get_case(case_id)
        return {"fir_number": f"CAT-FIR-{case_id}", "crime_type": "assault"}

    def get_features(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        if USE_LOCAL_FALLBACK:
            return self.sqlite_feats.get_features(entity_type, entity_id)
        return {}

    def save_prediction(self, model_name: str, entity_id: str, prediction: Dict[str, Any]) -> None:
        # Mock insert prediction history into Catalyst Datastore table 'Predictions'
        # table.insert_row({'model_name': model_name, 'entity_id': entity_id, 'prediction_val': str(prediction)})
        pass

    def get_active_hotspots(self) -> List[Dict[str, Any]]:
        if USE_LOCAL_FALLBACK:
            return self.sqlite_hot.get_active_hotspots()
        return []

    def get_community_members(self, community_id: int) -> List[str]:
        if USE_LOCAL_FALLBACK:
            return self.sqlite_comm.get_community_members(community_id)
        return []

    def get_suspect_risk(self, suspect_id: str) -> Optional[float]:
        if USE_LOCAL_FALLBACK:
            return self.sqlite_risk.get_suspect_risk(suspect_id)
        return 0.5

    def get_dossier_text(self, entity_type: str, entity_id: str) -> Optional[str]:
        if USE_LOCAL_FALLBACK:
            return self.sqlite_dossier.get_dossier_text(entity_type, entity_id)
        return None

    def get_model_metadata(self, model_name: str) -> Optional[Dict[str, Any]]:
        if USE_LOCAL_FALLBACK:
            return self.sqlite_model.get_model_metadata(model_name)
        return None
