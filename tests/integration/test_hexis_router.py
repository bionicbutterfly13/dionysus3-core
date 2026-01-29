import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import api.routers.hexis as hexis_router
from api.services.hexis_service import get_hexis_service, HexisService

@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(hexis_router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def mock_hexis_service(app):
    service = AsyncMock(spec=HexisService)
    # Use dependency_overrides for FastAPI
    app.dependency_overrides[get_hexis_service] = lambda: service
    yield service
    app.dependency_overrides.clear()

def test_get_consent_status(client, mock_hexis_service):
    mock_hexis_service.check_consent.return_value = True
    response = client.get("/hexis/consent/status?agent_id=test-agent")
    assert response.status_code == 200
    assert response.json() == {"agent_id": "test-agent", "has_consent": True}
    mock_hexis_service.check_consent.assert_called_once_with("test-agent")

def test_post_consent(client, mock_hexis_service):
    payload = {
        "agent_id": "test-agent",
        "signature": "sig123",
        "terms": "terms v1"
    }
    response = client.post("/hexis/consent", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_hexis_service.grant_consent.assert_called_once()

def test_get_boundaries(client, mock_hexis_service):
    mock_hexis_service.get_boundaries.return_value = ["Boundary 1"]
    response = client.get("/hexis/boundaries?agent_id=test-agent")
    assert response.status_code == 200
    assert response.json() == {"agent_id": "test-agent", "boundaries": ["Boundary 1"]}

def test_post_boundary(client, mock_hexis_service):
    payload = {
        "agent_id": "test-agent",
        "boundary_text": "Don't do X"
    }
    response = client.post("/hexis/boundaries", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_hexis_service.add_boundary.assert_called_once_with("test-agent", "Don't do X")

def test_terminate_request_removed_returns_404(client):
    response = client.post("/hexis/terminate", json={"agent_id": "test-agent"})
    assert response.status_code == 404


def test_terminate_confirm_removed_returns_404(client):
    confirm_payload = {
        "agent_id": "test-agent",
        "token": "token123",
        "last_will": "Goodbye world"
    }
    response = client.post("/hexis/terminate/confirm", json=confirm_payload)
    assert response.status_code == 404
