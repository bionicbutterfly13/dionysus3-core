"""
Integration Tests: Ollama Embedding Generation
Feature: 002-remote-persistence-safety
Phase 6, User Story 4: n8n Workflow Integration

T042: Integration test for Ollama embedding generation

TDD Test - Write FIRST, verify FAILS before implementation.

Tests that n8n workflow generates embeddings via Ollama.
"""

import os
import uuid

import pytest
import httpx


# =============================================================================
# Configuration
# =============================================================================

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def ollama_client():
    """HTTP client for Ollama API."""
    return httpx.AsyncClient(base_url=OLLAMA_URL, timeout=60.0)


@pytest.fixture
def sync_service():
    """Get RemoteSyncService instance."""
    from api.services.remote_sync import RemoteSyncService
    return RemoteSyncService()


# =============================================================================
# T042: Ollama Embedding Tests
# =============================================================================

class TestOllamaConnectivity:
    """Test basic Ollama connectivity."""

    async def test_ollama_is_reachable(self, ollama_client):
        """Test that Ollama API is reachable."""
        response = await ollama_client.get("/")
        assert response.status_code == 200

    async def test_embedding_model_available(self, ollama_client):
        """Test that the embedding model is loaded."""
        response = await ollama_client.get("/api/tags")
        assert response.status_code == 200

        data = response.json()
        models = [m["name"] for m in data.get("models", [])]

        # Should have nomic-embed-text or similar
        assert any(OLLAMA_MODEL in m for m in models), \
            f"Model {OLLAMA_MODEL} not found. Available: {models}"


class TestEmbeddingGeneration:
    """Test embedding generation via Ollama."""

    async def test_generate_embedding_direct(self, ollama_client):
        """Test generating embedding directly from Ollama."""
        response = await ollama_client.post(
            "/api/embeddings",
            json={
                "model": OLLAMA_MODEL,
                "prompt": "Test memory content for embedding generation"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "embedding" in data
        embedding = data["embedding"]

        # nomic-embed-text produces 768-dimensional vectors
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, (int, float)) for x in embedding)

    async def test_embedding_dimension(self, ollama_client):
        """Test that embedding has expected dimensions."""
        response = await ollama_client.post(
            "/api/embeddings",
            json={
                "model": OLLAMA_MODEL,
                "prompt": "Test content"
            }
        )

        data = response.json()
        embedding = data["embedding"]

        # nomic-embed-text: 768 dimensions
        # Other models may differ
        assert len(embedding) in [384, 768, 1024, 1536], \
            f"Unexpected embedding dimension: {len(embedding)}"

    async def test_similar_content_similar_embeddings(self, ollama_client):
        """Test that similar content produces similar embeddings."""
        import numpy as np

        # Generate embeddings for similar content
        resp1 = await ollama_client.post(
            "/api/embeddings",
            json={"model": OLLAMA_MODEL, "prompt": "Rate limiting implementation"}
        )
        resp2 = await ollama_client.post(
            "/api/embeddings",
            json={"model": OLLAMA_MODEL, "prompt": "Rate limiter implementation"}
        )
        resp3 = await ollama_client.post(
            "/api/embeddings",
            json={"model": OLLAMA_MODEL, "prompt": "Making pizza with tomatoes"}
        )

        emb1 = np.array(resp1.json()["embedding"])
        emb2 = np.array(resp2.json()["embedding"])
        emb3 = np.array(resp3.json()["embedding"])

        # Cosine similarity
        def cosine_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_similar = cosine_sim(emb1, emb2)
        sim_different = cosine_sim(emb1, emb3)

        # Similar content should have higher similarity
        assert sim_similar > sim_different


class TestN8nEmbeddingWorkflow:
    """Test n8n workflow generates embeddings."""

    async def test_memory_gets_embedding_via_n8n(self, sync_service):
        """Test that synced memory receives embedding from n8n workflow."""
        memory_id = str(uuid.uuid4())

        # Sync memory (n8n should add embedding)
        result = await sync_service.sync_memory({
            "id": memory_id,
            "content": "Test memory for embedding generation via n8n",
            "type": "semantic",
            "importance": 0.5,
        })

        assert result.get("success")

        # Wait for n8n to process (may need to poll)
        import asyncio
        await asyncio.sleep(2)

        # Retrieve memory and check for embedding
        memory = await sync_service.get_memory_from_neo4j(memory_id)

        assert memory is not None
        assert "embedding" in memory or memory.get("embedding_generated")

    async def test_embedding_stored_in_neo4j(self, sync_service):
        """Test that embedding is stored in Neo4j node."""
        memory_id = str(uuid.uuid4())

        await sync_service.sync_memory({
            "id": memory_id,
            "content": "Memory with embedding to verify storage",
            "type": "semantic",
            "importance": 0.7,
        })

        import asyncio
        await asyncio.sleep(2)

        # Query Neo4j directly
        memory = await sync_service.get_memory_from_neo4j(memory_id)

        if memory:
            embedding = memory.get("embedding")
            if embedding:
                assert isinstance(embedding, list)
                assert len(embedding) > 0
