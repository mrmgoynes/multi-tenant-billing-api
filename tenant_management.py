from sqlalchemy.orm import Session
from sqlalchemy import text

def create_tenant_infrastructure(db: Session, schema_name: str):
    """
    System Automation: Programmatically spawns an isolated database schema 
    inside the PostgreSQL container and clones the core financial tables.
    """
    try:
        # 1. Create the unique schema folder for the new tenant
        db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name};"))
        
        # 2. Clone the Customers table structure into the new schema
        db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.customers (
                LIKE tenant_template.customers INCLUDING ALL
            );
        """))
        
        # 3. Clone the Subscriptions table structure into the new schema
        db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.subscriptions (
                LIKE tenant_template.subscriptions INCLUDING ALL
            );
        """))
        
        # 4. Clone the Invoices table structure into the new schema
        db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.invoices (
                LIKE tenant_template.invoices INCLUDING ALL
            );
        """))
        
        # 5. Commit the entire structural generation transaction
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to provision tenant infrastructure: {str(e)}")