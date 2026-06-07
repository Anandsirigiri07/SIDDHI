# backend/test_critical_path.py
import os
import sys
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app
from backend.sql_guard import validate_query, rewrite_query

client = TestClient(app)

def test_health():
    """Verify health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_success():
    """Verify login works for all demo accounts and returns a valid JWT token."""
    credentials = [
        ("investigator", "Investigator"),
        ("analyst", "Analyst"),
        ("supervisor", "Supervisor"),
        ("policymaker", "Policymaker")
    ]
    for username, role in credentials:
        response = client.post("/api/auth/login", json={"username": username, "password": "password123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == username
        assert data["user"]["role"] == role

def test_login_failure():
    """Verify incorrect credentials return 401 unauthorized."""
    response = client.post("/api/auth/login", json={"username": "analyst", "password": "wrongpassword"})
    assert response.status_code == 401

def test_sql_guard_security():
    """Verify SQL Guard blocks destructive queries but permits read-only ones."""
    # Forbidden keywords
    assert not validate_query("DROP TABLE firs")
    assert not validate_query("DELETE FROM accused WHERE accused_id = 1")
    assert not validate_query("UPDATE users SET role = 'Supervisor'")
    assert not validate_query("INSERT INTO locations (name) VALUES ('Test')")
    
    # Semicolon chaining / Multi-statements
    assert not validate_query("SELECT * FROM firs; DROP TABLE users;")
    
    # Non-whitelisted tables
    assert not validate_query("SELECT * FROM passwords")

    # Whitelisted queries
    assert validate_query("SELECT * FROM firs")
    assert validate_query("SELECT * FROM accused JOIN fir_accused ON accused.accused_id = fir_accused.accused_id")

    # Limit rewriting
    assert "LIMIT 100" in rewrite_query("SELECT * FROM firs")
    assert "LIMIT 100" not in rewrite_query("SELECT * FROM firs LIMIT 10") # Preserves custom limits

def test_rbac_restrictions():
    """Verify endpoints enforce correct role constraints."""
    # Obtain analyst token
    analyst_res = client.post("/api/auth/login", json={"username": "analyst", "password": "password123"})
    analyst_token = analyst_res.json()["access_token"]

    # Obtain supervisor token
    supervisor_res = client.post("/api/auth/login", json={"username": "supervisor", "password": "password123"})
    supervisor_token = supervisor_res.json()["access_token"]

    # Analyst accessing supervisor-only audit logs should get 403 Forbidden
    response = client.get("/api/audit", headers={"Authorization": f"Bearer {analyst_token}"})
    assert response.status_code == 403

    # Supervisor accessing audit logs should get 200 OK
    response = client.get("/api/audit", headers={"Authorization": f"Bearer {supervisor_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_query_pipeline_critical_path():
    """Verify that the 4 main queries classify, generate, execute, and yield the Triple-Lens payload."""
    analyst_res = client.post("/api/auth/login", json={"username": "analyst", "password": "password123"})
    token = analyst_res.json()["access_token"]

    queries = [
        "Show all chain snatching cases near Whitefield",
        "List repeat offenders in Indiranagar",
        "Show burglary hotspots",
        "Analyze co-accused network for Rajesh"
    ]

    for q in queries:
        response = client.post(
            "/api/query",
            json={"query": q, "role": "Analyst", "session_id": "test-session-123"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify Triple-Lens structure
        assert "answer" in data
        assert "graph" in data
        assert "heatmap" in data
        assert "alerts" in data
        assert "citations" in data
        assert "fir_ids" in data
        assert "evidence" in data
        assert "sql_executed" in data

        # Verify graph structure D3 keys
        assert "nodes" in data["graph"]
        assert "links" in data["graph"]
        
        # Verify heatmap GeoJSON structure
        assert data["heatmap"]["type"] == "FeatureCollection"
        assert "features" in data["heatmap"]

def test_fir_metadata_details():
    """Verify individual FIR metadata endpoint."""
    analyst_res = client.post("/api/auth/login", json={"username": "analyst", "password": "password123"})
    token = analyst_res.json()["access_token"]

    response = client.get("/api/fir/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "fir_id" in data
    assert "fir_number" in data
    assert "crime_type" in data
    assert "description" in data
    assert "location" in data
    assert "officer" in data
    assert "victims" in data
    assert "accused" in data

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__]))
