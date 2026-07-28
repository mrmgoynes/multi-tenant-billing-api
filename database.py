from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from tenant_context import get_tenant_schema

# Explicitly use +psycopg to leverage your installed modern v3 driver
DATABASE_URL = "postgresql+psycopg://admin:SecretPassword123@localhost:5432/billing_system"

# Establish high-performance enterprise connection pooling
engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20,
    pool_pre_ping=True  # Automatically audits and revives dropped database connections
)

# Core Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==============================================================================
# ARCHITECTURAL LINK: Declarative Mapping Foundation
# This provides the shared metadata tracking hook required by your models.py file
# ==============================================================================
class Base(DeclarativeBase):
    """
    Central Database Metadata Registry:
    Tracks all declarative table structures across both central and tenant tables.
    """
    pass

def get_db():
    """
    Dynamic Database Session Context Provider:
    Spawns an isolated transaction session and forces its search path to the active tenant.
    """
    db = SessionLocal()
    try:
        # 1. Fetch the thread-safe context value managed by your middleware
        active_schema = get_tenant_schema()
        
        # 2. Instruct PostgreSQL to prioritize the active tenant's schema space
        db.execute(text(f'SET search_path TO "{active_schema}", public;'))
        db.commit()  # Seal the search path context inside this transaction thread
        
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
