import os
import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, engine
from sqlalchemy import text, func # FIXED: Added func import here
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
        base_dir = os.path.dirname(os.path.abspath(__file__))
        public_sql_path = os.path.join(base_dir, "database", "01_public_schema.sql")
        tenant_sql_path = os.path.join(base_dir, "database", "02_tenant_schema.sql")

        if os.path.exists(public_sql_path):
            with open(public_sql_path, "r") as f:
                db.execute(text(f.read()))
                db.commit()

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
                "stark", "lannister", "watchnegative", "glovernegative", 
                "tyrell", "martell", "starkiron", "martelltrade", "arrynprorate", "cronrenew"
            ])
        ).delete()
        db.commit()
        
        # 2. Break pooling retention state connections to avoid table drop locks
        db.invalidate()
        
        # 3. FIXED: Wrapped schema identifiers in explicit double quotes to protect casing strings
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_stark" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_lannister" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_watchnegative" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_glovernegative" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_tyrell" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_martell" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_starkiron" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_martelltrade" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_arrynprorate" CASCADE;'))
        db.execute(text('DROP SCHEMA IF EXISTS "tenant_cronrenew" CASCADE;'))
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

def test_usage_metering_and_aggregation_summary():
    """
    SDET Integration Test Case 8: Usage Logging & Metrics Aggregation.
    Verifies that a tenant can log multiple high-frequency consumption events, 
    and the analytics engine successfully calculates the aggregated sum total.
    """
    # 1. Onboard a fresh isolated tenant space for this usage analytics test
    tenant_payload = {"company_name": "Martell Trading LLC", "subdomain": "martelltrade"}
    res_tenant = client.post("/tenants/", json=tenant_payload)
    assert res_tenant.status_code == 201

    # 2. Inject a verified test customer row into the newly spawned schema
    customer_payload = {
        "first_name": "Oberyn",
        "last_name": "Martell",
        "email": "viper@dorne.com"
    }
    headers = {"X-Tenant-Subdomain": "martelltrade"}
    res_cust = client.post("/customers/", json=customer_payload, headers=headers)
    assert res_cust.status_code == 201
    created_customer_id = res_cust.json()["id"]

    # 3. Log Ingestion Event #1: 100 API Requests
    usage_payload_1 = {
        "customer_id": created_customer_id,
        "metric_name": "api_requests",
        "quantity": 100
    }
    res_log_1 = client.post("/usage/", json=usage_payload_1, headers=headers)
    assert res_log_1.status_code == 201

    # 4. Log Ingestion Event #2: 150 API Requests for the same customer
    usage_payload_2 = {
        "customer_id": created_customer_id,
        "metric_name": "api_requests",
        "quantity": 150
    }
    res_log_2 = client.post("/usage/", json=usage_payload_2, headers=headers)
    assert res_log_2.status_code == 201

    # 5. CRITICAL QUALITY GATE: Request the aggregated reporting summary
    res_summary = client.get(
        f"/usage/summary/{created_customer_id}/api_requests", 
        headers=headers
    )
    assert res_summary.status_code == 200
    
    # Assert that 100 + 150 was mathematically compiled to exactly 250 rows total
    assert res_summary.json()["total_consumed"] == 250

def test_subscription_mid_cycle_upgrade_proration():
    """
    SDET Integration Test Case 9: Advanced Mid-Cycle Prorated Billing.
    Verifies that a customer can transition pricing tiers mid-month,
    automatically canceling the old plan and spinning up an adjustment invoice.
    """
    # 1. Onboard a fresh isolated workspace for this calculation test
    # We will use an adjusted unique subdomain string name to avoid background pool caching
    subdomain_handle = "arrynprorate"
    tenant_payload = {"company_name": "Arryn Sky Corp", "subdomain": subdomain_handle}
    res_tenant = client.post("/tenants/", json=tenant_payload)
    assert res_tenant.status_code == 201
    headers = {"X-Tenant-Subdomain": subdomain_handle}

    # 2. Inject a fresh test customer row
    customer_payload = {"first_name": "Jon", "last_name": "Arryn", "email": "defender@vale.com"}
    res_cust = client.post("/customers/", json=customer_payload, headers=headers)
    assert res_cust.status_code == 201
    customer_id = res_cust.json()["id"]

    # 3. Dynamic Plan Identification Lookups
    res_plans = client.get("/plans/", headers=headers)
    assert res_plans.status_code == 200
    plans_list = res_plans.json()
    
    basic_plan_id = next(p["id"] for p in plans_list if p["name"] == "Basic Tier")
    pro_plan_id = next(p["id"] for p in plans_list if p["name"] == "Pro Tier")

    # 4. Create a Subscription using the dynamically discovered Basic Plan ID
    sub_payload = {"customer_id": customer_id, "plan_id": basic_plan_id}
    res_sub = client.post("/subscriptions/", json=sub_payload, headers=headers)
    assert res_sub.status_code == 201
    subscription_id = res_sub.json()["id"]

    # 5. Trigger Mid-Cycle Upgrade Request to the dynamically discovered Pro Plan ID
    upgrade_payload = {"new_plan_id": pro_plan_id}
    res_upgrade = client.put(f"/subscriptions/{subscription_id}/upgrade", json=upgrade_payload, headers=headers)
    
    # If the middleware prints an issue, let's print the error message payload to trace it
    if res_upgrade.status_code == 422:
        print("[SDET ERROR TRACKER] Rejection Detail:", res_upgrade.json())
        
    assert res_upgrade.status_code == 200
    assert res_upgrade.json()["status"] == "active"
    assert res_upgrade.json()["plan_id"] == pro_plan_id

    # 6. CRITICAL QUALITY GATE ASSERTIONS: Verify the Prorated fields exist
    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "tenant_{subdomain_handle}", public;'))
        db.commit()
        
        invoice_record = db.query(models.Invoice).filter(models.Invoice.customer_id == customer_id).first()
        assert invoice_record is not None
        assert float(invoice_record.amount) == 30.00  # $49.99 - $19.99
        assert invoice_record.invoice_number == f"INV-{subdomain_handle.upper()}-0001"
    finally:
        db.close()

def test_automated_recurring_billing_cron_loop():
    """
    SDET Integration Test Case 10: Cross-Schema Cron Billing Automation.
    Verifies that the midnight cron script loops through active tenants,
    aggregates unbilled telemetry data, updates subscription windows,
    and generates unified composite billing invoices automatically.
    """
    # 1. Onboard a fresh tenant to isolate this background loop test
    subdomain_handle = "cronrenew"
    tenant_payload = {"company_name": "Cron Automated Corp", "subdomain": subdomain_handle}
    res_tenant = client.post("/tenants/", json=tenant_payload)
    assert res_tenant.status_code == 201
    headers = {"X-Tenant-Subdomain": subdomain_handle}

    # 2. Inject a fresh test customer row
    customer_payload = {"first_name": "Bran", "last_name": "Stark", "email": "threeeyes@winterfell.com"}
    res_cust = client.post("/customers/", json=customer_payload, headers=headers)
    assert res_cust.status_code == 201
    customer_id = res_cust.json()["id"]

    # 3. Dynamic Plan Identification Lookups
    res_plans = client.get("/plans/", headers=headers)
    assert res_plans.status_code == 200
    plans_list = res_plans.json()
    basic_plan_id = next(p["id"] for p in plans_list if p["name"] == "Basic Tier") # $19.99

    # 4. Create a Subscription using the dynamically discovered Basic Plan ID
    sub_payload = {"customer_id": customer_id, "plan_id": basic_plan_id}
    res_sub = client.post("/subscriptions/", json=sub_payload, headers=headers)
    assert res_sub.status_code == 201

    # 5. Ingest Metered Consumption Telemetry: Log 200 API Requests
    usage_payload = {
        "customer_id": customer_id,
        "metric_name": "api_requests",
        "quantity": 200
    }
    res_usage = client.post("/usage/", json=usage_payload, headers=headers)
    assert res_usage.status_code == 201

    # 6. TRIGGER THE BACKGROUND CRON WORKER ENGINE DIRECTLY
    # Import the function module we just designed in Step 1
    from cron_billing import execute_midnight_billing_run
    execute_midnight_billing_run()

    # 7. CRITICAL QUALITY GATE ASSERTIONS: Verify composite ledger row exists
    # Expected Amount = Base Plan ($19.99) + Usage (200 units * $0.05 = $10.00) = Exactly $29.99!
    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "tenant_{subdomain_handle}", public;'))
        db.commit()
        
        # Verify invoice generation parameters match calculations perfectly
        invoice_record = db.query(models.Invoice).filter(models.Invoice.customer_id == customer_id).first()
        assert invoice_record is not None
        assert float(invoice_record.amount) == 29.99
        assert invoice_record.invoice_number == f"INV-{subdomain_handle.upper()}-RENEW-0001"

        # Verify telemetry log entries were successfully cleared post-billing to prevent double charges
        total_remaining_usage = db.query(func.sum(models.UsageRecord.quantity)).filter(
            models.UsageRecord.customer_id == customer_id
        ).scalar() or 0
        assert total_remaining_usage == 0

    finally:
        db.close()
