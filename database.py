import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The network address path to our PostgreSQL container running over Port 5432
DATABASE_URL = "postgresql+psycopg://admin:SecretPassword123@localhost:5432/billing_system"

# Create the core database connectivity engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Generate an isolated session class for executing queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The base class that our python database models will inherit from
Base = declarative_base()

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