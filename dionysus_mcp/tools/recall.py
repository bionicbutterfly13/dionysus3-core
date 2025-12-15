"""
Semantic Recall MCP Tool
Feature: 003-semantic-search
Tasks: T008, T009, T010

MCP tool for semantic memory recall with context formatting.
"""

import logging
from typing import Optional

from api.services.vector_search import (
    VectorSearchService,
    SearchFilters,
    SearchResult,
    get_vector_search_service,
)

logger = logging.getLogger("dionysus.mcp.recall")


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.7
DEFAULT_WEIGHT_BY_IMPORTANCE = True


# =============================================================================
# Semantic Recall Tool
# =============================================================================

async def semantic_recall_tool(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = DEFAULT_THRESHOLD,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    memory_types: Optional[list[str]] = None,
    weight_by_importance: bool = DEFAULT_WEIGHT_BY_IMPORTANCE,
) -> str:
    """
    Recall semantically relevant memories for context injection.

    This tool searches the memory store using vector similarity to find
    memories related to the query. Results are formatted for easy injection
    into Claude's context.

    Args:
        query: Natural language query describing what context you need
        top_k: Maximum number of memories to return (default: 5)
        threshold: Minimum similarity score 0.0-1.0 (default: 0.7)
        project_id: Optional filter by project
        session_id: Optional filter by session
        memory_types: Optional filter by types (episodic, semantic, procedural, strategic)
        weight_by_importance: Whether to boost results by importance score (default: True)

    Returns:
        Formatted string with relevant memories for context injection
    """
    try:
        search_service = get_vector_search_service()

        # Build filters
        filters = SearchFilters(
            project_id=project_id,
            session_id=session_id,
            memory_types=memory_types,
        )

        # Execute search
        response = await search_service.semantic_search(
            query=query,
            top_k=top_k,
            threshold=threshold,
            filters=filters,
        )

        # Handle no results
        if response.count == 0:
            return f"No relevant memories found for query: '{query}' (threshold: {threshold})"

        # Sort by weighted score if enabled
        results = response.results
        if weight_by_importance:
            results = sorted(
                results,
                key=lambda r: r.similarity_score * (0.5 + 0.5 * r.importance),
                reverse=True,
            )

        # Format results for context injection
        formatted = format_results_for_context(
            query=query,
            results=results,
            total_time_ms=response.total_time_ms,
        )

        return formatted

    except Exception as e:
        logger.error(f"Semantic recall failed: {e}", exc_info=True)
        return f"Error during semantic recall: {str(e)}"


def format_results_for_context(
    query: str,
    results: list[SearchResult],
    total_time_ms: float,
) -> str:
    """
    Format search results for injection into Claude's context.

    Args:
        query: Original query
        results: List of search results
        total_time_ms: Total search time

    Returns:
        Formatted string suitable for context injection
    """
    lines = [
        f"## Relevant Memories ({len(results)} found)",
        f"Query: \"{query}\"",
        "",
    ]

    for i, result in enumerate(results, 1):
        # Build memory entry
        entry_lines = [
            f"### Memory {i} (relevance: {result.similarity_score:.0%})",
            f"**Type**: {result.memory_type} | **Importance**: {result.importance:.0%}",
        ]

        # Add optional metadata
        if result.project_id:
            entry_lines.append(f"**Project**: {result.project_id}")
        if result.session_id:
            entry_lines.append(f"**Session**: {result.session_id[:8]}...")

        # Add content
        entry_lines.append("")
        entry_lines.append(result.content)
        entry_lines.append("")

        lines.extend(entry_lines)

    # Add footer
    lines.append(f"---")
    lines.append(f"*Retrieved in {total_time_ms:.0f}ms*")

    return "\n".join(lines)


# =============================================================================
# Tool Registration (for FastMCP)
# =============================================================================

# Tool definition for MCP server registration
RECALL_TOOL_DEFINITION = {
    "name": "semantic_recall",
    "description": """Recall semantically relevant memories for context injection.

Use this tool when you need to:
- Find relevant past context for the current task
- Recall how something was done before
- Get background information on a topic from previous sessions
- Find related decisions or implementations

The tool searches using vector similarity, finding memories with similar meaning
even if the exact words don't match.

Example queries:
- "How did we implement rate limiting?"
- "What decisions were made about the database schema?"
- "Previous discussions about authentication"
""",
    "parameters": {
        "query": {
            "type": "string",
            "description": "Natural language query describing what context you need",
            "required": True,
        },
        "top_k": {
            "type": "integer",
            "description": "Maximum memories to return (default: 5)",
            "required": False,
        },
        "threshold": {
            "type": "number",
            "description": "Minimum similarity score 0.0-1.0 (default: 0.7)",
            "required": False,
        },
        "project_id": {
            "type": "string",
            "description": "Filter by project ID",
            "required": False,
        },
        "session_id": {
            "type": "string",
            "description": "Filter by session ID",
            "required": False,
        },
        "memory_types": {
            "type": "array",
            "description": "Filter by memory types: episodic, semantic, procedural, strategic",
            "required": False,
        },
    },
}


# List of tools for registration
RECALL_TOOLS = [
    (semantic_recall_tool, RECALL_TOOL_DEFINITION),
]
