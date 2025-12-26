"""
MemEvolve Integration Models

Pydantic models for MemEvolve-Dionysus integration.
Feature: 009-memevolve-integration
Phase: 1 - Foundation
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "ok"
    service: str = "dionysus-memevolve-adapter"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrajectoryStep(BaseModel):
    """Individual step in a MemEvolve trajectory."""
    observation: Optional[str] = Field(None, description="Observed state or event")
    thought: Optional[str] = Field(None, description="Agent thought or reasoning")
    action: Optional[str] = Field(None, description="Action taken by the agent")

    model_config = {"extra": "allow"}


class TrajectoryMetadata(BaseModel):
    """Metadata associated with a MemEvolve trajectory."""
    agent_id: Optional[str] = Field(None, description="Identifier for the agent")
    session_id: Optional[str] = Field(None, description="Session identifier")
    project_id: Optional[str] = Field(None, description="Project identifier")

    model_config = {"extra": "allow"}


class TrajectoryData(BaseModel):
    """Trajectory data from MemEvolve."""
    steps: List[TrajectoryStep] = Field(
        default_factory=list,
        description="Ordered list of trajectory steps"
    )
    metadata: Optional[TrajectoryMetadata] = Field(
        None,
        description="Metadata for the trajectory"
    )
    summary: Optional[str] = Field(
        None,
        description="Optional summary provided by the agent"
    )


class MemoryIngestRequest(BaseModel):
    """Request model for ingesting memory trajectories from MemEvolve."""
    trajectory: TrajectoryData = Field(
        ...,
        description="Trajectory data containing the agent experience"
    )


class MemoryRecallItem(BaseModel):
    """Individual memory item in recall response."""
    id: str = Field(..., description="Memory UUID")
    content: str = Field(..., description="Memory content text")
    type: str = Field(default="semantic", description="Memory type")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score")
    similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="Similarity score from vector search")
    valid_at: Optional[datetime] = Field(None, description="Temporal validity start (Graphiti)")
    invalid_at: Optional[datetime] = Field(None, description="Temporal validity end (Graphiti)")
    session_id: Optional[str] = Field(None, description="Source session ID")
    project_id: Optional[str] = Field(None, description="Source project ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="Memory tags")


class MemoryRecallRequest(BaseModel):
    """Request model for recalling memories for MemEvolve."""
    query: str = Field(
        ...,
        description="Query string for semantic memory recall"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        alias="max_results",
        description="Maximum number of results to return"
    )
    memory_types: Optional[List[str]] = Field(
        None,
        description="Filter by memory types: episodic, semantic, procedural, strategic"
    )
    project_id: Optional[str] = Field(
        None,
        description="Filter by project ID"
    )
    session_id: Optional[str] = Field(
        None,
        description="Filter by session ID"
    )
    include_temporal_metadata: bool = Field(
        default=False,
        description="Include Graphiti temporal validity (valid_at, invalid_at)"
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for recall filtering"
    )

    class Config:
        populate_by_name = True


class MemoryRecallResponse(BaseModel):
    """Response model for memory recall."""
    memories: List[MemoryRecallItem] = Field(
        default_factory=list,
        description="Retrieved memories with similarity scores"
    )
    query: str = Field(..., description="Original query string")
    result_count: int = Field(default=0, description="Number of results returned")
    search_time_ms: Optional[float] = Field(None, description="Search execution time in milliseconds")


class IngestResponse(BaseModel):
    """Response model for memory ingestion."""
    ingest_id: UUID = Field(..., description="Unique ingestion event ID")
    entities_extracted: int = Field(0, description="Number of entities extracted")
    memories_created: int = Field(0, description="Number of memories created")
