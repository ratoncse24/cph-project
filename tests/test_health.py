from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """
    Test the health check endpoint.
    """
    response = client.get("/projects/api/v1/health")
    assert response.status_code == 200