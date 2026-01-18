"""
Integration Tests: Semantic Search
Feature: 003-semantic-search
Task: T004

Tests for semantic similarity search functionality.
Requires: Neo4j with vector index, Ollama with nomic-embed-text
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from api.services.embedding import EmbeddingService, EmbeddingError
from api.services.vector_search import (
    VectorSearchService,
    SearchFilters,
    SearchResult,
    SearchResponse,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_embedding():
    """Return a mock 768-dimensional embedding."""
    return [0.1] * 768


@pytest.fixture
def mock_search_results():
    """Sample search results."""
    return [
        {
            "id": "mem-001",
            "content": "Implemented token bucket algorithm for request throttling",
            "type": "procedural",
            "importance": 0.8,
            "session_id": "sess-abc",
            "project_id": "dionysus-core",
            "created_at": "2025-12-10T14:30:00Z",
            "tags": ["rate-limiting", "api"],
            "similarity": 0.92,
        },
        {
            "id": "mem-002",
            "content": "Rate limiting prevents API abuse and ensures fair usage",
            "type": "semantic",
            "importance": 0.7,
            "session_id": "sess-def",
            "project_id": "dionysus-core",
            "created_at": "2025-12-11T10:00:00Z",
            "tags": ["rate-limiting"],
            "similarity": 0.85,
        },
    ]


# =============================================================================
# EmbeddingService Tests
# =============================================================================

class TestEmbeddingService:
    """Tests for embedding generation service."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, mock_embedding):
        """Test successful embedding generation."""
        service = EmbeddingService()

        with patch.object(service, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [mock_embedding]}
            mock_response.raise_for_status = MagicMock()

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client.return_value = mock_http

            result = await service.generate_embedding("test query")

            assert len(result) == 768
            assert result == mock_embedding
            mock_http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text_raises(self):
        """Test that empty text raises error."""
        service = EmbeddingService()

        with pytest.raises(EmbeddingError, match="empty text"):
            await service.generate_embedding("")

        with pytest.raises(EmbeddingError, match="empty text"):
            await service.generate_embedding("   ")

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self):
        """Test handling of API errors."""
        service = EmbeddingService()

        with patch.object(service, '_get_client') as mock_client:
            import httpx
            mock_http = AsyncMock()
            mock_http.post.side_effect = httpx.RequestError("Connection failed")
            mock_client.return_value = mock_http

            with pytest.raises(EmbeddingError, match="connection error"):
                await service.generate_embedding("test")

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, mock_embedding):
        """Test batch embedding generation."""
        service = EmbeddingService()
        texts = ["query one", "query two", "query three"]

        with patch.object(service, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embeddings": [mock_embedding, mock_embedding, mock_embedding]
            }
            mock_response.raise_for_status = MagicMock()

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client.return_value = mock_http

            results = await service.generate_embeddings_batch(texts)

            assert len(results) == 3
            assert all(len(e) == 768 for e in results)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check returns status."""
        service = EmbeddingService()

        with patch.object(service, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [{"name": "nomic-embed-text:latest"}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_http = AsyncMock()
            mock_http.get.return_value = mock_response
            mock_client.return_value = mock_http

            health = await service.health_check()

            assert health["ollama_reachable"] is True
            assert health["model_available"] is True


# =============================================================================
# VectorSearchService Tests
# =============================================================================

class TestVectorSearchService:
    """Tests for vector similarity search service."""

    @pytest.mark.asyncio
    async def test_semantic_search_success(self, mock_search_results):
        """Test successful semantic search via MemEvolve adapter."""
        service = VectorSearchService()
        adapter = AsyncMock()
        adapter.recall_memories.return_value = {
            "memories": mock_search_results,
            "query": "rate limiting strategies",
            "result_count": 2,
        }

        with patch("api.services.vector_search.get_memevolve_adapter", return_value=adapter):
            response = await service.semantic_search(
                query="rate limiting strategies",
                top_k=10,
                threshold=0.7,
            )

        assert isinstance(response, SearchResponse)
        assert response.query == "rate limiting strategies"
        assert response.count == 2
        assert len(response.results) == 2
        assert response.results[0].similarity_score == 0.92
        assert response.search_time_ms > 0

        call = adapter.recall_memories.call_args[0][0]
        assert call.query == "rate limiting strategies"
        assert call.limit == 10

    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self, mock_search_results):
        """Test semantic search with project/session filters."""
        service = VectorSearchService()
        adapter = AsyncMock()
        adapter.recall_memories.return_value = {
            "memories": [mock_search_results[0]],
            "query": "rate limiting",
            "result_count": 1,
        }

        filters = SearchFilters(
            project_id="dionysus-core",
            session_id="sess-abc",
            from_date=datetime(2025, 12, 1),
            to_date=datetime(2025, 12, 15),
            memory_types=["procedural", "semantic"],
        )

        with patch("api.services.vector_search.get_memevolve_adapter", return_value=adapter):
            response = await service.semantic_search(
                query="rate limiting",
                top_k=5,
                threshold=0.8,
                filters=filters,
            )

        assert response.count == 1
        call = adapter.recall_memories.call_args[0][0]
        assert call.project_id == "dionysus-core"
        assert call.session_id == "sess-abc"
        assert call.memory_types == ["procedural", "semantic"]

    @pytest.mark.asyncio
    async def test_semantic_search_uses_strategy_when_missing_overrides(self):
        """Use latest RetrievalStrategy when top_k/threshold not provided."""
        service = VectorSearchService()
        adapter = AsyncMock()
        adapter.execute_cypher.return_value = [{"s": {"top_k": 5, "threshold": 0.6, "id": "strat"}}]
        adapter.recall_memories.return_value = {
            "memories": [],
            "query": "test",
            "result_count": 0,
        }

        with patch("api.services.vector_search.get_memevolve_adapter", return_value=adapter):
            response = await service.semantic_search(query="test")

        assert response.count == 0
        call = adapter.recall_memories.call_args[0][0]
        assert call.limit == 5

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check returns status via MemEvolve adapter."""
        service = VectorSearchService()
        adapter = AsyncMock()
        adapter.execute_cypher.return_value = [{"status": 1}]

        with patch("api.services.vector_search.get_memevolve_adapter", return_value=adapter):
            health = await service.health_check()

        assert health["healthy"] is True
        assert health["backend"] == "memevolve"


# =============================================================================
# SearchResult Tests
# =============================================================================

class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            id="mem-001",
            content="Test content",
            memory_type="semantic",
            importance=0.8,
            similarity_score=0.92,
            session_id="sess-abc",
            project_id="dionysus-core",
            created_at=datetime(2025, 12, 10, 14, 30),
            tags=["test", "example"],
        )

        assert result.id == "mem-001"
        assert result.similarity_score == 0.92
        assert result.importance == 0.8
        assert "test" in result.tags

    def test_search_result_optional_fields(self):
        """Test search result with minimal fields."""
        result = SearchResult(
            id="mem-001",
            content="Test",
            memory_type="semantic",
            importance=0.5,
            similarity_score=0.7,
        )

        assert result.session_id is None
        assert result.project_id is None
        assert result.created_at is None
        assert result.tags is None


# =============================================================================
# Integration Tests (require live services)
# =============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    True,  # Set to False when running with live services
    reason="Requires live Neo4j and Ollama services"
)
class TestSemanticSearchIntegration:
    """Integration tests requiring live services."""

    @pytest.mark.asyncio
    async def test_end_to_end_semantic_search(self):
        """Test complete semantic search flow with live services."""
        service = VectorSearchService()

        try:
            # Health check first
            health = await service.health_check()
            assert health["healthy"], f"Service unhealthy: {health}"

            # Execute search
            response = await service.semantic_search(
                query="How do we handle rate limiting?",
                top_k=5,
                threshold=0.5,
            )

            assert isinstance(response, SearchResponse)
            assert response.embedding_time_ms > 0
            assert response.search_time_ms > 0

        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_embedding_dimensions(self):
        """Verify embedding service returns correct dimensions."""
        service = EmbeddingService()

        try:
            embedding = await service.generate_embedding("test query")
            assert len(embedding) == 768

        finally:
            await service.close()
