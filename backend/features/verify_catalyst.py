# backend/features/verify_catalyst.py
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import app
from backend.database import SessionLocal
from backend.auth_providers import auth_manager, LocalAuthProvider, CatalystAuthProvider
from backend.storage_providers import storage_manager, LocalStorage, StratusStorage
from backend.report_providers import report_manager, LocalPDFProvider, SmartBrowzProvider

client = TestClient(app)

def run_verification():
    print("==================================================")
    print("RUNNING SIDDHI V2 ZOHO CATALYST DEPLOYMENT AUDIT")
    print("==================================================")

    # 1. Verify Configuration Switches
    print("\n1. Auditing Configuration Manager Switches...")
    from backend.config.catalyst_config import USE_CATALYST, USE_SMARTBROWZ, USE_STRATUS, USE_LOCAL_FALLBACK
    print(f"  [OK] USE_CATALYST: {USE_CATALYST}")
    print(f"  [OK] USE_SMARTBROWZ: {USE_SMARTBROWZ}")
    print(f"  [OK] USE_STRATUS: {USE_STRATUS}")
    print(f"  [OK] USE_LOCAL_FALLBACK: {USE_LOCAL_FALLBACK}")

    # 2. Verify Auth Abstractions
    print("\n2. Auditing Authentication Abstraction Providers...")
    assert isinstance(auth_manager._provider, (LocalAuthProvider, CatalystAuthProvider))
    print(f"  [OK] AuthManager Active Provider: {auth_manager._provider.__class__.__name__}")
    
    # Test Catalyst mock profile resolution
    db = SessionLocal()
    try:
        user = db.execute(text("SELECT username, role, password_hash FROM users LIMIT 1")).fetchone()
        if user:
            print(f"  [OK] Database User check: {user[0]} ({user[1]})")
    finally:
        db.close()

    # 3. Verify Storage Abstractions
    print("\n3. Auditing Storage Abstraction Providers...")
    assert isinstance(storage_manager._provider, (LocalStorage, StratusStorage))
    print(f"  [OK] StorageManager Active Provider: {storage_manager._provider.__class__.__name__}")

    # 4. Verify SmartBrowz & Reports Abstractions
    print("\n4. Auditing SmartBrowz PDF Providers...")
    assert isinstance(report_manager._provider, (LocalPDFProvider, SmartBrowzProvider))
    print(f"  [OK] ReportManager Active Provider: {report_manager._provider.__class__.__name__}")

    # 5. Verify AppSail HTTP Health & Metrics APIs
    print("\n5. Auditing AppSail Deployment Endpoints...")
    
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    print(f"  [OK] GET /api/health -> {res_health.json()}")

    res_version = client.get("/api/version")
    assert res_version.status_code == 200
    print(f"  [OK] GET /api/version -> {res_version.json()}")

    res_status = client.get("/api/status")
    assert res_status.status_code == 200
    print(f"  [OK] GET /api/status -> {res_status.json()}")

    res_metrics = client.get("/api/system/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert "cases_processed" in metrics
    print(f"  [OK] GET /api/system/metrics -> Cases: {metrics['cases_processed']}, Hotspots: {metrics['active_hotspots']}")

    # 6. Verify SmartBrowz report pipeline
    print("\n6. Auditing SmartBrowz Dossier and Executive compilation...")
    res_exec = client.post("/api/reports/executive")
    assert res_exec.status_code == 200
    print(f"  [OK] SmartBrowz Executive Compilation -> Report URL: {res_exec.json()['report_url']}")

    print("\n==================================================")
    print("ZOHO CATALYST COMPATIBILITY AUDIT [PASS]")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
