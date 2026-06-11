# backend/main.py
import os
import json
import logging
import time
import re
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import backend modules
from backend.database import get_db, execute_raw_sql
from backend.models import User, FIR, AuditLog, Location, Officer, Victim
from backend.auth import (
    get_current_user,
    verify_password,
    create_access_token,
    RoleChecker
)
from backend.translator import translate_query_to_english, translate_response_to_lang
from backend.gemini_client import (
    classify_intent,
    generate_nl_to_sql,
    summarize_results,
    GEMINI_API_KEY
)
from backend.sql_guard import validate_query, rewrite_query
from backend.session_manager import session_manager
from backend.graph_engine import build_network_graph
from backend.pattern_engine import detect_hotspots
from backend.forecast_engine import forecast_hotspots
from backend.evidence_assembler import generate_final_response, create_audit_record

# Setup logger
logger = logging.getLogger("siddhi.main")
logging.basicConfig(level=logging.INFO)

# Initialize slowapi rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="SIDDHI Crime Intelligence API",
    description="Backend service for Situational Intelligence Dashboard for Dynamic Hotspot Investigation",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
def startup_event():
    if GEMINI_API_KEY:
        logger.info("Gemini API Key Detected: TRUE")
    else:
        logger.warning("Gemini API Key Detected: FALSE")


# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str
    role: str
    session_id: str

def get_total_rows_count(sql: str) -> int:
    """Calculates the total matching rows without LIMIT using a subquery wrapper."""
    # Strip LIMIT and OFFSET clauses from query
    clean_sql = re.sub(r'\s+LIMIT\s+\d+(?:\s+OFFSET\s+\d+)?\b', '', sql, flags=re.IGNORECASE)
    clean_sql = clean_sql.rstrip(';').strip()
    
    count_sql = f"SELECT COUNT(*) FROM ({clean_sql}) AS temp_count"
    try:
        results = execute_raw_sql(count_sql)
        if results:
            return list(results[0].values())[0]
    except Exception as e:
        logger.warning(f"Count subquery failed: {e}. Falling back to counting in python.")
        try:
            results = execute_raw_sql(clean_sql)
            return len(results)
        except Exception:
            return 0
    return 0

# Endpoints
@app.get("/health")
def health_check():
    """Simple API status checker."""
    return {"status": "healthy", "service": "siddhi-backend"}

@app.get("/api/forecast")
@limiter.limit("20/minute")
def get_hotspot_forecast(request: Request, current_user: User = Depends(get_current_user)):
    """Predicts next-week hotspot intensity per spatial cluster (exponential smoothing baseline)."""
    try:
        return forecast_hotspots()
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation error: {str(e)}"
        )

@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials and issues JWT token."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "role": user.role,
            "name": user.name
        }
    }

@app.post("/api/query")
@limiter.limit("10/minute")
def run_crime_query(
    request: Request,
    payload: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Main analytical query pipeline.
    Translates English/Kannada queries, classifies intent, generates SQL,
    performs network graphs and hotspot clustering, and returns unified Triple-Lens payloads.
    Logs audited operations and returns debug statistics.
    """
    start_time = time.time()
    
    # Role Enforcement
    if current_user.role != payload.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. User role '{current_user.role}' does not match requested role '{payload.role}'"
        )

    # Initialize debug data collector
    debug_data = {"tokens_used": 0}

    # STEP 1 & 2: Ingestion and Language Translation
    english_query, original_lang = translate_query_to_english(payload.query, debug_data=debug_data)
    logger.info(f"Ingested query: {payload.query} | Processed query: {english_query} | Lang: {original_lang}")

    # STEP 3: Intent Classification
    session_context = session_manager.get_context(payload.session_id)
    classification = classify_intent(english_query, session_context, debug_data=debug_data)
    intent = classification.get("intent", "RECORD_LOOKUP")
    entities = classification.get("entities", [])
    confidence = classification.get("confidence", 0.9)

    # STEP 4: Session Memory Update
    session_manager.update_context(payload.session_id, english_query, intent=intent, entities=entities)

    # STEP 5: NL to SQL Generation
    sql_payload = generate_nl_to_sql(english_query, payload.role, session_context, debug_data=debug_data)
    raw_sql = sql_payload.get("sql", "")
    explanation = sql_payload.get("explanation", "")

    # STEP 6: SQL Security Guard (Validate & Rewrite)
    if not validate_query(raw_sql):
        logger.warning(f"SQL Guard blocked query: {raw_sql}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SQL Security Violation: Generated query was blocked. Prompt: {raw_sql}"
        )

    rewritten_sql = rewrite_query(raw_sql)
    logger.info(f"Executing SQL: {rewritten_sql}")

    # STEP 7: direct SQLite query execution
    try:
        sql_results = execute_raw_sql(rewritten_sql)
    except Exception as e:
        logger.error(f"SQL Execution Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database execution error: {str(e)}"
        )

    # Calculate total matching rows
    total_rows = get_total_rows_count(rewritten_sql)

    # STEP 8: Run Graph Engine (passes query-specific rows)
    graph_data = build_network_graph(sql_results)

    # STEP 9: Run Pattern Engine (DBSCAN + Spikes)
    pattern_data = detect_hotspots(sql_results)

    # STEP 10: Summarize Results citing FIRs
    summary = summarize_results(english_query, sql_results, debug_data=debug_data)

    # STEP 11: Evidence Assembly
    final_response = generate_final_response(
        summary,
        sql_results,
        graph_data,
        pattern_data,
        rewritten_sql,
        explanation
    )

    # STEP 12: Back Translation if input was Kannada
    if original_lang == 'kn':
        translated_answer = translate_response_to_lang(final_response["answer"], 'kn', debug_data=debug_data)
        final_response["answer"] = translated_answer


    # Inject execution metadata
    execution_time = time.time() - start_time
    fallback_triggered = debug_data.get("fallback_triggered", False)
    execution_mode = "gemini" if (GEMINI_API_KEY and not fallback_triggered) else "fallback"
    if fallback_triggered:
        logger.warning(f"Gemini execution failed; falling back to simulated mode. Reason: {debug_data.get('fallback_reason', 'Unknown')}")
    
    # Update final response
    final_response["execution_mode"] = execution_mode
    final_response["model_used"] = debug_data.get("model_used", "simulated-fallback-model")
    final_response["tokens_used"] = debug_data.get("tokens_used", 0)
    final_response["intent"] = intent
    final_response["confidence"] = confidence
    final_response["total_rows_found"] = total_rows
    final_response["rows_returned"] = len(sql_results)
    
    # Add count details to evidence sub-object
    final_response["evidence"]["total_rows_found"] = total_rows
    final_response["evidence"]["rows_returned"] = len(sql_results)
    
    # Inject debug statistics
    final_response["debug"] = {
        "intent_prompt": debug_data.get("intent_prompt", ""),
        "sql_prompt": debug_data.get("sql_prompt", ""),
        "summary_prompt": debug_data.get("summary_prompt", ""),
        "model_used": debug_data.get("model_used", "simulated-fallback-model"),
        "tokens_used": debug_data.get("tokens_used", 0)
    }

    # STEP 13: Audit logging
    try:
        audit_entry = AuditLog(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id=current_user.user_id,
            username=current_user.username,
            role=payload.role,
            query=payload.query,
            intent=intent,
            entities=json.dumps(entities),
            generated_sql=rewritten_sql,
            rows_returned=len(sql_results),
            summary=final_response["answer"],
            execution_time=round(execution_time, 4)
        )
        db.add(audit_entry)
        db.commit()
    except Exception as ae:
        logger.error(f"Failed to record audit log: {ae}")

    return final_response

@app.get("/api/fir/{fir_id}")
def get_fir_details(fir_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns detailed metadata of a specific FIR."""
    fir = db.query(FIR).filter(FIR.fir_id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR record not found")
        
    location = db.query(Location).filter(Location.location_id == fir.location_id).first()
    officer = db.query(Officer).filter(Officer.officer_id == fir.officer_id).first()
    
    # Get associated victims
    victims = db.query(Victim).filter(Victim.fir_id == fir.fir_id).all()
    victims_list = [{"name": v.name, "age": v.age, "gender": v.gender} for v in victims]

    # Get associated accused
    accused_query = text("""
        SELECT a.accused_id, a.name, a.age, a.gender, a.occupation, a.address, a.risk_score, fa.role
        FROM fir_accused fa
        JOIN accused a ON fa.accused_id = a.accused_id
        WHERE fa.fir_id = :fir_id
    """)
    accused_records = db.execute(accused_query, {"fir_id": fir.fir_id}).fetchall()
    accused_list = []
    for r in accused_records:
        accused_list.append({
            "accused_id": r[0],
            "name": r[1],
            "age": r[2],
            "gender": r[3],
            "occupation": r[4],
            "address": r[5],
            "risk_score": r[6],
            "role": r[7]
        })

    return {
        "fir_id": fir.fir_id,
        "fir_number": fir.fir_number,
        "date": fir.date,
        "crime_type": fir.crime_type,
        "description": fir.description,
        "status": fir.status,
        "location": {
            "name": location.name,
            "lat": location.lat,
            "lng": location.lng,
            "district": location.district
        } if location else None,
        "officer": {
            "name": officer.name,
            "rank": officer.rank,
            "station": officer.station
        } if officer else None,
        "victims": victims_list,
        "accused": accused_list
    }

@app.get("/api/audit")
def get_audit_trail(
    current_user: User = Depends(RoleChecker(allowed_roles=["Supervisor"])),
    db: Session = Depends(get_db)
):
    """Retrieves all query audit logs. Enforced for Supervisor role only."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    audit_list = []
    for log in logs:
        audit_list.append({
            "log_id": log.log_id,
            "timestamp": log.timestamp,
            "username": log.username,
            "role": log.role,
            "query": log.query,
            "intent": log.intent,
            "entities": json.loads(log.entities) if log.entities else [],
            "generated_sql": log.generated_sql,
            "rows_returned": log.rows_returned,
            "summary": log.summary,
            "execution_time": log.execution_time
        })
    return audit_list
