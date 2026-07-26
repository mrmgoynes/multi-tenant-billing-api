import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from tenant_context import get_tenant_schema

# The network address path to our PostgreSQL container running over Port 5432
DATABASE_URL = "postgresql+psycopg://admin:SecretPassword123@localhost:5432/billing_system"

# Create the core database connectivity engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Generate an isolated session class for executing queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The base class that our python database models will inherit from
Base = declarative_base()

# --- ENTERPRISE MULTI-TENANT HOOK ---
@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    """
    Infrastructure Event Listener: The moment a database connection is pulled 
    from the connection pool, this hook dynamically overrides PostgreSQL's 
    search_path to force queries to execute within the active tenant's isolated schema folder.
    """
    cursor = dbapi_connection.cursor()
    active_schema = get_tenant_schema()
    
    # Execute a native PostgreSQL configuration rule to lock the connection scope
    cursor.execute(f"SET search_path TO {active_schema}, public;")
    cursor.close()

def get_db():
    """
    FastAPI Dependency: Yields a clean database session connection 
    per request and ensures it safely closes when finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()