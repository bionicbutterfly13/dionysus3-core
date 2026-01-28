"""
Subconscious observation models.

Feature: 102-subconscious-integration
Adapted from Hexis observation taxonomy; applied via MemoryBasinRouter/GraphitiService only.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class NarrativeObservation(BaseModel):
    """Narrative moment: chapter transition, turning point, theme emergence."""

    type: Optional[str] = Field(None, description="e.g. chapter_transition, turning_point, theme_emergence")
    kind: Optional[str] = None
    summary: Optional[str] = None
    rationale: Optional[str] = None
    evidence_summary: Optional[str] = None
    suggested_name: Optional[str] = None
    theme: Optional[str] = None
    pattern: Optional[str] = None
    confidence: Optional[float] = None
    evidence: Optional[list[Any]] = None
    evidence_ids: Optional[list[str]] = None
    memory_ids: Optional[list[str]] = None
    memory_id: Optional[str] = None
    evidence_memory_id: Optional[str] = None


class RelationshipObservation(BaseModel):
    """Relationship shift: entity, strength, change type."""

    entity: Optional[str] = None
    name: Optional[str] = None
    change_type: Optional[str] = None
    type: Optional[str] = None
    strength: Optional[float] = None
    new_strength: Optional[float] = None
    magnitude: Optional[float] = None
    confidence: Optional[float] = None
    summary: Optional[str] = None
    belief: Optional[str] = None
    evidence: Optional[list[Any]] = None
    evidence_ids: Optional[list[str]] = None
    memory_ids: Optional[list[str]] = None
    evidence_memory_id: Optional[str] = None


class ContradictionObservation(BaseModel):
    """Contradiction between beliefs/memories."""

    memory_a: Optional[str] = None
    memory_b: Optional[str] = None
    belief_a_id: Optional[str] = None
    belief_b_id: Optional[str] = None
    worldview_id: Optional[str] = None
    belief_id: Optional[str] = None
    tension: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    evidence: Optional[list[Any]] = None


class EmotionalObservation(BaseModel):
    """Emotional pattern observation."""

    pattern: Optional[str] = None
    summary: Optional[str] = None
    theme: Optional[str] = None
    confidence: Optional[float] = None
    frequency: Optional[int] = None
    unprocessed: Optional[bool] = None
    evidence: Optional[list[Any]] = None


class ConsolidationObservation(BaseModel):
    """Consolidation opportunity: link memories under a concept."""

    memory_ids: Optional[list[str]] = None
    memories: Optional[list[Any]] = None
    concept: Optional[str] = None
    suggested_concept: Optional[str] = None
    rationale: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    cluster_id: Optional[str] = None
    suggested_cluster_id: Optional[str] = None


class SubconsciousObservations(BaseModel):
    """Full observation payload from subconscious decider (Hexis-style)."""

    narrative_observations: list[NarrativeObservation] = Field(default_factory=list)
    relationship_observations: list[RelationshipObservation] = Field(default_factory=list)
    contradiction_observations: list[ContradictionObservation] = Field(default_factory=list)
    emotional_observations: list[EmotionalObservation] = Field(default_factory=list)
    consolidation_observations: list[ConsolidationObservation] = Field(default_factory=list)

    class Config:
        extra = "allow"


class SessionStartRequest(BaseModel):
    """Request for session-start (Letta-style)."""

    session_id: str
    project_id: Optional[str] = None
    cwd: Optional[str] = None


class SyncResponse(BaseModel):
    """Response for sync: guidance and memory blocks (Letta-style)."""

    guidance: str = ""
    memory_blocks: dict[str, str] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    """Request for ingest: transcript or summary (Letta-style)."""

    session_id: str
    transcript: Optional[str] = None
    summary: Optional[str] = None
