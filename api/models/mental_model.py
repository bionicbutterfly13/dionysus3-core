"""
Mental Model Pydantic Models
Feature: 005-mental-models
Tasks: T011-T014 (Phase 2: Foundational)

Pydantic models for mental model entities, predictions, revisions,
and request/response schemas.
Based on data-model.md and contracts/rest-api.yaml specifications.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# T011: Enums
# =============================================================================


class ModelDomain(str, Enum):
    """
    Domain type for mental models.

    Domains:
        USER: Models about the user's patterns, preferences, behaviors
        SELF: Models about the system's own capabilities and limitations
        WORLD: Models about external domain knowledge
        TASK_SPECIFIC: Models for specific task contexts
    """

    USER = "user"
    SELF = "self"
    WORLD = "world"
    TASK_SPECIFIC = "task_specific"


class ModelStatus(str, Enum):
    """
    Lifecycle status for mental models.

    States:
        DRAFT: Model created but not yet validated
        ACTIVE: Model is active and generating predictions
        DEPRECATED: Model is no longer in use (soft delete)
    """

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class RevisionTrigger(str, Enum):
    """
    What triggered a model revision.

    Triggers:
        PREDICTION_ERROR: High error rate triggered automatic revision
        USER_REQUEST: User explicitly requested a revision
        NEW_MEMORY: New memory contradicted model predictions
        NEW_EVIDENCE: New memory contradicted model predictions
        CONTRADICTION: Model conflicts with other models
        MANUAL: Human-triggered revision
    """

    PREDICTION_ERROR = "prediction_error"
    USER_REQUEST = "user_request"
    NEW_MEMORY = "new_memory"
    NEW_EVIDENCE = "new_evidence"
    CONTRADICTION = "contradiction"
    MANUAL = "manual"


class RelationshipType(str, Enum):
    """Types of relationships between basins in a model."""

    CAUSAL = "causal"
    TEMPORAL = "temporal"
    HIERARCHICAL = "hierarchical"
    ASSOCIATED = "associated"


# =============================================================================
# T011: Embedded Types
# =============================================================================


class BasinRelationship(BaseModel):
    """Describes how two basins relate within a model."""

    from_basin: UUID
    to_basin: UUID
    type: RelationshipType
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    description: str | None = None


class BasinRelationships(BaseModel):
    """Container for basin relationships."""

    relationships: list[BasinRelationship] = Field(default_factory=list)


class PredictionTemplate(BaseModel):
    """
    Pattern for generating predictions.

    Stored in mental_models.prediction_templates.
    """

    trigger: str = Field(description="What triggers this prediction")
    predict: str = Field(description="What the model predicts")
    suggest: str | None = Field(None, description="Suggested action")
    confidence_modifier: float = Field(
        default=0.0, ge=-1.0, le=1.0, description="Adjustment to base confidence"
    )
    applicable_domains: list[str] = Field(default_factory=list)


# =============================================================================
# T011: MentalModel Entity
# =============================================================================


class MentalModel(BaseModel):
    """
    A structured combination of memory basins that generates predictions.

    Based on Yufik's neuronal packet theory (2019, 2021).
    Mental models combine attractor basins (memory clusters) to form
    predictive structures about users, self, world, or specific tasks.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(max_length=255)
    domain: ModelDomain
    description: str | None = None

    # Basin composition
    constituent_basins: list[UUID] = Field(min_length=1)
    basin_relationships: BasinRelationships = Field(
        default_factory=lambda: BasinRelationships()
    )

    # Prediction capabilities
    prediction_templates: list[PredictionTemplate] = Field(default_factory=list)
    explanatory_scope: list[str] = Field(default_factory=list)
    requires_sensory_input: bool = False
    temporal_horizon: timedelta | None = None

    # Evidence and validation
    evidence_memories: list[UUID] = Field(default_factory=list)
    prediction_accuracy: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Rolling accuracy score"
    )
    last_validated: datetime | None = None

    # Lifecycle
    revision_count: int = Field(default=0, ge=0)
    status: ModelStatus = ModelStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("constituent_basins")
    @classmethod
    def validate_basins_not_empty(cls, v: list[UUID]) -> list[UUID]:
        if not v:
            raise ValueError("constituent_basins must contain at least one basin")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440099",
                "name": "User Emotional Patterns",
                "domain": "user",
                "description": "Predicts user emotional states based on conversation patterns",
                "constituent_basins": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002",
                ],
                "prediction_accuracy": 0.72,
                "status": "active",
            }
        }
    }


# =============================================================================
# T012: ModelPrediction Entity
# =============================================================================


class ModelPrediction(BaseModel):
    """
    A specific prediction generated by a mental model.

    Predictions are generated during the OBSERVE phase of the heartbeat
    and resolved during the ORIENT phase when actual outcomes are observed.
    """

    id: UUID = Field(default_factory=uuid4)
    model_id: UUID

    # Prediction content
    prediction: dict[str, Any] = Field(description="The prediction content")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Model confidence in prediction"
    )
    context: dict[str, Any] | None = Field(
        None, description="What prompted this prediction"
    )

    # Resolution (filled when prediction is resolved)
    observation: dict[str, Any] | None = Field(
        None, description="Actual outcome observed"
    )
    prediction_error: float | None = Field(
        None, ge=0.0, le=1.0, description="Calculated error (0=perfect, 1=completely wrong)"
    )
    resolved_at: datetime | None = None

    # Link to active inference state
    inference_state_id: UUID | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_resolved(self) -> bool:
        """Check if prediction has been resolved."""
        return self.resolved_at is not None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440100",
                "model_id": "660e8400-e29b-41d4-a716-446655440099",
                "prediction": {
                    "state": "anxiety",
                    "trigger": "work stress mention",
                    "suggested_response": "acknowledge feelings first",
                },
                "confidence": 0.75,
                "context": {"user_message": "I'm so stressed about this deadline"},
                "observation": None,
                "prediction_error": None,
                "resolved_at": None,
            }
        }
    }


# =============================================================================
# T013: ModelRevision Entity
# =============================================================================


class ModelRevision(BaseModel):
    """
    Historical record of changes to a model's structure.

    Revisions track what changed, why, and the impact on model accuracy.
    """

    id: UUID = Field(default_factory=uuid4)
    model_id: UUID

    # Revision sequencing (not currently persisted in DB schema, but used in tests/specs)
    revision_number: int = Field(default=1, ge=1, description="Monotonic revision number")

    # Trigger information
    trigger_type: RevisionTrigger = Field(alias="trigger")
    trigger_memory_id: UUID | None = None
    trigger_description: str | None = None

    # Structure changes
    old_structure: dict[str, Any] | None = None
    new_structure: dict[str, Any] | None = None
    basins_added: list[UUID] = Field(default_factory=list)
    basins_removed: list[UUID] = Field(default_factory=list)
    change_description: str | None = None

    # Accuracy tracking
    prediction_error_before: float | None = Field(None, ge=0.0, le=1.0, alias="accuracy_before")
    prediction_error_after: float | None = Field(None, ge=0.0, le=1.0, alias="accuracy_after")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def trigger(self) -> RevisionTrigger:
        """Compatibility alias for tests/specs."""
        return self.trigger_type

    @property
    def accuracy_before(self) -> float | None:
        """Compatibility alias for tests/specs."""
        return self.prediction_error_before

    @property
    def accuracy_after(self) -> float | None:
        """Compatibility alias for tests/specs."""
        return self.prediction_error_after

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440101",
                "model_id": "660e8400-e29b-41d4-a716-446655440099",
                "trigger": "prediction_error",
                "trigger_description": "Average error exceeded 50% threshold",
                "basins_added": ["550e8400-e29b-41d4-a716-446655440003"],
                "basins_removed": [],
                "accuracy_before": 0.55,
                "accuracy_after": 0.42,
            }
        }
    }


# =============================================================================
# T014: Request Schemas
# =============================================================================


class CreateModelRequest(BaseModel):
    """Request to create a new mental model."""

    name: str = Field(max_length=255)
    domain: ModelDomain
    basin_ids: list[UUID] = Field(min_length=1, description="Memory cluster IDs")
    description: str | None = None
    prediction_templates: list[PredictionTemplate] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "User Work Patterns",
                "domain": "user",
                "basin_ids": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002",
                ],
                "description": "Predicts user behavior around work and productivity",
                "prediction_templates": [
                    {
                        "trigger": "user mentions deadline",
                        "predict": "likely feeling time pressure",
                        "suggest": "help prioritize or break down task",
                    }
                ],
            }
        }
    }


class UpdateModelRequest(BaseModel):
    """Request to update a mental model."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    status: ModelStatus | None = None
    prediction_templates: list[PredictionTemplate] | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "active",
                "prediction_templates": [
                    {
                        "trigger": "user mentions deadline",
                        "predict": "likely feeling time pressure",
                        "suggest": "help prioritize or break down task",
                    }
                ],
            }
        }
    }


class ReviseModelRequest(BaseModel):
    """Request to revise a model's structure."""

    trigger_description: str
    add_basins: list[UUID] = Field(default_factory=list)
    remove_basins: list[UUID] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "trigger_description": "Adding career patterns basin based on recent conversations",
                "add_basins": ["550e8400-e29b-41d4-a716-446655440003"],
                "remove_basins": [],
            }
        }
    }


# =============================================================================
# T014: Response Schemas
# =============================================================================


class ModelResponse(BaseModel):
    """Response with model summary."""

    id: UUID
    name: str
    domain: ModelDomain
    status: ModelStatus
    prediction_accuracy: float
    basin_count: int
    revision_count: int
    created_at: datetime
    updated_at: datetime


class ModelDetailResponse(ModelResponse):
    """Response with full model details."""

    description: str | None
    constituent_basins: list[UUID]
    basin_relationships: BasinRelationships
    prediction_templates: list[PredictionTemplate]
    evidence_memories: list[UUID]


class ModelListResponse(BaseModel):
    """Response with list of models."""

    models: list[ModelResponse]
    total: int
    limit: int
    offset: int


class PredictionResponse(BaseModel):
    """Response with prediction details."""

    id: UUID
    model_id: UUID
    prediction: dict[str, Any]
    confidence: float
    context: dict[str, Any] | None
    observation: dict[str, Any] | None
    prediction_error: float | None
    resolved_at: datetime | None
    created_at: datetime


class PredictionListResponse(BaseModel):
    """Response with list of predictions."""

    predictions: list[PredictionResponse]
    total: int
    limit: int
    offset: int


class RevisionResponse(BaseModel):
    """Response with revision details."""

    id: UUID
    model_id: UUID
    trigger_type: RevisionTrigger
    trigger_description: str | None
    basins_added: list[UUID]
    basins_removed: list[UUID]
    change_description: str | None
    prediction_error_before: float | None
    prediction_error_after: float | None
    created_at: datetime


class RevisionListResponse(BaseModel):
    """Response with list of revisions."""

    revisions: list[RevisionResponse]
    total: int
    limit: int
    offset: int


# =============================================================================
# MCP Tool Response Schemas
# =============================================================================


class CreateModelToolResponse(BaseModel):
    """Response from create_model MCP tool."""

    success: bool
    model_id: UUID | None = None
    message: str


class ListModelsToolResponse(BaseModel):
    """Response from list_models MCP tool."""

    models: list[ModelResponse]
    total: int


class GetModelToolResponse(BaseModel):
    """Response from get_model MCP tool."""

    model: ModelDetailResponse | None
    predictions: list[PredictionResponse] | None = None
    revisions: list[RevisionResponse] | None = None


class ReviseModelToolResponse(BaseModel):
    """Response from revise_model MCP tool."""

    success: bool
    revision_id: UUID | None = None
    message: str
    new_accuracy: float | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    code: str | None = None
    details: dict[str, Any] | None = None
