from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, CheckConstraint
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
        {"schema": "public"}
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
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Plan(Base):
    """
    Tenant Structural Model:
    Defines the isolated tier structures available for client subscription mappings.
    """
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    billing_cycle = Column(String(20), default="monthly")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Subscription(Base):
    """
    Tenant Core Business Model:
    Binds an isolated Customer to a specific subscription Plan tier.
    """
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), default="active")
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Invoice(Base):
    """
    Tenant Financial Business Model:
    Tracks billable accounts receivable events generated dynamically per customer billing cycle.
    """
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    invoice_number = Column(String(30), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="unpaid")
    due_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ==============================================================================
# PHASE 21 ARCHITECTURE: HIGH-FREQUENCY EVENT TELEMETRY LEDGER
# ==============================================================================
class UsageRecord(Base):
    """
    Tenant Telemetry Ledger Model:
    Tracks consumption events (e.g., api hits, data processing metrics) 
    utilized to compute dynamic, usage-based customer invoicing tiers.
    """
    __tablename__ = "usage_records"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

