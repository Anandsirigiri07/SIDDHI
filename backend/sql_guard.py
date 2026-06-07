# backend/sql_guard.py
import re

ALLOWED_TABLES = {"users", "locations", "officers", "firs", "accused", "fir_accused", "victims", "audit_logs"}
FORBIDDEN_KEYWORDS = {"update", "delete", "drop", "insert", "alter", "truncate", "attach", "pragma"}

def clean_query(sql: str) -> str:
    """Normalizes spacing in the SQL query."""
    return re.sub(r'\s+', ' ', sql).strip()

def validate_query(sql: str) -> bool:
    """
    Validates if a SQL query is a secure read-only SELECT query.
    Blocks forbidden keywords, multiple statements, and unlisted tables.
    """
    sql_clean = clean_query(sql)
    sql_lower = sql_clean.lower()

    # 1. Block write-related keywords using word boundaries
    for kw in FORBIDDEN_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, sql_lower):
            return False

    # 2. Reject multi-statement chaining
    # Only a single trailing semicolon is allowed
    statements = [s.strip() for s in sql_clean.split(';') if s.strip()]
    if len(statements) > 1:
        return False

    # 3. Verify that the query ONLY queries whitelisted tables.
    # Look for identifiers following FROM or JOIN
    from_join_patterns = [
        r'\bfrom\s+([a-zA-Z0-9_]+)',
        r'\bjoin\s+([a-zA-Z0-9_]+)'
    ]
    
    tables_found = []
    for pattern in from_join_patterns:
        matches = re.findall(pattern, sql_lower)
        tables_found.extend(matches)

    # If FROM/JOIN matches are found, ensure they are in whitelisted ALLOWED_TABLES
    for table in tables_found:
        if table not in ALLOWED_TABLES:
            return False
            
    # As a secondary check, verify no query text contains reference to system tables
    if "sqlite_master" in sql_lower or "information_schema" in sql_lower:
        return False

    return True

def rewrite_query(sql: str) -> str:
    """
    Cleans and rewrites the query, appending LIMIT 100 if no limit is present.
    """
    sql_clean = clean_query(sql)
    
    # Strip trailing semicolon for appending LIMIT
    if sql_clean.endswith(';'):
        query_body = sql_clean[:-1].strip()
    else:
        query_body = sql_clean

    query_lower = query_body.lower()

    # Append LIMIT 100 if it does not already contain a limit statement
    if 'limit' not in query_lower:
        query_body = f"{query_body} LIMIT 100"

    return f"{query_body};"
