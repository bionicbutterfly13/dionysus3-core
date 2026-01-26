"""
Beautiful Loop models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PrecisionProfile(BaseModel):
    """Global precision state across all inference layers."""

    layer_precisions: Dict[str, float] = Field(
        default_factory=dict,
        description="Precision weight per inference layer (0-1)",
    )
    modality_precisions: Dict[str, float] = Field(
        default_factory=dict,
        description="Precision weight per sensory modality (0-1)",
    )
    temporal_depth: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How far into future to weight predictions (0=immediate, 1=long-term)",
    )
    meta_precision: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in this precision profile itself",
    )
    context_embedding: List[float] = Field(
        default_factory=list,
        description="Embedding of context that generated this profile",
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: Optional[str] = Field(default=None, description="OODA cycle that generated this")

    @field_validator("layer_precisions", "modality_precisions")
    @classmethod
    def validate_precision_values(cls, value: Dict[str, float]) -> Dict[str, float]:
        for key, precision in value.items():
            if not 0.0 <= precision <= 1.0:
                raise ValueError(f"Precision for '{key}' must be in [0, 1], got {precision}")
        return value


class PrecisionError(BaseModel):
    """Second-order error on precision forecast."""

    layer_id: str = Field(description="Which layer this error occurred at")
    predicted_precision: float = Field(ge=0.0, le=1.0)
    actual_precision_needed: float = Field(ge=0.0, le=1.0)
    error_magnitude: float = Field(default=0.0, ge=0.0)
    error_direction: Literal["over_confident", "under_confident"] = Field(
        default="under_confident"
    )
    context_hash: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def compute_derived(self) -> "PrecisionError":
        self.error_magnitude = abs(self.predicted_precision - self.actual_precision_needed)
        self.error_direction = (
            "over_confident"
            if self.predicted_precision > self.actual_precision_needed
            else "under_confident"
        )
        return self


class BoundInference(BaseModel):
    """An inference that passed binding competition."""

    inference_id: str
    source_layer: str
    content: Dict[str, Any] = Field(default_factory=dict)
    embedding: List[float] = Field(default_factory=list)
    precision_score: float = Field(ge=0.0, le=1.0)
    coherence_score: float = Field(ge=0.0, le=1.0)
    uncertainty_reduction: float = Field(description="How much this reduces overall uncertainty")
    binding_strength: float = Field(default=0.0, ge=0.0)
    bound_at: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def compute_binding_strength(self) -> "BoundInference":
        self.binding_strength = (
            self.precision_score
            * self.coherence_score
            * max(0.0, self.uncertainty_reduction)
        )
        return self


class ResonanceMode(str, Enum):
    """Modes of cognitive resonance derived from prediction error and coherence."""
    LUMINOUS = "luminous"
    STABLE = "stable"
    TURBULENT = "turbulent"
    DISSONANT = "dissonant"
    TRANSCENDENT = "transcendent"


class ResonanceSignal(BaseModel):
    """Unified signal for cognitive state and discovery requirement."""
    mode: ResonanceMode
    resonance_score: float = Field(ge=0.0, le=1.0)
    surprisal: float = Field(default=0.0)
    coherence: float = Field(default=0.0)
    discovery_urgency: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: Optional[str] = Field(default=None)


class UnifiedRealityModel(BaseModel):
    """Unified world model container for conscious experience."""

    belief_states: List[Any] = Field(default_factory=list)
    active_inference_states: List[Any] = Field(default_factory=list)
    metacognitive_particles: List[Any] = Field(default_factory=list)
    bound_inferences: List[BoundInference] = Field(default_factory=list)
    resonance: Optional[ResonanceSignal] = Field(default=None)
    coherence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    epistemic_affordances: List[str] = Field(default_factory=list)
    current_context: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: Optional[str] = Field(default=None)


class EpistemicState(BaseModel):
    """Current epistemic depth/luminosity level."""

    depth_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reality_model_coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    active_bindings: List[str] = Field(default_factory=list)
    transparent_processes: List[str] = Field(default_factory=list)
    luminosity_factors: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BindingConfig(BaseModel):
    """Configuration for Bayesian binding."""

    min_capacity: int = Field(default=5, ge=1)
    max_capacity: int = Field(default=9, ge=1)
    default_capacity: int = Field(default=7, ge=1)
    precision_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    coherence_threshold: float = Field(default=0.4, ge=0.0, le=1.0)

    def get_capacity(self, task_complexity: float) -> int:
        span = self.max_capacity - self.min_capacity
        return int(self.max_capacity - (task_complexity * span))


class HyperModelConfig(BaseModel):
    """Configuration for hyper-model learning."""

    base_learning_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    min_learning_rate: float = Field(default=0.01, ge=0.0)
    max_learning_rate: float = Field(default=0.3, le=1.0)
    default_layers: List[str] = Field(
        default_factory=lambda: ["perception", "reasoning", "metacognition", "action"]
    )
    default_modalities: List[str] = Field(
        default_factory=lambda: ["visual", "semantic", "procedural", "episodic"]
    )


class InferenceCandidate(BaseModel):
    inference_id: str
    source_layer: str
    content: Dict[str, Any] = Field(default_factory=dict)
    embedding: List[float] = Field(default_factory=list)


class PrecisionForecastRequest(BaseModel):
    context: Dict[str, Any]
    internal_states: Dict[str, Any] = Field(default_factory=dict)
    recent_errors: List[PrecisionError] = Field(default_factory=list)


class PrecisionErrorsRequest(BaseModel):
    errors: List[PrecisionError]
    cycle_id: str


class PrecisionErrorsResponse(BaseModel):
    recorded_count: int
    learning_delta: float


class BindingEvaluationRequest(BaseModel):
    candidates: List[InferenceCandidate]
    precision_profile: Optional[PrecisionProfile] = None
    binding_capacity: Optional[int] = None


class BindingEvaluationResponse(BaseModel):
    bound_inferences: List[BoundInference]
    rejected_count: int
    average_binding_strength: float


# ---------------------------------------------------------------------------
# Event types (FR-027)
# ---------------------------------------------------------------------------


class PrecisionForecastEvent(BaseModel):
    """Event emitted when a precision profile is forecast for a cycle."""

    event_type: Literal["precision_forecast"] = "precision_forecast"
    precision_profile: PrecisionProfile
    cycle_id: str


class PrecisionErrorEvent(BaseModel):
    """Event emitted when precision errors are recorded for a cycle."""

    event_type: Literal["precision_error"] = "precision_error"
    errors: List[PrecisionError]
    cycle_id: str


class PrecisionUpdateEvent(BaseModel):
    """Event emitted when the hyper-model updates precision from learning."""

    event_type: Literal["precision_update"] = "precision_update"
    new_profile: PrecisionProfile
    learning_delta: float


class BindingCompletedEvent(BaseModel):
    """Event emitted when binding competition completes for a cycle."""

    event_type: Literal["binding_completed"] = "binding_completed"
    bound_count: int
    rejected_count: int
    average_binding_strength: float
    cycle_id: Optional[str] = None


class CoherenceResponse(BaseModel):
    coherence_score: float
    bound_inference_count: int


class DepthResponse(BaseModel):
    depth_score: float
    luminosity_factors: Dict[str, float]


class BeautifulLoopConfig(BaseModel):
    binding: BindingConfig
    hyper_model: HyperModelConfig


class BeautifulLoopConfigUpdate(BaseModel):
    binding: Optional[BindingConfig] = None
    hyper_model: Optional[HyperModelConfig] = None
