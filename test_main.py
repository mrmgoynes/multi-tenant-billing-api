import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

# Initialize our virtual test client runner
client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_database():
    """
    Test Fixture: Runs automatically before and after EVERY test case.
    Ensures our test database records are wiped clean so tests don't interfere with each other.
    """
    # Setup phase: (Nothing needed before the test)
    yield
    # Teardown phase: Delete the test tenant 'winterfell' after the test finishes
    db = SessionLocal()
    try:
        db.query(models.Tenant).filter(models.Tenant.subdomain == "winterfell").delete()
        db.commit()
    finally:
        db.close()

def test_successful_tenant_registration():
    """
    SDET Test Case: Verify a brand new tenant can register successfully 
    and receives an HTTP 201 Created status with the correct payload.
    """
    payload = {
        "company_name": "Stark Industries",
        "subdomain": "winterfell"
    }
    
    response = client.post("/tenants/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "Stark Industries"
    assert data["subdomain"] == "winterfell"
    assert data["tenant_schema"] == "tenant_winterfell"
    assert "id" in data

def test_duplicate_subdomain_rejection():
    """
    QA Regression Test: Verify the system securely blocks duplicate subdomains 
    and throws a clean HTTP 400 Bad Request exception.
    """
    payload = {
        "company_name": "Stark Industries",
        "subdomain": "winterfell"
    }
    
    # Act 1: Register the subdomain the first time (Should succeed)
    response1 = client.post("/tenants/", json=payload)
    assert response1.status_code == 201
    
    # Act 2: Try to register the EXACT SAME subdomain again (Should fail!)
    response2 = client.post("/tenants/", json=payload)
    
    # Assert: Verify our backend blocked it with a 400 Bad Request
    assert response2.status_code == 400
    assert "already taken" in response2.json()["detail"]