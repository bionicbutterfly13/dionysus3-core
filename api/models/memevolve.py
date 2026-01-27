"""
MemEvolve Integration Models

Pydantic models for MemEvolve-Dionysus integration.
Feature: 009-memevolve-integration
Phase: 1 - Foundation

TERMINOLOGY NOTE:
"Trajectory" in this module refers to EXECUTION TRACES (operational),
NOT state-space trajectories (theoretical/IWMT).

- TrajectoryData = sequence of agent steps during a run (audit trail)
- TrajectoryStep = single action/observation pair

For state-space dynamics, see specs/038-thoughtseeds-framework/.
Full disambiguation: docs/TERMINOLOGY.md
"""

from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "ok"
    service: str = "dionysus-memevolve-adapter"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrajectoryType(str, Enum):
    """Classification for trajectory data."""
    EPISODIC = "episodic"
    STRUCTURAL = "structural"


class TrajectoryStep(BaseModel):
    """Individual step in a MemEvolve trajectory."""
    model_config = ConfigDict(extra="allow")

    observation: Optional[str] = Field(None, description="Observed state or event")
    thought: Optional[str] = Field(None, description="Agent thought or reasoning")
    action: Optional[str] = Field(None, description="Action taken by the agent")


class TrajectoryMetadata(BaseModel):
    """Metadata associated with a MemEvolve trajectory."""
    model_config = ConfigDict(extra="allow")

    agent_id: Optional[str] = Field(None, description="Identifier for the agent")
    session_id: Optional[str] = Field(None, description="Session identifier")
    project_id: Optional[str] = Field(None, description="Project identifier")
    trajectory_type: TrajectoryType = Field(default=TrajectoryType.EPISODIC, description="Type of trajectory")
    success: Optional[bool] = Field(None, description="Whether the task succeeded")
    reward: Optional[float] = Field(None, description="Terminal reward or score")
    cost: Optional[float] = Field(None, description="Estimated API cost for the run")
    latency_ms: Optional[float] = Field(None, description="Execution latency in ms")
    model_id: Optional[str] = Field(None, description="Model identifier used by the agent")
    timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp for trajectory occurrence (used as valid_at when provided)",
    )
    tags: Optional[List[str]] = Field(default_factory=list, description="Optional tags for the run")


class TrajectoryData(BaseModel):
    """Trajectory data from MemEvolve."""
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = Field(None, description="Trajectory UUID")
    query: Optional[str] = Field(None, description="Original task query")
    trajectory: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Raw trajectory events (EvolveLab-compatible)"
    )
    steps: List[TrajectoryStep] = Field(
        default_factory=list,
        description="Ordered list of trajectory steps"
    )
    result: Optional[Any] = Field(
        None,
        description="Outcome payload or terminal reward"
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
    model_config = ConfigDict(extra="allow")

    trajectory: TrajectoryData = Field(
        ...,
        description="Trajectory data containing the agent experience"
    )
    entities: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional pre-extracted entities"
    )
    edges: Optional[List[Dict[str, Any]]] = Field(
        None,
        validation_alias=AliasChoices("edges", "relationships"),
        description="Optional pre-extracted relationships (edges)"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session override for the ingest"
    )
    project_id: Optional[str] = Field(
        None,
        description="Optional project override for the ingest"
    )
    memory_type: Optional[str] = Field(
        None,
        description="Optional memory type label for the ingest"
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
    device_id: Optional[str] = Field(None, description="Source device ID")
    from_date: Optional[datetime] = Field(None, description="Memory valid from date")
    to_date: Optional[datetime] = Field(None, description="Memory valid to date")
    tags: Optional[List[str]] = Field(default_factory=list, description="Memory tags")


class MemoryRecallRequest(BaseModel):
    """Request model for recalling memories for MemEvolve."""
    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(
        ...,
        description="Query string for semantic memory recall"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        validation_alias=AliasChoices("max_results", "top_k", "limit"),
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
    device_id: Optional[str] = Field(
        None,
        description="Filter by device ID (Identity Anchoring)"
    )
    include_temporal_metadata: bool = Field(
        default=False,
        description="Include Graphiti temporal validity (valid_at, invalid_at)"
    )
    context: Optional[Dict[str, Any] | str] = Field(
        default=None,
        description="Additional context for recall filtering or raw context string"
    )


class MemoryRecallResponse(BaseModel):
    """Response model for memory recall."""
    memories: List[MemoryRecallItem] = Field(
        default_factory=list,
        description="Retrieved memories with similarity scores"
    )
    query: str = Field(..., description="Original query string")
    result_count: int = Field(default=0, description="Number of results returned")
    search_time_ms: Optional[float] = Field(None, description="Search execution time in milliseconds")
    error: Optional[str] = Field(None, description="Optional error message when recall fails")


class IngestResponse(BaseModel):
    """Response model for memory ingestion."""
    ingest_id: UUID = Field(..., description="Unique ingestion event ID")
    entities_extracted: int = Field(0, description="Number of entities extracted")
    memories_created: int = Field(0, description="Number of memories created")


class EvolutionResponse(BaseModel):
    """Response model for meta-evolution."""
    success: bool = Field(..., description="Whether the evolution trigger was successful")
    message: str = Field(..., description="Status message or error details")
    optimization_basis: Optional[str] = Field(None, description="Summary of data analyzed")
    new_strategy_id: Optional[str] = Field(None, description="UUID of the created RetrievalStrategy node")
