from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from sqlalchemy.sql import func
from database import Base

class Tenant(Base):
    """
    Python mapping for the public.tenants table.
    Tracks all active business corporate entities on the platform.
    """
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended')", name="check_tenant_status"),
        {"schema": "public"} # Explicitly tells the engine to lock this table to the controller schema
    )

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    tenant_schema = Column(String(50), unique=True, nullable=False)
    subdomain = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Customer(Base):
    """
    Python mapping for the tenant-specific customers table.
    Housed dynamically inside individual client schema folders.
    """
    __tablename__ = "customers"
    
    # Note: We DO NOT specify a schema here because our database.py 
    # search path switcher hook will dynamically inject the schema name at runtime!
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())