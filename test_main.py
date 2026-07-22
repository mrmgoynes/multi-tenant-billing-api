from fastapi.testclient import TestClient
from main import app

# Initialize the automated test client runner
client = TestClient(app)

def test_read_root_endpoint():
    """
    QA Test Case: Verify the core root endpoint returns an HTTP 200 status 
    and the expected JSON system configuration payload.
    """
    # Act: Programmatically send a GET request to the root URL
    response = client.get("/")
    
    # Assert: Verify the server responded with a perfect 200 OK status
    assert response.status_code == 200
    
    # Assert: Validate the exact key-value structural data matches expectations
    data = response.json()
    assert data["status"] == "online"
    assert "Multi-Tenant" in data["message"]