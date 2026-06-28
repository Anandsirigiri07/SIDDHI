# backend/storage_providers.py
from abc import ABC, abstractmethod
import os
import shutil
from backend.config.catalyst_config import USE_STRATUS, USE_LOCAL_FALLBACK

class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, file_path: str, destination_name: str) -> str:
        """Uploads a file to storage and returns the access URL/identifier."""
        pass

    @abstractmethod
    def download_file(self, file_name: str, local_path: str) -> bool:
        """Downloads a file from storage to a local path."""
        pass

class LocalStorage(StorageProvider):
    def __init__(self, base_dir: str = "C:/Users/trivi/.gemini/antigravity/brain/778851e5-df3d-4ba0-8ee3-d5fc7eb5eabe/scratch"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, file_path: str, destination_name: str) -> str:
        dest_path = os.path.join(self.base_dir, destination_name)
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy2(file_path, dest_path)
        return f"file:///{dest_path.replace(chr(92), '/')}"

    def download_file(self, file_name: str, local_path: str) -> bool:
        source_path = os.path.join(self.base_dir, file_name)
        if os.path.exists(source_path):
            if os.path.abspath(source_path) != os.path.abspath(local_path):
                shutil.copy2(source_path, local_path)
            return True
        return False

class StratusStorage(StorageProvider):
    def upload_file(self, file_path: str, destination_name: str) -> str:
        # Mock Catalyst Stratus Cloud Storage API upload
        # Stratus API returns a cloud URL
        cloud_url = f"https://stratus.zohocatalyst.com/siddhi-files/buckets/reports/{destination_name}"
        
        if USE_LOCAL_FALLBACK:
            # Mirror locally
            local_store = LocalStorage()
            local_store.upload_file(file_path, destination_name)
            
        return cloud_url

    def download_file(self, file_name: str, local_path: str) -> bool:
        # Mock Catalyst Stratus Cloud Storage API download
        if USE_LOCAL_FALLBACK:
            local_store = LocalStorage()
            return local_store.download_file(file_name, local_path)
        return True

class StorageManager:
    def __init__(self):
        if USE_STRATUS:
            self._provider = StratusStorage()
        else:
            self._provider = LocalStorage()

    def upload(self, file_path: str, destination_name: str) -> str:
        return self._provider.upload_file(file_path, destination_name)

    def download(self, file_name: str, local_path: str) -> bool:
        return self._provider.download_file(file_name, local_path)

storage_manager = StorageManager()
