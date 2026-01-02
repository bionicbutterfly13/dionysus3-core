"""
Memory Router
Features: 002-remote-persistence-safety, 003-semantic-search
Tasks: T034, T035, T039, T040, T005, T006

API endpoints for memory queries with session and project attribution.
Includes semantic similarity search (Feature 003).
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from api.services.remote_sync import RemoteSyncService
from api.services.vector_search import (
    VectorSearchService,
    SearchFilters,
    get_vector_search_service,
)


router = APIRouter(prefix="/api/memory", tags=["memory"])


# =============================================================================
# Response Models
# =============================================================================


class MemoryResponse(BaseModel):
    """Single memory response."""
    id: str
    content: str
    type: str
    importance: float = 0.5
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: Optional[str] = None


class MemoryListResponse(BaseModel):
    """List of memories response."""
    memories: list[MemoryResponse] = Field(default_factory=list)
    total: int = 0
    session_id: Optional[str] = None
    project_id: Optional[str] = None


class SessionMemoriesResponse(BaseModel):
    """Memories for a specific session."""
    session_id: str
    memories: list[MemoryResponse] = Field(default_factory=list)
    total: int = 0
    session_metadata: Optional[dict] = None


class ProjectMemoriesResponse(BaseModel):
    """Memories for a specific project (T039-T040)."""
    project_id: str
    memories: list[MemoryResponse] = Field(default_factory=list)
    total: int = 0


# =============================================================================
# Graph Traversal (Webhook-backed)
# =============================================================================


class TraverseQueryType(str, Enum):
    CONCEPT_HIERARCHY = "concept_hierarchy"
    JOURNEY_TIMELINE = "journey_timeline"
    RELATED_2HOP = "related_2hop"
    DOCUMENT_LINKS = "document_links"
    WORLDVIEW_FILTER = "worldview_filter"
    SKILL_GRAPH = "skill_graph"


class MemoryTraverseRequest(BaseModel):
    query_type: TraverseQueryType = Field(
        ...,
        description="Traversal query identifier (mapped to vetted Cypher in n8n).",
    )
    params: dict = Field(default_factory=dict, description="Query parameters")


class MemoryTraverseResponse(BaseModel):
    success: bool = True
    query_type: str
    data: dict = Field(default_factory=dict)


# =============================================================================
# Dependencies
# =============================================================================


def get_sync_service() -> RemoteSyncService:
    """Get RemoteSyncService instance."""
    return RemoteSyncService()


# =============================================================================
# Session Endpoints (T034)
# =============================================================================


@router.get(
    "/sessions/{session_id}",
    response_model=SessionMemoriesResponse,
    summary="Get memories by session ID",
    description="Retrieve all memories from a specific session.",
)
async def get_session_memories(
    session_id: str,
    query: Optional[str] = Query(None, description="Optional keyword search"),
    include_metadata: bool = Query(False, description="Include session start/end times"),
) -> SessionMemoriesResponse:
    """
    T034: GET /api/memory/sessions/{session_id}

    Retrieve all memories from a specific coding session.
    """
    sync_service = get_sync_service()

    memories = await sync_service.query_by_session(
        session_id=session_id,
        query=query,
        include_session_metadata=include_metadata,
    )

    return SessionMemoriesResponse(
        session_id=session_id,
        memories=[MemoryResponse(**m) for m in memories],
        total=len(memories),
        session_metadata=memories[0].get("session_metadata") if memories and include_metadata else None,
    )


# =============================================================================
# Date Range Endpoints (T035)
# =============================================================================


@router.get(
    "/range",
    response_model=MemoryListResponse,
    summary="Get memories by date range",
    description="Query memories within a date range.",
)
async def get_memories_by_date_range(
    from_date: datetime = Query(..., description="Start of date range (ISO format)"),
    to_date: datetime = Query(..., description="End of date range (ISO format)"),
    session_id: Optional[str] = Query(None, description="Filter by session"),
) -> MemoryListResponse:
    """
    T035: Date range filtering for memories.

    Query memories created within the specified date range.
    """
    sync_service = get_sync_service()

    memories = await sync_service.query_by_date_range(
        from_date=from_date,
        to_date=to_date,
        session_id=session_id,
    )

    return MemoryListResponse(
        memories=[MemoryResponse(**m) for m in memories],
        total=len(memories),
        session_id=session_id,
    )


# =============================================================================
# Search Endpoints (T036)
# =============================================================================


@router.get(
    "/search",
    response_model=MemoryListResponse,
    summary="Search memories with session attribution",
    description="Search memories with optional session/project attribution.",
)
async def search_memories(
    query: str = Query(..., description="Search query"),
    include_attribution: bool = Query(True, description="Include session_id in results"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
) -> MemoryListResponse:
    """
    T036: Session attribution in search results.

    Search memories and include session attribution.
    """
    sync_service = get_sync_service()

    memories = await sync_service.search_memories(
        query=query,
        include_session_attribution=include_attribution,
        limit=limit,
    )

    return MemoryListResponse(
        memories=[MemoryResponse(**m) for m in memories],
        total=len(memories),
    )


# =============================================================================
# Project Endpoints (T039, T040 - Phase 5)
# =============================================================================


@router.get(
    "/projects",
    response_model=list[ProjectMemoriesResponse],
    summary="Get memories grouped by project",
    description="Query memories across all projects.",
)
async def get_memories_by_project(
    query: Optional[str] = Query(None, description="Optional keyword search"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per project"),
) -> list[ProjectMemoriesResponse]:
    """
    T039: Cross-project query endpoint.

    Query memories across different projects.
    """
    sync_service = get_sync_service()

    # This will be implemented when Phase 5 methods are added
    # For now, return empty list
    return []


@router.get(
    "/projects/{project_id}",
    response_model=ProjectMemoriesResponse,
    summary="Get memories for a specific project",
    description="Query memories from a specific project.",
)
async def get_project_memories(
    project_id: str,
    query: Optional[str] = Query(None, description="Optional keyword search"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
) -> ProjectMemoriesResponse:
    """
    T040: Project-specific memory query.

    Get all memories from a specific project.
    """
    sync_service = get_sync_service()

    # This will use project-specific query when implemented
    # For now, return empty
    return ProjectMemoriesResponse(
        project_id=project_id,
        memories=[],
        total=0,
    )


@router.post(
    "/traverse",
    response_model=MemoryTraverseResponse,
    summary="Run vetted graph traversal query",
    description="Executes a predefined traversal query via n8n; the API never contacts Neo4j directly.",
)
async def traverse_memory_graph(req: MemoryTraverseRequest) -> MemoryTraverseResponse:
    sync_service = get_sync_service()
    result = await sync_service.traverse(query_type=req.query_type.value, params=req.params)
    if not result.get("success", True):
        raise HTTPException(status_code=502, detail=result.get("error", "Traversal failed"))
    return MemoryTraverseResponse(
        success=True,
        query_type=req.query_type.value,
        data=result,
    )


# =============================================================================
# Semantic Search Endpoints (Feature 003 - T005, T006)
# =============================================================================


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., description="Natural language search query", min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    project_id: Optional[str] = Field(None, description="Filter by project")
    session_id: Optional[str] = Field(None, description="Filter by session")
    from_date: Optional[datetime] = Field(None, description="Filter by start date")
    to_date: Optional[datetime] = Field(None, description="Filter by end date")
    memory_types: Optional[list[str]] = Field(None, description="Filter by memory types")


class SemanticSearchResultItem(BaseModel):
    """Single semantic search result."""
    id: str
    content: str
    memory_type: str
    importance: float
    similarity_score: float
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: Optional[datetime] = None
    tags: Optional[list[str]] = None


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    query: str
    results: list[SemanticSearchResultItem]
    count: int
    embedding_time_ms: float
    search_time_ms: float
    total_time_ms: float


@router.post(
    "/semantic-search",
    response_model=SemanticSearchResponse,
    summary="Semantic similarity search",
    description="Search memories using semantic similarity (vector embeddings).",
)
async def semantic_search(
    request: SemanticSearchRequest,
) -> SemanticSearchResponse:
    """
    T005, T006: Semantic search endpoint with filters.

    Searches memories using vector similarity via the n8n vector-search webhook.
    The webhook is responsible for embedding the query and running the
    Neo4j vector index (provider configurable in n8n).

    Filters can narrow results by project, session, date range, or memory type.
    """
    search_service = get_vector_search_service()

    # Build filters from request
    filters = SearchFilters(
        project_id=request.project_id,
        session_id=request.session_id,
        from_date=request.from_date,
        to_date=request.to_date,
        memory_types=request.memory_types,
    )

    try:
        response = await search_service.semantic_search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            filters=filters,
        )

        return SemanticSearchResponse(
            query=response.query,
            results=[
                SemanticSearchResultItem(
                    id=r.id,
                    content=r.content,
                    memory_type=r.memory_type,
                    importance=r.importance,
                    similarity_score=r.similarity_score,
                    session_id=r.session_id,
                    project_id=r.project_id,
                    created_at=r.created_at,
                    tags=r.tags,
                )
                for r in response.results
            ],
            count=response.count,
            embedding_time_ms=response.embedding_time_ms,
            search_time_ms=response.search_time_ms,
            total_time_ms=response.total_time_ms,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.get(
    "/semantic-search/health",
    summary="Semantic search health check",
    description="Check health of semantic search services (Neo4j, Ollama).",
)
async def semantic_search_health() -> dict:
    """
    Health check for semantic search infrastructure.

    Verifies:
    - n8n webhook connectivity
    - configured vector search URL
    """
    search_service = get_vector_search_service()
    return await search_service.health_check()
