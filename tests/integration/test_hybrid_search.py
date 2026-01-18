"""
Integration Tests: MemEvolve Vector Search Mapping
Feature: 003-semantic-search

Validates that VectorSearchService maps MemEvolve recall payloads correctly.
"""

import pytest
from unittest.mock import AsyncMock, patch

from api.services.vector_search import VectorSearchService


@pytest.mark.asyncio
async def test_semantic_search_defaults_missing_fields():
    """Missing similarity/type should fall back to defaults."""
    adapter = AsyncMock()
    adapter.recall_memories.return_value = {
        "memories": [
            {"id": "mem-1", "content": "alpha"},
            {"id": "mem-2", "content": "beta", "similarity": 0.4},
        ],
        "query": "test",
        "result_count": 2,
    }

    service = VectorSearchService()
    with patch("api.services.vector_search.get_memevolve_adapter", return_value=adapter):
        response = await service.semantic_search(query="test", top_k=5, threshold=0.7)

    assert response.count == 2
    assert response.results[0].similarity_score == 0.0
    assert response.results[0].memory_type == "semantic"
    assert response.results[1].similarity_score == 0.4


@pytest.mark.asyncio
async def test_semantic_search_handles_adapter_error():
    """Adapter errors should yield empty results."""
    adapter = AsyncMock()
    adapter.recall_memories.side_effect = RuntimeError("boom")

    service = VectorSearchService()
    with patch("api.services.vector_search.get_memevolve_adapter", return_value=adapter):
        response = await service.semantic_search(query="test", top_k=5, threshold=0.7)

    assert response.count == 0
    assert response.results == []
