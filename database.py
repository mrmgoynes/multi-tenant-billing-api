import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
from tenant_context import get_tenant_schema

# 1. Scan and parse your local .env configuration matrix into OS memory space
load_dotenv()

# 2. Extract the connection profile securely or fall back to a safe placeholder structure
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("CRITICAL ENVIRONMENT CONFIGURATION ERROR: DATABASE_URL secrets metric is missing!")

# Establish high-performance enterprise connection pooling
engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20,
    pool_pre_ping=True
)

# Core Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        active_schema = get_tenant_schema()
        db.execute(text(f'SET search_path TO "{active_schema}", public;'))
        db.commit()
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()