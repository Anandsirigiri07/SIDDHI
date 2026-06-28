# backend/test_phase5_intelligence.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from sqlalchemy import text

client = TestClient(app)

def get_auth_token():
    response = client.post(
        "/api/auth/login",
        json={"username": "analyst", "password": "password123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_suspect_dossier_api():
    """Verify suspect dossier endpoint returns structured JSON and cited prose."""
    token = get_auth_token()
    db = SessionLocal()
    try:
        sus_id = db.execute(text("SELECT accused_id FROM accused LIMIT 1")).scalar()
    finally:
        db.close()
        
    response = client.post(
        f"/api/v2/intelligence/dossier/suspect/{sus_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "structured_data" in data
    assert "dossier" in data
    
    dossier = data["dossier"]
    assert "FACTUAL DATABASE EVIDENCE" in dossier
    assert "PROSECUTORIAL AI INFERENCES" in dossier
    assert "RECOMMENDED INVESTIGATIVE LEADS" in dossier

def test_case_priority_dossier_api():
    """Verify case priority dossier endpoint returns priority risk bands and CI bounds."""
    token = get_auth_token()
    db = SessionLocal()
    try:
        case_id = db.execute(text("SELECT fir_id FROM firs LIMIT 1")).scalar()
    finally:
        db.close()
        
    response = client.post(
        f"/api/v2/intelligence/dossier/case/{case_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "structured_data" in data
    assert "dossier" in data
    
    dossier = data["dossier"]
    assert "FACTUAL DATABASE EVIDENCE" in dossier
    assert "PROSECUTORIAL AI INFERENCES" in dossier
    assert "RECOMMENDED INVESTIGATIVE LEADS" in dossier
    # Verify delay is forecast with bounds
    assert "Filing Delay Forecast" in dossier

def test_district_intelligence_api():
    """Verify district intelligence API returns hotspot shift analysis and rankings."""
    token = get_auth_token()
    response = client.get(
        "/api/v2/intelligence/district/Bengaluru East",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "structured_data" in data
    
    struct = data["structured_data"]
    assert struct["district_name"] == "Bengaluru East"
    assert "hotspot_movement_analysis" in struct
    assert "district_ranking" in struct

def test_executive_briefing_api():
    """Verify city-wide executive briefing is formatted beautifully for command review."""
    token = get_auth_token()
    response = client.post(
        "/api/v2/intelligence/summary/executive",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "briefing" in data
    
    briefing = data["briefing"]
    assert "FACTUAL DATABASE EVIDENCE" in briefing
    assert "PROSECUTORIAL AI INFERENCES" in briefing
    assert "RECOMMENDED INVESTIGATIVE LEADS" in briefing
