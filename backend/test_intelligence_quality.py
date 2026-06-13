# backend/test_intelligence_quality.py
import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app
from backend.database import SessionLocal, execute_raw_sql
from backend.models import AuditLog, Accused, FIR
from backend.gemini_client import simulate_nl_to_sql_dynamic, classify_intent
from backend.graph_engine import build_network_graph
from backend.pattern_engine import detect_hotspots
from backend.evidence_assembler import attach_fir_citations

client = TestClient(app)

def get_auth_token():
    """Helper to authenticate and get JWT token for tests."""
    response = client.post("/api/auth/login", json={"username": "analyst", "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_location_and_crime_type_extraction():
    """Test A: Verifies location + crime type extraction combines filters in SQL with AND."""
    query = "Show all chain snatching cases near Whitefield"
    sql, explanation = simulate_nl_to_sql_dynamic(query)
    
    # Assert both location and crime type are present
    assert "Whitefield" in sql or "Whitefield" in explanation
    assert "chain_snatching" in sql
    # Assert AND logic is used to combine
    assert "AND" in sql

def test_repeat_offender_profiling():
    """Test B: Verifies repeat offender profiling logic fetches Indiranagar repeat accused."""
    query = "List repeat offenders in Indiranagar"
    sql, explanation = simulate_nl_to_sql_dynamic(query)
    
    # Assert GROUP BY and HAVING are present to identify repeat offenders
    assert "GROUP BY" in sql
    assert "HAVING COUNT" in sql or "HAVING count" in sql
    assert "Indiranagar" in sql

def test_graph_expansion_limit():
    """Test C: Verifies 2-hop co-accused network graph expansion for Rajesh Kumar."""
    # Run the query pipeline for Rajesh Kumar network analysis
    token = get_auth_token()
    response = client.post(
        "/api/query",
        json={"query": "Analyze co-accused network for Rajesh", "role": "Analyst", "session_id": "test-graph-session"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    graph = data["graph"]
    
    # Verify Rajesh is the seed node
    assert graph["seed_node"] is not None
    assert "accused-" in graph["seed_node"]
    
    # Verify graph does not include the entire database (strict 2-hop expansion)
    assert len(graph["nodes"]) > 0
    # There are 75+ accused globally, but Rajesh's 2-hop network should be limited
    assert len(graph["nodes"]) < 30

def test_hotspot_generation_query_aware():
    """Test D: Verifies burglary hotspot generation respects query filters."""
    # Execute burglary hotspot query
    token = get_auth_token()
    response = client.post(
        "/api/query",
        json={"query": "Show burglary hotspots", "role": "Analyst", "session_id": "test-hotspot-session"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    heatmap = data["heatmap"]
    
    assert heatmap["type"] == "FeatureCollection"
    # Ensure dominant crime in heatmap clusters is Burglary
    for feature in heatmap["features"]:
        assert feature["properties"]["dominant_crime"] == "Burglary"

def test_evidence_citations_validity():
    """Test E: Verifies citations in response summary match actual database rows."""
    sql_results = [
        {"fir_id": 101, "fir_number": "FIR-2024-00101"},
        {"fir_id": 102, "fir_number": "FIR-2024-00102"}
    ]
    
    # Summary cites valid and invalid FIRs
    summary = "Suspects committed crime in [FIR-2024-00101] and [FIR-2024-99999]"
    
    clean_summary, citations, fir_ids = attach_fir_citations(summary, sql_results)
    
    # Verify only the DB-verified FIR was retained
    assert "FIR-2024-00101" in citations
    assert "FIR-2024-99999" not in citations
    # Verify the invalid citation tag was stripped from text
    assert "[FIR-2024-99999]" not in clean_summary
    assert "[FIR-2024-00101]" in clean_summary

def test_audit_accuracy():
    """Test F: Verifies audit logs accurately store all pipeline execution fields."""
    token = get_auth_token()
    query = "Show all chain snatching cases near Whitefield"
    
    # Execute query to trigger audit logging
    response = client.post(
        "/api/query",
        json={"query": query, "role": "Analyst", "session_id": "test-audit-session"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Check stored record in DB
    db = SessionLocal()
    try:
        latest_audit = db.query(AuditLog).order_by(AuditLog.log_id.desc()).first()
        assert latest_audit is not None
        assert latest_audit.query == query
        assert latest_audit.role == "Analyst"
        assert latest_audit.intent == "RECORD_LOOKUP"
        assert latest_audit.generated_sql is not None
        assert latest_audit.rows_returned is not None
        assert latest_audit.execution_time > 0.0
        assert latest_audit.summary is not None
    finally:
        db.close()

def test_nl_to_sql_query_specificity():
    """Test G: Verifies that different queries generate different SQL queries."""
    sql1, _ = simulate_nl_to_sql_dynamic("Show all chain snatching cases near Whitefield")
    sql2, _ = simulate_nl_to_sql_dynamic("Show burglary hotspots")
    sql3, _ = simulate_nl_to_sql_dynamic("Analyze co-accused network for Rajesh")
    
    assert sql1 != sql2
    assert sql2 != sql3
    assert sql1 != sql3

def test_bridge_suspect_calculation():
    """Verify that suspect bridge scores are computed using community mapping and centrality."""
    from backend.database import execute_raw_sql
    sql_results = execute_raw_sql("SELECT DISTINCT A1.name AS accused_1_name, A2.name AS accused_2_name, A1.accused_id, A2.accused_id, F.fir_id FROM accused AS A1 JOIN fir_accused AS FA1 ON A1.accused_id = FA1.accused_id JOIN firs AS F ON FA1.fir_id = F.fir_id JOIN fir_accused AS FA2 ON F.fir_id = FA2.fir_id JOIN accused AS A2 ON FA2.accused_id = A2.accused_id WHERE A1.name LIKE '%Rajesh%' AND A1.accused_id != A2.accused_id LIMIT 10")
    graph = build_network_graph(sql_results)
    
    assert "nodes" in graph
    accused_nodes = [n for n in graph["nodes"] if n["type"] == "Accused"]
    assert len(accused_nodes) > 0
    for node in accused_nodes:
        assert "bridge_score" in node
        assert "is_bridge" in node
        assert isinstance(node["bridge_score"], float)
        assert isinstance(node["is_bridge"], bool)

def test_document_ingest_pipeline():
    """Verify the two-stage document ingestion pipeline: parse draft then confirm."""
    token = get_auth_token()
    
    # 1. Parse draft
    from io import BytesIO
    file_content = b"Image content with handwritten notes about a burglary in Koramangala 5th Block."
    response_parse = client.post(
        "/api/ingest/parse",
        files={"file": ("burglary_note.png", BytesIO(file_content), "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response_parse.status_code == 200
    data_parse = response_parse.json()
    assert data_parse["success"] is True
    assert "metadata" in data_parse
    draft = data_parse["draft"]
    assert "fir" in draft
    assert "accused" in draft
    assert "confidence" in draft["fir"]["fir_number"]
    assert "value" in draft["fir"]["fir_number"]
    
    # 2. Confirm ingestion
    payload_confirm = {
        "fir": {
            "fir_number": draft["fir"]["fir_number"]["value"],
            "date": draft["fir"]["date"]["value"],
            "crime_type": draft["fir"]["crime_type"]["value"],
            "description": draft["fir"]["description"]["value"] + " (Verified)",
            "status": "Under Investigation",
            "location_name": draft["fir"]["location_name"]["value"],
            "station_area": draft["fir"]["station_area"]["value"],
            "district": draft["fir"]["district"]["value"]
        },
        "accused": [
            {
                "name": draft["accused"][0]["name"]["value"],
                "age": draft["accused"][0]["age"]["value"],
                "gender": draft["accused"][0]["gender"]["value"],
                "occupation": draft["accused"][0]["occupation"]["value"],
                "address": draft["accused"][0]["address"]["value"],
                "role": "Principal"
            }
        ],
        "victims": [
            {
                "name": draft["victims"][0]["name"]["value"],
                "age": draft["victims"][0]["age"]["value"],
                "gender": draft["victims"][0]["gender"]["value"]
            }
        ],
        "document_reference": "burglary_note.png"
    }
    
    response_confirm = client.post(
        "/api/ingest/confirm",
        json=payload_confirm,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response_confirm.status_code == 200
    data_confirm = response_confirm.json()
    assert data_confirm["success"] is True
    assert "fir_id" in data_confirm
    assert data_confirm["fir_number"] == draft["fir"]["fir_number"]["value"]
    
    # Check database persistence
    db = SessionLocal()
    try:
        inserted_fir = db.query(FIR).filter(FIR.fir_number == draft["fir"]["fir_number"]["value"]).first()
        assert inserted_fir is not None
        assert inserted_fir.document_reference == "burglary_note.png"
        assert "Verified" in inserted_fir.description
    finally:
        db.close()

def test_prosecutorial_dossier_generation():
    """Verify that case dossiers are generated with facts and inferences clearly separated and cited."""
    token = get_auth_token()
    response = client.post(
        "/api/dossier",
        json={"query": "Show burglary hotspots", "session_id": "test-dossier-session"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    dossier = data["dossier"]
    assert "FACTUAL DATABASE EVIDENCE" in dossier
    assert "PROSECUTORIAL AI INFERENCES" in dossier
    assert "RECOMMENDED INVESTIGATIVE LEADS" in dossier
    assert "[FIR-" in dossier

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
