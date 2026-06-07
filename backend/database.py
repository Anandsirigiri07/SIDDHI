# backend/database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./siddhi.db")

connect_args = {}
# For SQLite, disable cross-thread access check to prevent issues in multi-threaded FastAPI
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def execute_raw_sql(sql_query: str):
    """
    Executes raw SQL query directly on the connection pool.
    Bypasses SQLAlchemy ORM entirely, returning list of dictionaries.
    """
    with engine.connect() as connection:
        # SQLAlchemy requires transaction commit or autocommit, but we are doing SELECT only
        result = connection.execute(text(sql_query))
        # Convert result rows into a list of dicts
        keys = list(result.keys())
        rows = [dict(zip(keys, row)) for row in result.fetchall()]
        return rows
