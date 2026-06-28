# backend/test_phase4_predictive.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def get_auth_token():
    response = client.post(
        "/api/auth/login",
        json={"username": "supervisor", "password": "password123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_ml_status_api():
    """Verify ML status endpoint returns the model registry metadata."""
    token = get_auth_token()
    response = client.get(
        "/api/v2/ml/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "last_updated" in data

def test_ml_models_list_api():
    """Verify ML models list returns all five registered model tasks."""
    token = get_auth_token()
    response = client.get(
        "/api/v2/ml/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "repeat_offender" in data
    assert "chargesheet_delay" in data
    assert "priority_predictor" in data
    assert "hotspot_forecast" in data
    assert "crime_classifier" in data

def test_ml_metrics_api():
    """Verify ML metrics endpoint returns candidate metrics."""
    token = get_auth_token()
    response = client.get(
        "/api/v2/ml/metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "repeat_offender" in data
    assert "test" in data["repeat_offender"]

def test_predict_repeat_offender_api():
    """Verify repeat offender prediction works with valid input."""
    token = get_auth_token()
    payload = {
        "pagerank_score": 0.05,
        "betweenness_score": 0.02,
        "degree_centrality": 0.1,
        "closeness": 0.3,
        "prior_case_count": 4.0,
        "gang_score": 0.8,
        "risk_factor_score": 12.0,
        "age": 28.0,
        "gender_code": 0.0,
        "organized_crime_score": 0.75
    }
    response = client.post(
        "/api/v2/ml/repeat-offender",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "repeat_offender_probability" in data
    assert "risk_band" in data
    assert "top_factors" in data

def test_predict_delay_api():
    """Verify chargesheet delay prediction works with valid input."""
    token = get_auth_token()
    payload = {
        "victim_count": 2.0,
        "accused_count": 3.0,
        "officer_load": 4.0,
        "gravity_score": 1.0,
        "district_crime_rate": 250.0,
        "investigation_age": 45.0,
        "court_delay": 120.0,
        "act_count": 2.0,
        "section_count": 4.0
    }
    response = client.post(
        "/api/v2/ml/delay",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_days" in data
    assert "confidence_score" in data
    assert "top_factors" in data

def test_predict_priority_api():
    """Verify priority prediction works with valid input."""
    token = get_auth_token()
    payload = {
        "gravity_score": 1.0,
        "women_involved": 1.0,
        "children_involved": 0.0,
        "repeat_offender_presence": 1.0,
        "gang_score": 0.8,
        "victim_vulnerability": 0.5,
        "weapon_usage": 1.0,
        "community_risk": 45.0,
        "organized_crime_score": 0.75
    }
    response = client.post(
        "/api/v2/ml/priority",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "priority_score" in data
    assert "risk_category" in data
    assert "top_factors" in data

def test_predict_hotspot_api():
    """Verify hotspot forecasting works with valid input."""
    token = get_auth_token()
    payload = {
        "crime_density": 45.2,
        "cluster_risk": 150.0,
        "repeat_offender_density": 0.45,
        "severity_density": 6.5,
        "historical_baseline": 3.2,
        "weekly_change": 1.5,
        "emerging_cluster": 1.0,
        "cluster_size": 250.0
    }
    response = client.post(
        "/api/v2/ml/hotspot",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_cluster_growth" in data
    assert "future_cluster_size" in data
    assert "forecasted_risk" in data

def test_predict_classify_api():
    """Verify crime classification suggestions work with valid input."""
    token = get_auth_token()
    payload = {
        "text_content": "Chain snatching incident reported near Hebbal flyover during morning walk."
    }
    response = client.post(
        "/api/v2/ml/classify",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_crime_head" in data
    assert "predicted_crime_subhead" in data
    assert "suggested_acts" in data
    assert "suggested_sections" in data
