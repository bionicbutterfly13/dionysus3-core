"""
Meta-ToT Models
Feature: 041-meta-tot-engine
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetaToTDecision(BaseModel):
    """Threshold decision for Meta-ToT activation."""

    use_meta_tot: bool = Field(..., description="Whether Meta-ToT should run")
    complexity_score: float = Field(..., description="0-1 complexity estimate")
    uncertainty_score: float = Field(..., description="0-1 uncertainty estimate")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="Decision thresholds")
    rationale: str = Field(..., description="Decision rationale")


class MetaToTNodeTrace(BaseModel):
    """Trace snapshot for a single Meta-ToT node."""

    node_id: str
    parent_id: Optional[str] = None
    depth: int
    node_type: str
    cpa_domain: str
    thought: str
    score: float
    visit_count: int
    value_estimate: float
    prediction_error: float
    free_energy: float
    children_ids: List[str] = Field(default_factory=list)


class MetaToTTracePayload(BaseModel):
    """Stored trace payload for a Meta-ToT run."""

    trace_id: str
    session_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    decision: Optional[MetaToTDecision] = None
    best_path: List[str] = Field(default_factory=list)
    selected_action: Optional[str] = None
    confidence: Optional[float] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    nodes: List[MetaToTNodeTrace] = Field(default_factory=list)


class MetaToTResult(BaseModel):
    """Result of a Meta-ToT run."""

    session_id: str
    best_path: List[str]
    confidence: float
    metrics: Dict[str, Any]
    decision: Optional[MetaToTDecision] = None
    trace_id: Optional[str] = None
    active_inference_state: Optional[Dict[str, Any]] = None


class MetaToTRunRequest(BaseModel):
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)


class MetaToTRunResponse(BaseModel):
    decision: MetaToTDecision
    result: MetaToTResult
    trace: Optional[MetaToTTracePayload] = None
