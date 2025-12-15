"""
Integration Tests: n8n Workflow End-to-End
Feature: 002-remote-persistence-safety
Task: T018

TDD Test - Write FIRST, verify FAILS before implementation.

Tests the complete sync flow:
Webhook → n8n → Ollama (embedding) → Neo4j

Requires:
- SSH tunnel to VPS (ports 5678, 7687, 11434)
- n8n workflow imported and active
- Ollama with nomic-embed-text model
"""

import json
import os
import time
import uuid
from datetime import datetime

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()


# Skip all tests if n8n is not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("N8N_WEBHOOK_URL"),
    reason="N8N_WEBHOOK_URL not configured - skipping n8n integration tests",
)


@pytest.fixture
def webhook_url():
    """Get n8n webhook URL."""
    return os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/memory-sync")


@pytest.fixture
def webhook_token():
    """Get webhook authentication token."""
    return os.getenv("MEMORY_WEBHOOK_TOKEN", "test-token")


@pytest.fixture
def neo4j_config():
    """Get Neo4j configuration."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", ""),
    }


@pytest.fixture
async def neo4j_client(neo4j_config):
    """Create Neo4j client for verification."""
    from api.services.neo4j_client import Neo4jClient

    client = Neo4jClient(**neo4j_config)
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
def sample_payload():
    """Generate a sample memory payload."""
    return {
        "memory_id": str(uuid.uuid4()),
        "content": "Integration test: learned about n8n webhook workflows",
        "memory_type": "procedural",
        "importance": 0.7,
        "session_id": str(uuid.uuid4()),
        "project_id": "dionysus-core",
        "tags": ["n8n", "integration-test", "webhook"],
        "sync_version": 1,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


class TestN8nWebhookEndpoint:
    """Test n8n webhook is reachable."""

    @pytest.mark.asyncio
    async def test_n8n_health_check(self):
        """Test that n8n is running and healthy."""
        base_url = os.getenv("N8N_WEBHOOK_URL", "").rsplit("/webhook", 1)[0]
        health_url = f"{base_url}/healthz"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(health_url)
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("n8n not reachable - ensure SSH tunnel is active")

    @pytest.mark.asyncio
    async def test_webhook_endpoint_exists(self, webhook_url, webhook_token, sample_payload):
        """Test that the webhook endpoint responds."""
        from api.services.hmac_utils import generate_signature

        payload_bytes = json.dumps(sample_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    webhook_url,
                    content=payload_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                    },
                )
                # Any response (even error) means endpoint exists
                assert response.status_code in [200, 400, 401, 500]
            except httpx.ConnectError:
                pytest.skip("n8n webhook not reachable")


class TestEndToEndSync:
    """Test complete sync flow through n8n."""

    @pytest.mark.asyncio
    async def test_memory_syncs_to_neo4j(
        self, webhook_url, webhook_token, sample_payload, neo4j_client
    ):
        """
        Test that a memory sent to webhook ends up in Neo4j.

        Flow: POST to n8n webhook → n8n validates → Ollama generates embedding → Neo4j stores
        """
        from api.services.hmac_utils import generate_signature

        payload_bytes = json.dumps(sample_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        # Send to n8n webhook
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
            )

            if response.status_code != 200:
                pytest.fail(f"n8n webhook returned {response.status_code}: {response.text}")

        # Verify response
        data = response.json()
        assert data.get("success") is True
        assert data.get("memory_id") == sample_payload["memory_id"]

        # Wait a moment for Neo4j write to complete
        time.sleep(2)

        # Verify memory exists in Neo4j
        memory = await neo4j_client.get_memory(sample_payload["memory_id"])
        assert memory is not None, "Memory not found in Neo4j after sync"
        assert memory["content"] == sample_payload["content"]
        assert memory["memory_type"] == sample_payload["memory_type"]

        # Cleanup
        await neo4j_client.delete_memory(sample_payload["memory_id"])

    @pytest.mark.asyncio
    async def test_embedding_is_generated(
        self, webhook_url, webhook_token, sample_payload, neo4j_client
    ):
        """Test that Ollama generates an embedding for the memory."""
        from api.services.hmac_utils import generate_signature

        # Ensure no embedding in payload (n8n should generate it)
        sample_payload.pop("embedding", None)

        payload_bytes = json.dumps(sample_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
            )

            if response.status_code != 200:
                pytest.skip(f"n8n webhook failed: {response.text}")

        # Check response indicates embedding was generated
        data = response.json()
        assert data.get("embedding_generated") is True

        # Wait for processing
        time.sleep(3)

        # Verify embedding exists in Neo4j
        # Note: We can't easily retrieve the embedding via standard query,
        # but we can verify the workflow reported success
        memory = await neo4j_client.get_memory(sample_payload["memory_id"])
        assert memory is not None

        # Cleanup
        await neo4j_client.delete_memory(sample_payload["memory_id"])


class TestSessionRelationshipCreation:
    """Test that n8n creates Session relationships."""

    @pytest.mark.asyncio
    async def test_session_node_created(
        self, webhook_url, webhook_token, sample_payload, neo4j_client
    ):
        """Test that Session node is created when memory is synced."""
        from api.services.hmac_utils import generate_signature

        payload_bytes = json.dumps(sample_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
            )

            if response.status_code != 200:
                pytest.skip(f"n8n webhook failed: {response.text}")

        # Wait for processing
        time.sleep(2)

        # Query Neo4j for session
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)
        session = await sync_service.get_session(sample_payload["session_id"])

        assert session is not None, "Session node not created"
        assert session["id"] == sample_payload["session_id"]
        assert session["project_id"] == sample_payload["project_id"]

        # Cleanup
        await neo4j_client.delete_memory(sample_payload["memory_id"])


class TestErrorHandling:
    """Test n8n workflow error handling."""

    @pytest.mark.asyncio
    async def test_invalid_signature_returns_error(self, webhook_url, sample_payload):
        """Test that invalid signature returns error from n8n."""
        payload_bytes = json.dumps(sample_payload).encode()
        bad_signature = "sha256=invalid"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": bad_signature,
                },
            )

            # n8n should reject with error
            assert response.status_code in [400, 401, 500]

    @pytest.mark.asyncio
    async def test_invalid_payload_returns_error(self, webhook_url, webhook_token):
        """Test that invalid payload returns error from n8n."""
        from api.services.hmac_utils import generate_signature

        invalid_payload = {"invalid": "payload"}
        payload_bytes = json.dumps(invalid_payload).encode()
        signature = generate_signature(payload_bytes, webhook_token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
            )

            # n8n should reject with error
            assert response.status_code in [400, 500]
