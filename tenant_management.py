import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger("tenant_management")

def create_tenant_infrastructure(db: Session, schema_name: str) -> None:
    """
    System Automation: Programmatically spawns an isolated database schema,
    clones core tables, and seeds the tenant workspace with default subscription plans.
    """
    try:
        logger.info(f"Initiating infrastructure provisioning for target schema: '{schema_name}'")
        
        # 1. Create unique schema folder namespace
        db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";'))
        
        # 2. Clone table structures from templates
        db.execute(text(f'CREATE TABLE IF NOT EXISTS "{schema_name}".customers (LIKE tenant_template.customers INCLUDING ALL);'))
        db.execute(text(f'CREATE TABLE IF NOT EXISTS "{schema_name}".subscriptions (LIKE tenant_template.subscriptions INCLUDING ALL);'))
        db.execute(text(f'CREATE TABLE IF NOT EXISTS "{schema_name}".invoices (LIKE tenant_template.invoices INCLUDING ALL);'))
        
        # NEW: Clone the structural plans table definition
        db.execute(text(f'CREATE TABLE IF NOT EXISTS "{schema_name}".plans (LIKE tenant_template.plans INCLUDING ALL);'))
        db.commit()

        # 3. SDET SYSTEM SEEDER: Populate base product tiers into the isolated workspace
        logger.info(f"Seeding default subscription tier metadata products into '{schema_name}'")
        db.execute(text(f"""
            INSERT INTO "{schema_name}".plans (name, price, billing_cycle) VALUES 
            ('Basic Tier', 19.99, 'monthly'),
            ('Pro Tier', 49.99, 'monthly'),
            ('Enterprise Tier', 199.99, 'monthly')
            ON CONFLICT DO NOTHING;
        """))
        db.commit()
        
        logger.info(f"Successfully provisioned and seeded tenant workspace environment for '{schema_name}'")

    except Exception as e:
        db.rollback()
        logger.error(f"DDL structural compilation/seeding failed for workspace '{schema_name}': {str(e)}")
        raise RuntimeError(f"Failed to provision tenant infrastructure: {str(e)}")