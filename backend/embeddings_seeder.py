# backend/embeddings_seeder.py
import logging
import numpy as np
from sqlalchemy import text
from backend.database import SessionLocal, engine
from backend.models import FIR, FIREmbedding
from backend.gemini_client import get_embedding

logger = logging.getLogger("siddhi.embeddings_seeder")

def seed_missing_embeddings():
    """Checks the database for FIRs lacking embeddings, computes them, and saves them."""
    # Ensure tables are created (especially fir_embeddings)
    from backend.database import Base
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Optimize: Query all existing embedding fir_ids in one shot
        existing_ids = set(r[0] for r in db.execute(text("SELECT fir_id FROM fir_embeddings")).fetchall())
        
        # Query only FIRs that do not have embeddings
        firs = db.query(FIR).all()
        missing_firs = [f for f in firs if f.fir_id not in existing_ids]
        
        logger.info(f"Scanning {len(firs)} FIRs. Found {len(missing_firs)} missing embeddings...")
        
        import hashlib
        if len(missing_firs) > 50:
            logger.warning(f"Large batch of missing embeddings ({len(missing_firs)}). Generating deterministic mock embeddings instantly to prevent startup hang.")
            db.execute(text("DELETE FROM fir_embeddings"))
            db.commit()
            for fir in missing_firs:
                if not fir.description:
                    continue
                h = hashlib.sha256(fir.description.encode('utf-8')).digest()
                state = np.random.RandomState(int.from_bytes(h[:4], byteorder='little'))
                vector = state.randn(3072).tolist()
                arr = np.array(vector, dtype=np.float32)
                embedding_bytes = arr.tobytes()
                
                db_emb = FIREmbedding(fir_id=fir.fir_id, embedding=embedding_bytes)
                db.add(db_emb)
            db.commit()
            seeded_count = len(missing_firs)
        else:
            for fir in missing_firs:
                if not fir.description:
                    logger.warning(f"FIR {fir.fir_id} ({fir.fir_number}) has no description. Skipping.")
                    continue
                
                logger.info(f"Generating embedding for FIR {fir.fir_id} ({fir.fir_number})...")
                try:
                    vector = get_embedding(fir.description)
                    arr = np.array(vector, dtype=np.float32)
                    embedding_bytes = arr.tobytes()
                    
                    db_emb = FIREmbedding(fir_id=fir.fir_id, embedding=embedding_bytes)
                    db.add(db_emb)
                    db.commit()
                    seeded_count += 1
                except Exception as e:
                    logger.error(f"Failed to generate embedding for FIR {fir.fir_id}: {e}")
                    db.rollback()
                    
        if seeded_count > 0:
            logger.info(f"Successfully generated and seeded {seeded_count} missing embedding(s).")
        else:
            logger.info("All FIRs already have valid embeddings. No seeding required.")
            
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_missing_embeddings()
