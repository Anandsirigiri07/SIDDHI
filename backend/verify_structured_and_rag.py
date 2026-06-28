# backend/verify_structured_and_rag.py
import logging
import sys
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import FIR, FIREmbedding
from backend.gemini_client import (
    classify_intent,
    generate_nl_to_sql,
    semantic_search_firs,
    get_embedding
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("siddhi.verification")

def verify():
    logger.info("Initializing Verification of Structured Outputs and Semantic RAG...")
    
    # 1. Database and Seeding Check
    db = SessionLocal()
    try:
        from backend.embeddings_seeder import seed_missing_embeddings
        logger.info("Running seeder to ensure database has embeddings...")
        seed_missing_embeddings()
        
        # Verify fir_embeddings table population
        total_firs = db.query(FIR).count()
        total_embs = db.query(FIREmbedding).count()
        logger.info(f"Database contains {total_firs} FIRs and {total_embs} Embeddings.")
        
        if total_embs == 0 and total_firs > 0:
            logger.error("ERROR: Embeddings seeder failed to populate embeddings.")
            sys.exit(1)
        elif total_firs == 0:
            logger.warning("Database is empty. Skipping database seeder checks.")
        else:
            logger.info("SUCCESS: Database embeddings table verified.")
            
        # 2. Semantic Search Check
        if total_embs > 0:
            logger.info("Testing semantic search...")
            matches = semantic_search_firs("burglary at Koramangala store", db, limit=2)
            logger.info(f"Semantic search returned {len(matches)} matches:")
            for m in matches:
                logger.info(f" - {m['fir_number']}: score={m['score']:.4f}, desc={m['description'][:60]}...")
            
            if not matches:
                logger.error("ERROR: Semantic search returned no matches.")
                sys.exit(1)
            logger.info("SUCCESS: Semantic search verified.")
            
        # 3. Intent Classification Check (Structured Outputs)
        logger.info("Testing Intent Classification structured output schema...")
        context = {"queries": []}
        classification = classify_intent("Show me chain snatching near Whitefield", context)
        logger.info(f"Classified intent response keys: {list(classification.keys())}")
        logger.info(f"Result: {classification}")
        
        assert "intent" in classification
        assert "confidence" in classification
        assert "entities" in classification
        assert "requires_graph" in classification
        assert "requires_map" in classification
        logger.info("SUCCESS: Intent Classification schema compliance verified.")
        
        # 4. SQL Generation Check (Structured Outputs)
        logger.info("Testing NL to SQL structured output schema...")
        sql_res = generate_nl_to_sql("Show all robberies", "Analyst", context)
        logger.info(f"NL to SQL response keys: {list(sql_res.keys())}")
        logger.info(f"Result: {sql_res}")
        
        assert "sql" in sql_res
        assert "explanation" in sql_res
        logger.info("SUCCESS: NL to SQL schema compliance verified.")
        
        logger.info("--- ALL VERIFICATIONS COMPLETED SUCCESSFULLY ---")
        
    except Exception as e:
        logger.exception(f"Verification failed with exception: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify()
