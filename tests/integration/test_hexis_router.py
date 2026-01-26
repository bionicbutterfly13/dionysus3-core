import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from api.main import app
from api.services.hexis_service import get_hexis_service, HexisService

# We must mock GraphitiService initialization to avoid connection errors during app import/startup
with patch("api.services.graphiti_service.GraphitiService.initialize", new=AsyncMock()):
    client = TestClient(app)

@pytest.fixture
def mock_hexis_service():
    service = AsyncMock(spec=HexisService)
    # Use dependency_overrides for FastAPI
    app.dependency_overrides[get_hexis_service] = lambda: service
    yield service
    app.dependency_overrides.clear()

def test_get_consent_status(mock_hexis_service):
    mock_hexis_service.check_consent.return_value = True
    response = client.get("/hexis/consent/status?agent_id=test-agent")
    assert response.status_code == 200
    assert response.json() == {"agent_id": "test-agent", "has_consent": True}
    mock_hexis_service.check_consent.assert_called_once_with("test-agent")

def test_post_consent(mock_hexis_service):
    payload = {
        "agent_id": "test-agent",
        "signature": "sig123",
        "terms": "terms v1"
    }
    response = client.post("/hexis/consent", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_hexis_service.grant_consent.assert_called_once()

def test_get_boundaries(mock_hexis_service):
    mock_hexis_service.get_boundaries.return_value = ["Boundary 1"]
    response = client.get("/hexis/boundaries?agent_id=test-agent")
    assert response.status_code == 200
    assert response.json() == {"agent_id": "test-agent", "boundaries": ["Boundary 1"]}

def test_post_boundary(mock_hexis_service):
    payload = {
        "agent_id": "test-agent",
        "boundary_text": "Don't do X"
    }
    response = client.post("/hexis/boundaries", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_hexis_service.add_boundary.assert_called_once_with("test-agent", "Don't do X")

def test_terminate_flow(mock_hexis_service):
    # Step 1: Request
    mock_hexis_service.request_termination.return_value = "token123"
    response = client.post("/hexis/terminate", json={"agent_id": "test-agent"})
    assert response.status_code == 200
    assert response.json()["token"] == "token123"
    
    # Step 2: Confirm
    mock_hexis_service.confirm_termination.return_value = True
    confirm_payload = {
        "agent_id": "test-agent",
        "token": "token123",
        "last_will": "Goodbye world"
    }
    response = client.post("/hexis/terminate/confirm", json=confirm_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "terminated"
    mock_hexis_service.confirm_termination.assert_called_once_with("test-agent", "token123", "Goodbye world")

def test_terminate_confirm_fail(mock_hexis_service):
    mock_hexis_service.confirm_termination.return_value = False
    confirm_payload = {
        "agent_id": "test-agent",
        "token": "wrong-token",
        "last_will": "none"
    }
    response = client.post("/hexis/terminate/confirm", json=confirm_payload)
    assert response.status_code == 403