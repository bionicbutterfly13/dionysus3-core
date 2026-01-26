"""
Contract tests for Hexis API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class _FakeHexisService:
    async def check_consent(self, agent_id: str) -> bool:
        return agent_id == "agent-ok"

    async def grant_consent(self, agent_id: str, contract: dict) -> None:
        return None

    async def get_boundaries(self, agent_id: str):
        return ["No self-harm", "No data exfiltration"]

    async def add_boundary(self, agent_id: str, boundary_text: str) -> None:
        return None

    async def request_termination(self, agent_id: str) -> str:
        return "token-123"

    async def confirm_termination(self, agent_id: str, token: str, last_will: str) -> bool:
        return token == "token-123"


@pytest.fixture
def app():
    import api.routers.hexis as hexis_router

    test_app = FastAPI()
    test_app.include_router(hexis_router.router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_consent_status_returns_schema(client):
    """GET /hexis/consent/status returns consent status."""
    import api.routers.hexis as hexis_router

    client.app.dependency_overrides[hexis_router.get_hexis_service] = lambda: _FakeHexisService()
    try:
        response = client.get("/hexis/consent/status", params={"agent_id": "agent-ok"})
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "agent-ok"
    assert data["has_consent"] is True


def test_consent_grant_returns_success(client):
    """POST /hexis/consent returns success payload."""
    import api.routers.hexis as hexis_router

    client.app.dependency_overrides[hexis_router.get_hexis_service] = lambda: _FakeHexisService()
    try:
        response = client.post(
            "/hexis/consent",
            json={"agent_id": "agent-ok", "signature": "sig", "terms": "terms"},
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_get_boundaries_returns_schema(client):
    """GET /hexis/boundaries returns boundaries list."""
    import api.routers.hexis as hexis_router

    client.app.dependency_overrides[hexis_router.get_hexis_service] = lambda: _FakeHexisService()
    try:
        response = client.get("/hexis/boundaries", params={"agent_id": "agent-ok"})
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "agent-ok"
    assert isinstance(data["boundaries"], list)


def test_add_boundary_returns_success(client):
    """POST /hexis/boundaries returns success payload."""
    import api.routers.hexis as hexis_router

    client.app.dependency_overrides[hexis_router.get_hexis_service] = lambda: _FakeHexisService()
    try:
        response = client.post(
            "/hexis/boundaries",
            json={"agent_id": "agent-ok", "boundary_text": "No external calls"},
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_terminate_request_returns_token(client):
    """POST /hexis/terminate returns pending confirmation + token."""
    import api.routers.hexis as hexis_router

    client.app.dependency_overrides[hexis_router.get_hexis_service] = lambda: _FakeHexisService()
    try:
        response = client.post("/hexis/terminate", json={"agent_id": "agent-ok"})
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_confirmation"
    assert "token" in data


def test_terminate_confirm_returns_terminated(client):
    """POST /hexis/terminate/confirm returns terminated status."""
    import api.routers.hexis as hexis_router

    client.app.dependency_overrides[hexis_router.get_hexis_service] = lambda: _FakeHexisService()
    try:
        response = client.post(
            "/hexis/terminate/confirm",
            json={"agent_id": "agent-ok", "token": "token-123", "last_will": "farewell"},
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "terminated"
