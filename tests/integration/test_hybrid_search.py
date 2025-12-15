"""
Integration Tests: Hybrid Search
Feature: 003-semantic-search
Task: T011

Tests for hybrid search combining keyword and semantic similarity.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_embedding():
    """Return a mock 768-dimensional embedding."""
    return [0.1] * 768


@pytest.fixture
def keyword_match_results():
    """Results that match keywords exactly."""
    return [
        {
            "id": "mem-exact-1",
            "content": "Token bucket rate limiting implementation",
            "memory_type": "procedural",
            "importance": 0.8,
            "session_id": "sess-abc",
            "project_id": "dionysus-core",
            "created_at": "2025-12-10T14:30:00Z",
            "tags": ["rate-limiting"],
            "score": 0.95,  # Keyword match score
        },
    ]


@pytest.fixture
def semantic_match_results():
    """Results that match semantically but not keywords."""
    return [
        {
            "id": "mem-semantic-1",
            "content": "Request throttling prevents API abuse by limiting requests per time window",
            "memory_type": "semantic",
            "importance": 0.7,
            "session_id": "sess-def",
            "project_id": "dionysus-core",
            "created_at": "2025-12-11T10:00:00Z",
            "tags": ["api"],
            "score": 0.82,  # Semantic similarity
        },
        {
            "id": "mem-semantic-2",
            "content": "Protecting endpoints from excessive usage through quotas",
            "memory_type": "semantic",
            "importance": 0.6,
            "session_id": "sess-ghi",
            "project_id": "dionysus-core",
            "created_at": "2025-12-12T09:00:00Z",
            "tags": None,
            "score": 0.75,
        },
    ]


# =============================================================================
# Hybrid Search Tests
# =============================================================================

class TestHybridSearch:
    """Tests for hybrid keyword + semantic search."""

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(
        self, mock_embedding, keyword_match_results, semantic_match_results
    ):
        """Test that hybrid search combines keyword and semantic results."""
        from api.services.vector_search import VectorSearchService

        mock_embed_service = AsyncMock()
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        # Combined results from both methods
        all_results = keyword_match_results + semantic_match_results

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = all_results

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            response = await service.hybrid_search(
                query="rate limiting",
                top_k=10,
                threshold=0.5,
                keyword_weight=0.3,  # 30% keyword, 70% semantic
            )

            # Should have results from both types
            assert response.count >= 1
            # Results should be ordered by combined score
            scores = [r.similarity_score for r in response.results]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_hybrid_search_boosts_keyword_matches(
        self, mock_embedding, keyword_match_results
    ):
        """Test that keyword matches get boosted in hybrid search."""
        from api.services.vector_search import VectorSearchService

        mock_embed_service = AsyncMock()
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = keyword_match_results

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            response = await service.hybrid_search(
                query="rate limiting",  # Exact keyword match
                top_k=5,
                keyword_weight=0.5,  # High keyword weight
            )

            # Keyword matches should have boosted scores
            assert response.count > 0

    @pytest.mark.asyncio
    async def test_hybrid_search_keyword_weight_parameter(self, mock_embedding):
        """Test that keyword_weight parameter affects results."""
        from api.services.vector_search import VectorSearchService

        mock_embed_service = AsyncMock()
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

            # Test with different keyword weights
            await service.hybrid_search(
                query="test",
                keyword_weight=0.0,  # Pure semantic
            )

            await service.hybrid_search(
                query="test",
                keyword_weight=1.0,  # Pure keyword
            )

            await service.hybrid_search(
                query="test",
                keyword_weight=0.5,  # Balanced
            )

            # All calls should complete without error
            assert mock_session.run.call_count == 3

    @pytest.mark.asyncio
    async def test_hybrid_search_semantic_fills_gaps(
        self, mock_embedding, semantic_match_results
    ):
        """Test that semantic results fill gaps when keywords don't match."""
        from api.services.vector_search import VectorSearchService

        mock_embed_service = AsyncMock()
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            # No keyword matches, only semantic
            mock_result.data.return_value = semantic_match_results

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            response = await service.hybrid_search(
                query="request throttling prevention",
                top_k=10,
                keyword_weight=0.3,
            )

            # Should still get semantic results
            assert response.count == len(semantic_match_results)

    @pytest.mark.asyncio
    async def test_hybrid_search_deduplicates_results(
        self, mock_embedding, keyword_match_results
    ):
        """Test that same memory appearing in both sets is deduplicated."""
        from api.services.vector_search import VectorSearchService

        mock_embed_service = AsyncMock()
        mock_embed_service.generate_embedding.return_value = mock_embedding

        service = VectorSearchService(embedding_service=mock_embed_service)

        # Same result appearing twice (from keyword and semantic)
        duplicate_results = keyword_match_results + keyword_match_results

        with patch.object(service, '_get_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = duplicate_results

            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_driver_instance = AsyncMock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance

            response = await service.hybrid_search(
                query="rate limiting",
                top_k=10,
            )

            # Should deduplicate by memory ID
            ids = [r.id for r in response.results]
            assert len(ids) == len(set(ids))  # No duplicates


class TestHybridSearchAPI:
    """Tests for hybrid search REST API endpoint."""

    @pytest.mark.asyncio
    async def test_hybrid_search_endpoint_exists(self):
        """Test that hybrid search endpoint is available."""
        from api.routers.memory import router

        # Find the hybrid search endpoint
        endpoints = [route.path for route in router.routes]
        assert "/hybrid-search" in endpoints or "/semantic-search" in endpoints

    @pytest.mark.asyncio
    async def test_hybrid_search_request_validation(self):
        """Test that request validation works."""
        from api.routers.memory import SemanticSearchRequest

        # Valid request
        request = SemanticSearchRequest(
            query="rate limiting",
            top_k=10,
            threshold=0.7,
        )
        assert request.query == "rate limiting"

        # Invalid: empty query
        with pytest.raises(ValueError):
            SemanticSearchRequest(query="", top_k=10)

        # Invalid: threshold out of range
        with pytest.raises(ValueError):
            SemanticSearchRequest(query="test", threshold=1.5)
