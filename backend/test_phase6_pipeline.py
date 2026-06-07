# backend/test_phase6_pipeline.py
import os
import sys
import time
import json
from fastapi.testclient import TestClient

# Reconfigure stdout to use UTF-8 to prevent cp1252 encoding crashes on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

client = TestClient(app)

def get_auth_token():
    response = client.post("/api/auth/login", json={"username": "analyst", "password": "password123"})
    return response.json()["access_token"]

def main():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    test_cases = [
        {
            "id": 1,
            "description": "Show all chain snatching cases near Whitefield",
            "query": "Show all chain snatching cases near Whitefield"
        },
        {
            "id": 2,
            "description": "List repeat offenders in Indiranagar",
            "query": "List repeat offenders in Indiranagar"
        },
        {
            "id": 3,
            "description": "Show burglary hotspots",
            "query": "Show burglary hotspots"
        },
        {
            "id": 4,
            "description": "Analyze co-accused network for Rajesh Kumar",
            "query": "Analyze co-accused network for Rajesh Kumar"
        },
        {
            "id": 5,
            "description": "ಬೆಂಗಳೂರು ವೈಟ್ಫೀಲ್ಡ್ನಲ್ಲಿ ಸರ ಕಳ್ಳತನ ಪ್ರಕರಣಗಳನ್ನು ತೋರಿಸಿ",
            "query": "ಬೆಂಗಳೂರು ವೈಟ್ಫೀಲ್ಡ್ನಲ್ಲಿ ಸರ ಕಳ್ಳತನ ಪ್ರಕರಣಗಳನ್ನು ತೋರಿಸಿ"
        },
        {
            "id": 6,
            "description": "ಇಂದಿರಾನಗರದಲ್ಲಿ ಪದೇ ಪದೇ ಅಪರಾಧ ಎಸಗುವವರ ಪಟ್ಟಿ",
            "query": "ಇಂದಿರಾನಗರದಲ್ಲಿ ಪದೇ ಪದೇ ಅಪರಾಧ ಎಸಗುವವರ ಪಟ್ಟಿ"
        }
    ]
    
    print("=========================================================")
    print("PHASE 6 MULTILINGUAL PIPELINE VERIFICATION RUN")
    print("=========================================================")
    
    for i, tc in enumerate(test_cases):
        if i > 0:
            # Sleep 15 seconds between requests to avoid hitting 5 RPM rate limit
            print(f"\n[Sleeping 15 seconds to avoid API rate limiting...]")
            time.sleep(15)
            
        print(f"\nQUERY {tc['id']}: \"{tc['query']}\"")
        
        # Call API
        response = client.post(
            "/api/query",
            json={"query": tc["query"], "role": "Analyst", "session_id": "phase6-test-session"},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"ERROR: {response.status_code} - {response.text}")
            continue
            
        data = response.json()
        
        print(f"* Intent: {data.get('intent')}")
        print(f"* Confidence: {data.get('confidence')}")
        print(f"* Execution Mode: {data.get('execution_mode')}")
        print(f"* Model Used: {data.get('model_used')}")
        print(f"* Tokens Used: {data.get('tokens_used')}")
        print(f"* Generated SQL:\n  {data.get('sql_executed')}")
        print(f"* Summary:\n  {data.get('answer')}")
        print(f"* Citations: {data.get('citations')}")
        print("-" * 50)

if __name__ == '__main__':
    main()
