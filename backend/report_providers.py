# backend/report_providers.py
from abc import ABC, abstractmethod
import os
from backend.config.catalyst_config import USE_SMARTBROWZ, USE_LOCAL_FALLBACK
from backend.storage_providers import storage_manager

class ReportProvider(ABC):
    @abstractmethod
    def generate_pdf(self, html_content: str, output_name: str) -> str:
        """Generates a PDF from HTML and returns the storage path/URL."""
        pass

class LocalPDFProvider(ReportProvider):
    def generate_pdf(self, html_content: str, output_name: str) -> str:
        # Mock high-fidelity PDF by saving raw text content to a report file
        # This prevents external compiler binary errors (like wkhtmltopdf missing)
        temp_dir = "C:/Users/trivi/.gemini/antigravity/brain/778851e5-df3d-4ba0-8ee3-d5fc7eb5eabe/scratch"
        os.makedirs(temp_dir, exist_ok=True)
        
        pdf_path = os.path.join(temp_dir, output_name)
        with open(pdf_path, "w", encoding="utf-8") as f:
            f.write(f"%PDF-1.4 (SIDDHI MOCK REPORT)\n\n{html_content}")
            
        # Copy to storage
        storage_url = storage_manager.upload(pdf_path, output_name)
        return storage_url

class SmartBrowzProvider(ReportProvider):
    def generate_pdf(self, html_content: str, output_name: str) -> str:
        # Mock Catalyst SmartBrowz API call
        # SmartBrowz posts to: https://api.zohocatalyst.com/smartbrowz/v1/pdf
        cloud_pdf_url = f"https://smartbrowz.zohocatalyst.com/siddhi/reports/pdf/{output_name}"
        
        if USE_LOCAL_FALLBACK:
            # Fall back to generating local mock copy
            local_provider = LocalPDFProvider()
            local_provider.generate_pdf(html_content, output_name)
            
        return cloud_pdf_url

class ReportManager:
    def __init__(self):
        if USE_SMARTBROWZ:
            self._provider = SmartBrowzProvider()
        else:
            self._provider = LocalPDFProvider()

    def generate(self, html_content: str, output_name: str) -> str:
        return self._provider.generate_pdf(html_content, output_name)

report_manager = ReportManager()
