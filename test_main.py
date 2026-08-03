import os
import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, engine
from sqlalchemy import text
import models

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def initialize_test_database_schemas():
    """
    SDET Global Engine Initializer:
    Runs once per test session. Dynamically reads local SQL schema files 
    and builds the base table hierarchies directly inside the container.
    """
    db = SessionLocal()
    try:
        # 1. Path routing to your database initialization scripts
        base_dir = os.path.dirname(os.path.abspath(__file__))
        public_sql_path = os.path.join(base_dir, "database", "01_public_schema.sql")
        tenant_sql_path = os.path.join(base_dir, "database", "02_tenant_schema.sql")

        # 2. Execute public registry scripts if they exist locally
        if os.path.exists(public_sql_path):
            with open(public_sql_path, "r") as f:
                db.execute(text(f.read()))
                db.commit()

        # 3. Execute template container scripts
        if os.path.exists(tenant_sql_path):
            with open(tenant_sql_path, "r") as f:
                db.execute(text(f.read()))
                db.commit()
    except Exception as e:
        print(f"[SDET ENGINE ERROR] Critical bootloader schema synchronization failed: {e}")
    finally:
        db.close()


@pytest.fixture(autouse=True)
def cleanup_database():
    """
    SDET Test Fixture: Automated lifecycle manager.
    Wipes master registries and destroys generated test schema folders from Docker.
    """
    yield  # Let the test run first
    
    db = SessionLocal()
    try:
        # 1. Wipe master registration records from the public directory table
        db.query(models.Tenant).filter(
            models.Tenant.subdomain.in_([
                "stark", "lannister", "watchnegative", "glovernegative", "tyrell", "martell", "starkiron"
            ])
        ).delete()
        db.commit()
        
        # 2. Break pooling retention state connections to avoid table drop locks
        db.invalidate()
        
        # 3. Drop isolated test schema folders from the PostgreSQL engine
        db.execute(text("DROP SCHEMA IF EXISTS tenant_stark CASCADE;"))
        db.execute(text("DROP SCHEMA IF EXISTS tenant_lannister CASCADE;"))
        db.execute(text("DROP SCHEMA IF EXISTS tenant_watchnegative CASCADE;"))
        db.execute(text("DROP SCHEMA IF EXISTS tenant_glovernegative CASCADE;"))
        db.execute(text("DROP SCHEMA IF EXISTS tenant_tyrell CASCADE;"))
        db.execute(text("DROP SCHEMA IF EXISTS tenant_martell CASCADE;"))
        db.execute(text("DROP SCHEMA IF EXISTS tenant_starkiron CASCADE;"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def test_cross_tenant_data_isolation():
    """
    SDET Multi-Tenant Verification: Proves that data inserted into Tenant A is entirely invisible and locked away from Tenant B.
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
    headers_tenant_b = {"X-Tenant-Subdomain": "lannister"}
    res_list_b = client.get("/customers/", headers=headers_tenant_b)
    assert res_list_b.status_code == 200
    assert len(res_list_b.json()) == 0


def test_customer_creation_rejects_malformed_email():
    """
    SDET Negative Test Case: Verifies that the validation schema intercepts and blocks a malformed email payload.
    """
    tenant_payload = {"company_name": "Night's Watch LLC", "subdomain": "watchnegative"}
    res_tenant = client.post("/tenants/", json=tenant_payload)
    assert res_tenant.status_code == 201

    malformed_payload = {
        "first_name": "Samwell",
        "last_name": "Tarly",
        "email": "sam.tarly@citadel"
    }
    headers = {"X-Tenant-Subdomain": "watchnegative"}
    response = client.post("/customers/", json=malformed_payload, headers=headers)
    assert response.status_code == 422
    
    error_details = response.json()["detail"][0]
    assert error_details["loc"] == ["body", "email"]


def test_customer_creation_rejects_excessive_name_length():
    """
    SDET Negative Test Case 3: Boundary Violation.
    Verifies that first_name values exceeding max_length=50 are caught by Pydantic.
    """
    tenant_payload = {"company_name": "Glover Logistics", "subdomain": "glovernegative"}
    res_tenant = client.post("/tenants/", json=tenant_payload)
    assert res_tenant.status_code == 201

    toxic_payload = {
        "first_name": "A" * 51,
        "last_name": "Mormont",
        "email": "johannah.m@mormont.com"
    }
    headers = {"X-Tenant-Subdomain": "glovernegative"}
    response = client.post("/customers/", json=toxic_payload, headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "first_name"]


def test_customer_creation_rejects_missing_isolation_header():
    """
    SDET Negative Test Case 4: Security Gate Missing Header.
    Verifies that requests to tenant-specific resources without an X-Tenant-Subdomain header are blocked by the middleware with a 400 Bad Request.
    """
    customer_payload = {
        "first_name": "Arya",
        "last_name": "Stark",
        "email": "noone@braavos.com"
    }
    response = client.post("/customers/", json=customer_payload)
    assert response.status_code == 400
    assert "Missing required isolation control header" in response.json()["detail"]


def test_customer_creation_rejects_nonexistent_tenant_header():
    """
    SDET Negative Test Case 5: Security Gate Unauthorized Tenant.
    Verifies that if an invalid or un-onboarded subdomain header is passed, the middleware halts execution immediately with a 403 Forbidden status.
    """
    customer_payload = {
        "first_name": "Tyrion",
        "last_name": "Lannister",
        "email": "halfman@casterly.com"
    }
    headers = {"X-Tenant-Subdomain": "white_walkers"}
    response = client.post("/customers/", json=customer_payload, headers=headers)
    assert response.status_code == 403
    assert "Access Denied: Invalid, inactive, or suspended tenant target" in response.json()["detail"]


def test_cross_tenant_duplicate_email_isolation():
    """
    SDET Negative Test Case 6: Cross-Tenant Data Contamination.
    Proves that creating a customer with an email address in Tenant A does not restrict or block a completely separate Tenant B from registering the same email address within their independent workspace.
    """
    client.post("/tenants/", json={"company_name": "Tyrell Orchards", "subdomain": "tyrell"})
    client.post("/tenants/", json={"company_name": "Martell Sun", "subdomain": "martell"})
    
    shared_payload = {
        "first_name": "Olenna",
        "last_name": "Redwyne",
        "email": "queen.of.thorns@highgarden.com"
    }
    
    res_a = client.post("/customers/", json=shared_payload, headers={"X-Tenant-Subdomain": "tyrell"})
    assert res_a.status_code == 201
    
    res_b = client.post("/customers/", json=shared_payload, headers={"X-Tenant-Subdomain": "martell"})
    assert res_b.status_code == 201


def test_invoice_sequential_sequencing_isolation():
    """
    SDET Integration Test Case 7: Invoice Sequential Number Generation.
    Verifies that when multiple invoices are generated within a tenant workspace, the engine dynamically queries historical count states to auto-increment the sequence number tracker cleanly (e.g., INV-STARK-0001 -> INV-STARK-0002).
    """
    tenant_payload = {"company_name": "Stark Ironworks LLC", "subdomain": "starkiron"}
    res_tenant = client.post("/tenants/", json=tenant_payload)
    assert res_tenant.status_code == 201

    customer_payload = {
        "first_name": "Tony",
        "last_name": "Stark",
        "email": "tony@starkindustries.com"
    }
    headers = {"X-Tenant-Subdomain": "starkiron"}
    res_cust = client.post("/customers/", json=customer_payload, headers=headers)
    assert res_cust.status_code == 201
    created_customer_id = res_cust.json()["id"]

    invoice_payload_1 = {
        "customer_id": created_customer_id,
        "amount": "1500.00",
        "due_date": "2026-09-15T00:00:00Z"
    }
    res_inv_1 = client.post("/invoices/", json=invoice_payload_1, headers=headers)
    assert res_inv_1.status_code == 201
    assert res_inv_1.json()["invoice_number"] == "INV-STARKIRON-0001"

    invoice_payload_2 = {
        "customer_id": created_customer_id,
        "amount": "250.50",
        "due_date": "2026-09-30T00:00:00Z"
    }
    res_inv_2 = client.post("/invoices/", json=invoice_payload_2, headers=headers)
    assert res_inv_2.status_code == 201
    assert res_inv_2.json()["invoice_number"] == "INV-STARKIRON-0002"
