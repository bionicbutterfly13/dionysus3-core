"""
Contract Tests: Webhook Sync API
Feature: 002-remote-persistence-safety
Task: T017

TDD Test - Write FIRST, verify FAILS before implementation.

Tests the POST /sync/memory webhook endpoint including:
- Payload validation against OpenAPI schema
- HMAC signature authentication
- Response schema validation
- Error handling
"""

import json
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from api.models.sync import MemorySyncPayload, SyncResponse
from api.services.hmac_utils import generate_signature


@pytest.fixture
def webhook_token():
    """Test webhook token."""
    return "test-webhook-token-for-testing"


@pytest.fixture
def app(webhook_token):
    """Create FastAPI test app with sync router."""
    from fastapi import FastAPI

    # Import will fail until T022 implements the router
    from api.routers.sync import router, set_webhook_token

    app = FastAPI()
    app.include_router(router, prefix="/api")
    set_webhook_token(webhook_token)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_payload():
    """Generate a valid sync payload."""
    return {
        "memory_id": str(uuid.uuid4()),
        "content": "Test memory content for webhook sync",
        "memory_type": "episodic",
        "importance": 0.8,
        "session_id": str(uuid.uuid4()),
        "project_id": "dionysus-core",
        "tags": ["test", "webhook"],
        "sync_version": 1,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


class TestPayloadValidation:
    """Test webhook payload validation."""

    def test_valid_payload_accepted(self, client, valid_payload, webhook_token):
        """Test that a valid payload is accepted."""
        payload_bytes = json.dumps(valid_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["memory_id"] == valid_payload["memory_id"]

    def test_missing_required_field_rejected(self, client, valid_payload, webhook_token):
        """Test that missing required fields are rejected."""
        # Remove required field
        del valid_payload["content"]

        payload_bytes = json.dumps(valid_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 400

    def test_invalid_memory_type_rejected(self, client, valid_payload, webhook_token):
        """Test that invalid memory_type is rejected."""
        valid_payload["memory_type"] = "invalid_type"

        payload_bytes = json.dumps(valid_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 400

    def test_importance_out_of_range_rejected(self, client, valid_payload, webhook_token):
        """Test that importance outside 0-1 range is rejected."""
        valid_payload["importance"] = 1.5

        payload_bytes = json.dumps(valid_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 400

    def test_invalid_sync_version_rejected(self, client, valid_payload, webhook_token):
        """Test that sync_version < 1 is rejected."""
        valid_payload["sync_version"] = 0

        payload_bytes = json.dumps(valid_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 400


class TestHMACAuthentication:
    """Test HMAC signature authentication."""

    def test_missing_signature_rejected(self, client, valid_payload):
        """Test that missing signature is rejected with 401."""
        payload_bytes = json.dumps(valid_payload).encode()

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 401
        assert "signature" in response.json().get("error", "").lower()

    def test_invalid_signature_rejected(self, client, valid_payload):
        """Test that invalid signature is rejected with 401."""
        payload_bytes = json.dumps(valid_payload).encode()
        bad_signature = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": bad_signature,
            },
        )

        assert response.status_code == 401

    def test_tampered_payload_rejected(self, client, valid_payload, webhook_token):
        """Test that tampered payload is rejected."""
        # Generate signature for original payload
        original_bytes = json.dumps(valid_payload).encode()
        signature = generate_signature(original_bytes, webhook_token)

        # Tamper with payload
        valid_payload["importance"] = 0.99
        tampered_bytes = json.dumps(valid_payload).encode()

        response = client.post(
            "/api/sync/memory",
            content=tampered_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 401


class TestResponseSchema:
    """Test response schema matches contract."""

    def test_success_response_schema(self, client, valid_payload, webhook_token):
        """Test that success response matches SyncResponse schema."""
        payload_bytes = json.dumps(valid_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Validate against SyncResponse schema
        assert "success" in data
        assert "memory_id" in data
        assert "synced_at" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["memory_id"], str)

    def test_error_response_schema(self, client, valid_payload):
        """Test that error response has correct schema."""
        payload_bytes = json.dumps(valid_payload).encode()

        response = client.post(
            "/api/sync/memory",
            content=payload_bytes,
            headers={"Content-Type": "application/json"},
        )

        data = response.json()
        assert "error" in data or "detail" in data


class TestSyncTriggerEndpoint:
    """Test POST /sync/trigger endpoint."""

    def test_trigger_endpoint_exists(self, client):
        """Test that trigger endpoint responds."""
        # This will fail until T023 implements the endpoint
        response = client.post(
            "/api/sync/trigger",
            headers={"Authorization": "Bearer test-token"},
        )

        # Should not be 404
        assert response.status_code != 404

    def test_trigger_returns_queue_info(self, client):
        """Test that trigger returns queue information."""
        response = client.post(
            "/api/sync/trigger",
            headers={"Authorization": "Bearer test-token"},
        )

        if response.status_code == 202:
            data = response.json()
            assert "triggered" in data
            assert "queue_size" in data


class TestSyncStatusEndpoint:
    """Test GET /sync/status endpoint."""

    def test_status_endpoint_exists(self, client):
        """Test that status endpoint responds."""
        # This will fail until T024 implements the endpoint
        response = client.get("/api/sync/status")

        # Should not be 404
        assert response.status_code != 404

    def test_status_returns_health_info(self, client):
        """Test that status returns health information."""
        response = client.get("/api/sync/status")

        if response.status_code == 200:
            data = response.json()
            assert "healthy" in data
            assert "queue_size" in data
            assert "pending_count" in data


class TestRecoveryEndpoint:
    """Test POST /recovery/bootstrap endpoint."""

    def test_recovery_endpoint_exists(self, client):
        """Test that recovery endpoint responds."""
        # This will fail until T026 implements the endpoint
        response = client.post(
            "/api/recovery/bootstrap",
            headers={"Authorization": "Bearer test-token"},
            json={"dry_run": True},
        )

        # Should not be 404
        assert response.status_code != 404

    def test_recovery_dry_run(self, client):
        """Test recovery in dry_run mode."""
        response = client.post(
            "/api/recovery/bootstrap",
            headers={"Authorization": "Bearer test-token"},
            json={"dry_run": True},
        )

        if response.status_code == 200:
            data = response.json()
            assert data.get("dry_run") is True
            assert "recovered_count" in data
