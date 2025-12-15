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
            "memory_type": "procedural",
            "importance": 0.8,
            "session_id": "sess-abc",
            "project_id": "dionysus-core",
            "created_at": "2025-12-10T14:30:00Z",
            "tags": ["rate-limiting", "api"],
            "score": 0.92,
        },
        {
            "id": "mem-002",
            "content": "Rate limiting prevents API abuse and ensures fair usage",
            "memory_type": "semantic",
            "importance": 0.7,
            "session_id": "sess-def",
            "project_id": "dionysus-core",
            "created_at": "2025-12-11T10:00:00Z",
            "tags": ["rate-limiting"],
            "score": 0.85,
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
            mock_response = AsyncMock()
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
            mock_response = AsyncMock()
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
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [{"name": "nomic-embed-text:latest"}]
            }

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
    async def test_semantic_search_success(self, mock_embedding, mock_search_results):
        """Test successful semantic search."""
        mock_embed_service = AsyncMock(spec=EmbeddingService)
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = mock_search_results

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

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
            assert response.embedding_time_ms > 0
            assert response.search_time_ms > 0

    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self, mock_embedding, mock_search_results):
        """Test semantic search with project/session filters."""
        mock_embed_service = AsyncMock(spec=EmbeddingService)
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        filters = SearchFilters(
            project_id="dionysus-core",
            session_id="sess-abc",
            from_date=datetime(2025, 12, 1),
            to_date=datetime(2025, 12, 15),
            memory_types=["procedural", "semantic"],
        )

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = [mock_search_results[0]]

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            response = await service.semantic_search(
                query="rate limiting",
                top_k=5,
                threshold=0.8,
                filters=filters,
            )

            assert response.count == 1
            # Verify the cypher query included filter parameters
            call_args = mock_session.run.call_args
            query = call_args[0][0]
            params = call_args[0][1]

            assert "project_id" in params
            assert params["project_id"] == "dionysus-core"
            assert "session_id" in params
            assert "from_date" in params
            assert "memory_types" in params

    @pytest.mark.asyncio
    async def test_semantic_search_no_results(self, mock_embedding):
        """Test semantic search with no matching results."""
        mock_embed_service = AsyncMock(spec=EmbeddingService)
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = []

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            response = await service.semantic_search(
                query="completely unrelated topic xyz123",
                top_k=10,
                threshold=0.9,
            )

            assert response.count == 0
            assert response.results == []

    @pytest.mark.asyncio
    async def test_search_results_ordered_by_score(self, mock_embedding):
        """Test that results are ordered by similarity score descending."""
        mock_embed_service = AsyncMock(spec=EmbeddingService)
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        # Results in descending score order (as they should come from Neo4j)
        results = [
            {"id": "1", "content": "a", "memory_type": "semantic", "importance": 0.5,
             "session_id": None, "project_id": None, "created_at": None, "tags": None, "score": 0.95},
            {"id": "2", "content": "b", "memory_type": "semantic", "importance": 0.5,
             "session_id": None, "project_id": None, "created_at": None, "tags": None, "score": 0.85},
            {"id": "3", "content": "c", "memory_type": "semantic", "importance": 0.5,
             "session_id": None, "project_id": None, "created_at": None, "tags": None, "score": 0.75},
        ]

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = results

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            response = await service.semantic_search("test", top_k=10)

            scores = [r.similarity_score for r in response.results]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_find_similar_memories(self, mock_embedding):
        """Test finding memories similar to an existing memory."""
        mock_embed_service = AsyncMock(spec=EmbeddingService)
        service = VectorSearchService(embedding_service=mock_embed_service)

        similar_results = [
            {"id": "mem-002", "content": "similar content", "memory_type": "semantic",
             "importance": 0.6, "session_id": None, "project_id": None,
             "created_at": None, "tags": None, "score": 0.88},
        ]

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()

            # First call returns source embedding
            mock_result1 = AsyncMock()
            mock_record = {"embedding": mock_embedding}
            mock_result1.single.return_value = mock_record

            # Second call returns similar memories
            mock_result2 = AsyncMock()
            mock_result2.data.return_value = similar_results

            mock_session.run.side_effect = [mock_result1, mock_result2]
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            results = await service.find_similar_memories(
                memory_id="mem-001",
                top_k=5,
                threshold=0.7,
                exclude_self=True,
            )

            assert len(results) == 1
            assert results[0].id == "mem-002"
            assert results[0].similarity_score == 0.88

    @pytest.mark.asyncio
    async def test_health_check(self, mock_embedding):
        """Test health check returns comprehensive status."""
        mock_embed_service = AsyncMock(spec=EmbeddingService)
        mock_embed_service.health_check.return_value = {
            "healthy": True,
            "model_available": True,
        }

        service = VectorSearchService(embedding_service=mock_embed_service)

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()

            # Neo4j connection check
            mock_result1 = AsyncMock()
            mock_result1.single.return_value = {"n": 1}

            # Vector index check
            mock_result2 = AsyncMock()
            mock_result2.data.return_value = [{"name": "memory_embedding_index"}]

            mock_session.run.side_effect = [mock_result1, mock_result2]
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            health = await service.health_check()

            assert health["healthy"] is True
            assert health["neo4j_connected"] is True
            assert health["vector_index_exists"] is True


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
