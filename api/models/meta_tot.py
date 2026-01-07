"""
Meta-ToT Models
Feature: 041-meta-tot-engine
"""

import json
import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ActiveInferenceState(BaseModel):
    """Active inference currency state."""

    state_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prediction_error: float = 0.0
    free_energy: float = 0.0
    surprise: float = 0.0
    precision: float = 1.0
    beliefs: Dict[str, float] = Field(default_factory=dict)
    prediction_updates: Dict[str, float] = Field(default_factory=dict)
    reasoning_level: int = 0
    parent_state_id: Optional[str] = None

    def compute_prediction_error(self, observation: Dict[str, float]) -> float:
        total_error = 0.0
        for key, observed_value in observation.items():
            predicted_value = self.beliefs.get(key, observed_value)
            error = abs(observed_value - predicted_value)
            total_error += error * self.precision
        self.prediction_error = total_error
        return total_error

    def update_beliefs(self, prediction_error: float, learning_rate: float = 0.1) -> None:
        for belief_key, belief_value in list(self.beliefs.items()):
            gradient = self.prediction_updates.get(belief_key, 0.0)
            belief_update = -learning_rate * gradient * prediction_error
            self.beliefs[belief_key] = max(0.0, min(1.0, belief_value + belief_update))
        self.free_energy = prediction_error + 0.01 * len(self.beliefs)
        self.surprise = -math.log(max(0.001, 1.0 - min(prediction_error, 0.99)))


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
    active_inference_state: Optional[ActiveInferenceState] = None


class MetaToTRunRequest(BaseModel):
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)


class MetaToTRunResponse(BaseModel):
    decision: MetaToTDecision
    result: MetaToTResult
    trace: Optional[MetaToTTracePayload] = None
