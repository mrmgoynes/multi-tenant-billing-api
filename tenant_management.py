import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

# Configure clean internal orchestration logging
logger = logging.getLogger("tenant_management")

def create_tenant_infrastructure(db: Session, schema_name: str) -> None:
    """
    System Automation: Programmatically spawns an isolated database schema 
    inside the PostgreSQL cluster and clones the core financial tables.
    """
    try:
        logger.info(f"Initiating infrastructure provisioning for target schema: '{schema_name}'")
        
        # 1. Create the unique schema folder namespace for the new tenant
        # Using double quotes to safely handle any complex schema names in PostgreSQL
        db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";'))
        
        # 2. Clone the Customers table structure into the new schema namespace
        db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".customers (
                LIKE tenant_template.customers INCLUDING ALL
            );
        """))
        
        # 3. Clone the Subscriptions table structure into the new schema namespace
        db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".subscriptions (
                LIKE tenant_template.subscriptions INCLUDING ALL
            );
        """))
        
        # 4. Clone the Invoices table structure into the new schema namespace
        db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".invoices (
                LIKE tenant_template.invoices INCLUDING ALL
            );
        """))
        
        # 5. Commit the entire structural generation transaction cleanly
        db.commit()
        logger.info(f"Successfully provisioned isolated tenant environment structures for '{schema_name}'")

    except Exception as e:
        db.rollback()
        logger.error(f"DDL structural compilation failed for workspace '{schema_name}': {str(e)}")
        raise RuntimeError(f"Failed to provision tenant infrastructure: {str(e)}")
