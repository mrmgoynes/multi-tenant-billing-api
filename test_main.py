import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from sqlalchemy import text
import models

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_database():
    """
    SDET Test Fixture: Automated lifecycle manager.
    Wipes master registries and destroys generated test schema folders from Docker.
    """
    yield
    db = SessionLocal()
    try:
        # Wipe master registration records from the public directory table
        db.query(models.Tenant).filter(models.Tenant.subdomain.in_(["stark", "lannister"])).delete()
        db.commit()
        
        # Drop both isolated test schema folders from the PostgreSQL engine
        db.execute(text("DROP SCHEMA IF EXISTS tenant_stark CASCADE;"))
        db.execute(text("DROP SCHEMA IF EXISTS tenant_lannister CASCADE;"))
        db.commit()
    finally:
        db.close()

def test_cross_tenant_data_isolation():
    """
    SDET Multi-Tenant Verification: Proves that data inserted into Tenant A
    is entirely invisible and locked away from Tenant B.
    """
    # 1. Onboard Tenant A (Stark)
    tenant_a_payload = {"company_name": "Stark Corp", "subdomain": "stark"}
    res_t1 = client.post("/tenants/", json=tenant_a_payload)
    assert res_t1.status_code == 201

    # 2. Onboard Tenant B (Lannister)
    tenant_b_payload = {"company_name": "Lannister Corp", "subdomain": "lannister"}
    res_t2 = client.post("/tenants/", json=tenant_b_payload)
    assert res_t2.status_code == 201

    # 3. Add Customer to Tenant A (Passing Tenant A's subdomain header)
    customer_payload = {
        "first_name": "Jon",
        "last_name": "Snow",
        "email": "jon.snow@winterfell.com"
    }
    headers_tenant_a = {"X-Tenant-Subdomain": "stark"}
    res_cust_a = client.post("/customers/", json=customer_payload, headers=headers_tenant_a)
    assert res_cust_a.status_code == 201

    # 4. Attempt to fetch Tenant A's customer list as Tenant A (Should contain 1 customer)
    res_list_a = client.get("/customers/", headers=headers_tenant_a)
    assert res_list_a.status_code == 200
    assert len(res_list_a.json()) == 1
    assert res_list_a.json()[0]["email"] == "jon.snow@winterfell.com"

    # 5. SECURITY ATTACK VALIDATION: Fetch customer list as Tenant B (Lannister)
    # Even though Jon Snow exists inside the database cluster, Tenant B's folder must be empty.
    headers_tenant_b = {"X-Tenant-Subdomain": "lannister"}
    res_list_b = client.get("/customers/", headers=headers_tenant_b)
    
    assert res_list_b.status_code == 200
    assert len(res_list_b.json()) == 0  # CRITICAL SECURITY ASSERTION: Leak check passed!