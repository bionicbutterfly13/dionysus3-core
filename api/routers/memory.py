"""
Memory Router
Feature: 002-remote-persistence-safety
Tasks: T034, T035, T039, T040

API endpoints for memory queries with session and project attribution.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from api.services.remote_sync import RemoteSyncService


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
