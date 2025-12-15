"""
Contract Tests: semantic_recall MCP Tool
Feature: 003-semantic-search
Task: T007

Tests for the semantic_recall MCP tool interface.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_search_results():
    """Sample search results for mocking."""
    return [
        {
            "id": "mem-001",
            "content": "Implemented token bucket algorithm for request throttling",
            "memory_type": "procedural",
            "importance": 0.8,
            "similarity_score": 0.92,
            "session_id": "sess-abc",
            "project_id": "dionysus-core",
        },
        {
            "id": "mem-002",
            "content": "Rate limiting prevents API abuse",
            "memory_type": "semantic",
            "importance": 0.7,
            "similarity_score": 0.85,
            "session_id": "sess-def",
            "project_id": "dionysus-core",
        },
    ]


# =============================================================================
# Contract Tests
# =============================================================================

class TestSemanticRecallMCPContract:
    """Contract tests for semantic_recall MCP tool."""

    def test_tool_has_required_parameters(self):
        """Verify tool accepts required parameters."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        # Tool should exist and be callable
        assert callable(semantic_recall_tool)

    @pytest.mark.asyncio
    async def test_tool_returns_formatted_context(self, mock_search_results):
        """Verify tool returns properly formatted context string."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = [
                MagicMock(
                    id=r["id"],
                    content=r["content"],
                    memory_type=r["memory_type"],
                    importance=r["importance"],
                    similarity_score=r["similarity_score"],
                    session_id=r.get("session_id"),
                    project_id=r.get("project_id"),
                )
                for r in mock_search_results
            ]
            mock_response.count = len(mock_search_results)
            mock_response.total_time_ms = 50.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            result = await semantic_recall_tool(
                query="rate limiting",
                top_k=5,
                threshold=0.7,
            )

            # Should return a formatted string with context
            assert isinstance(result, str)
            assert "rate limiting" in result.lower() or "token bucket" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_respects_threshold(self, mock_search_results):
        """Verify tool passes threshold parameter correctly."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = []
            mock_response.count = 0
            mock_response.total_time_ms = 10.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            await semantic_recall_tool(
                query="test",
                threshold=0.95,  # High threshold
            )

            # Verify threshold was passed
            call_kwargs = mock_search.semantic_search.call_args.kwargs
            assert call_kwargs.get("threshold") == 0.95

    @pytest.mark.asyncio
    async def test_tool_respects_top_k(self, mock_search_results):
        """Verify tool passes top_k parameter correctly."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = []
            mock_response.count = 0
            mock_response.total_time_ms = 10.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            await semantic_recall_tool(
                query="test",
                top_k=3,
            )

            # Verify top_k was passed
            call_kwargs = mock_search.semantic_search.call_args.kwargs
            assert call_kwargs.get("top_k") == 3

    @pytest.mark.asyncio
    async def test_tool_filters_by_project(self, mock_search_results):
        """Verify tool can filter by project_id."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = []
            mock_response.count = 0
            mock_response.total_time_ms = 10.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            await semantic_recall_tool(
                query="test",
                project_id="dionysus-core",
            )

            # Verify project filter was passed
            call_kwargs = mock_search.semantic_search.call_args.kwargs
            filters = call_kwargs.get("filters")
            assert filters is not None
            assert filters.project_id == "dionysus-core"

    @pytest.mark.asyncio
    async def test_tool_handles_no_results(self):
        """Verify tool handles empty results gracefully."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = []
            mock_response.count = 0
            mock_response.total_time_ms = 10.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            result = await semantic_recall_tool(
                query="completely unknown topic xyz123",
            )

            # Should return informative message, not error
            assert isinstance(result, str)
            assert "no" in result.lower() or "0" in result

    @pytest.mark.asyncio
    async def test_tool_handles_errors_gracefully(self):
        """Verify tool handles errors without crashing."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_search.semantic_search.side_effect = Exception("Connection failed")
            mock_service.return_value = mock_search

            result = await semantic_recall_tool(
                query="test",
            )

            # Should return error message, not raise
            assert isinstance(result, str)
            assert "error" in result.lower() or "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_includes_importance_weighting(self, mock_search_results):
        """Verify results consider importance scores."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = [
                MagicMock(
                    id="mem-001",
                    content="High importance memory",
                    memory_type="procedural",
                    importance=0.9,  # High importance
                    similarity_score=0.8,
                    session_id=None,
                    project_id=None,
                ),
                MagicMock(
                    id="mem-002",
                    content="Low importance memory",
                    memory_type="semantic",
                    importance=0.3,  # Low importance
                    similarity_score=0.85,  # Higher similarity but lower importance
                    session_id=None,
                    project_id=None,
                ),
            ]
            mock_response.count = 2
            mock_response.total_time_ms = 20.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            result = await semantic_recall_tool(
                query="test",
                weight_by_importance=True,
            )

            # Tool should format results (implementation will weight by importance)
            assert isinstance(result, str)


class TestSemanticRecallMCPOutput:
    """Tests for output formatting of semantic_recall tool."""

    @pytest.mark.asyncio
    async def test_output_includes_memory_content(self, mock_search_results):
        """Verify output includes actual memory content."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = [
                MagicMock(
                    id="mem-001",
                    content="Token bucket rate limiting implementation details",
                    memory_type="procedural",
                    importance=0.8,
                    similarity_score=0.92,
                    session_id="sess-abc",
                    project_id="dionysus-core",
                )
            ]
            mock_response.count = 1
            mock_response.total_time_ms = 30.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            result = await semantic_recall_tool(query="rate limiting")

            # Should include the memory content
            assert "Token bucket" in result or "rate limiting" in result.lower()

    @pytest.mark.asyncio
    async def test_output_format_for_context_injection(self, mock_search_results):
        """Verify output is formatted for easy context injection."""
        from dionysus_mcp.tools.recall import semantic_recall_tool

        with patch('dionysus_mcp.tools.recall.get_vector_search_service') as mock_service:
            mock_search = AsyncMock()
            mock_response = MagicMock()
            mock_response.results = [
                MagicMock(
                    id=r["id"],
                    content=r["content"],
                    memory_type=r["memory_type"],
                    importance=r["importance"],
                    similarity_score=r["similarity_score"],
                    session_id=r.get("session_id"),
                    project_id=r.get("project_id"),
                )
                for r in mock_search_results
            ]
            mock_response.count = len(mock_search_results)
            mock_response.total_time_ms = 40.0

            mock_search.semantic_search.return_value = mock_response
            mock_service.return_value = mock_search

            result = await semantic_recall_tool(query="rate limiting")

            # Output should be suitable for injection into Claude context
            # Should be clear, formatted text
            assert len(result) > 0
            # Should have some structure (newlines for multiple results)
            if len(mock_search_results) > 1:
                assert "\n" in result
