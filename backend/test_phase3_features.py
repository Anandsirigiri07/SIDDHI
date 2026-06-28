# backend/test_phase3_features.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, FeatureStore, FIR, Accused, Officer, HotspotCluster

client = TestClient(app)

def get_auth_token():
    # Login as supervisor or analyst
    response = client.post(
        "/api/auth/login",
        json={"username": "supervisor", "password": "password123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_rebuild_features_api():
    """Verify rebuild endpoint recalculates and returns valid stats."""
    token = get_auth_token()
    response = client.post(
        "/api/v2/features/rebuild",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "statistics" in data
    stats = data["statistics"]
    assert stats["cases"] > 0
    assert stats["status"] == "completed"

def test_get_case_features_api():
    """Verify case features fetch returns expected analytical keys."""
    db = SessionLocal()
    case_id = db.query(FIR.fir_id).first()[0]
    db.close()
    
    token = get_auth_token()
    response = client.get(
        f"/api/v2/features/case/{case_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "severity_score" in data
    assert "gravity_score" in data
    assert "investigation_age" in data
    assert "priority_target" in data

def test_get_suspect_features_api():
    """Verify suspect features fetch returns centralities and target labels."""
    db = SessionLocal()
    suspect_id = db.query(Accused.accused_id).first()[0]
    db.close()
    
    token = get_auth_token()
    response = client.get(
        f"/api/v2/features/suspect/{suspect_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "pagerank_score" in data
    assert "betweenness_score" in data
    assert "degree_centrality" in data
    assert "closeness" in data
    assert "gang_score" in data
    assert "repeat_offender_target" in data

def test_get_officer_features_api():
    """Verify officer features returns workload, backlog, and clearance rate."""
    db = SessionLocal()
    officer_id = db.query(Officer.officer_id).first()[0]
    db.close()
    
    token = get_auth_token()
    response = client.get(
        f"/api/v2/features/officer/{officer_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "active_cases" in data
    assert "officer_load" in data
    assert "clearance_rate" in data
    assert "case_backlog" in data

def test_get_hotspot_features_api():
    """Verify hotspot features returns size, risk, density, and growth targets."""
    db = SessionLocal()
    hotspot_id = db.query(HotspotCluster.cluster_id).first()[0]
    db.close()
    
    token = get_auth_token()
    response = client.get(
        f"/api/v2/features/hotspot/{hotspot_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "cluster_size" in data
    assert "crime_density" in data
    assert "cluster_risk" in data
    assert "future_cluster_size" in data
    assert "weekly_growth" in data
    assert "emerging_cluster" in data
