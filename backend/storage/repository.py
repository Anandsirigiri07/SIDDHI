# backend/storage/repository.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class CaseMasterRepository(ABC):
    @abstractmethod
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        pass

class FeatureStoreRepository(ABC):
    @abstractmethod
    def get_features(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        pass

class PredictionsRepository(ABC):
    @abstractmethod
    def save_prediction(self, model_name: str, entity_id: str, prediction: Dict[str, Any]) -> None:
        pass

class HotspotsRepository(ABC):
    @abstractmethod
    def get_active_hotspots(self) -> List[Dict[str, Any]]:
        pass

class CommunitiesRepository(ABC):
    @abstractmethod
    def get_community_members(self, community_id: int) -> List[str]:
        pass

class RiskScoresRepository(ABC):
    @abstractmethod
    def get_suspect_risk(self, suspect_id: str) -> Optional[float]:
        pass

class DossiersRepository(ABC):
    @abstractmethod
    def get_dossier_text(self, entity_type: str, entity_id: str) -> Optional[str]:
        pass

class ModelRegistryRepository(ABC):
    @abstractmethod
    def get_model_metadata(self, model_name: str) -> Optional[Dict[str, Any]]:
        pass
