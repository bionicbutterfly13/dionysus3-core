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


class MemoryIngestRequest(BaseModel):
    """Request model for ingesting memory trajectories from MemEvolve."""
    trajectory_data: Dict[str, Any] = Field(
        ...,
        description="Trajectory data from MemEvolve containing memory state snapshots"
    )
    source_agent: Optional[str] = Field(
        None,
        description="Identifier of the MemEvolve agent sending the data"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for the ingestion"
    )


class MemoryRecallRequest(BaseModel):
    """Request model for recalling memories for MemEvolve."""
    query: str = Field(
        ...,
        description="Query string for semantic memory recall"
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for recall filtering"
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )


class MemoryRecallResponse(BaseModel):
    """Response model for memory recall."""
    memories: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved memories"
    )
    query: str
    result_count: int = 0


class IngestResponse(BaseModel):
    """Response model for memory ingestion."""
    success: bool = True
    ingested_count: int = 0
    message: str = "Ingestion complete"
