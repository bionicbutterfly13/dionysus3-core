"""
MOSAEIC Dual Memory Architecture Models
Feature: 008-mosaeic-memory

Pydantic models for the dual memory system implementing:
- Episodic memory with time-based decay
- Semantic memory with confidence-based preservation
- Turning point detection and preservation
- Basin reorganization dynamics

Ported from:
- Dionysus-2.0/backend/src/models/cognition_base.py
- active-inference-core/src/caicore/dynamics/attractor_basin_manager.py
- infomarket/src/consciousness/pattern_evolution.py
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enumerations
# =============================================================================


class ExperientialDimension(str, Enum):
    """
    Five experiential windows for capturing autobiographical episodes.
    Based on cognitive science research on memory encoding.
    """
    MENTAL = "mental"           # Thoughts, cognitions, inner dialogue
    OBSERVATION = "observation" # Perceptions, what was noticed externally
    SENSES = "senses"           # Sensory details (visual, auditory, tactile)
    ACTIONS = "actions"         # Behavioral responses, what was done
    EMOTIONS = "emotions"       # Affective states, feelings


class TurningPointTrigger(str, Enum):
    """
    What triggered a memory to be marked as a Turning Point (flashbulb memory).
    These memories are exempt from time-based decay.
    """
    HIGH_EMOTION = "high_emotion"   # Emotional intensity >= 8.0
    SURPRISE = "surprise"           # Large prediction error (> 0.8)
    CONSEQUENCE = "consequence"     # Linked to severe maladaptive pattern
    MANUAL = "manual"               # Explicitly flagged by user/system


class PatternSeverity(str, Enum):
    """Severity levels for maladaptive patterns."""
    LOW = "low"           # Minor inconvenience
    MODERATE = "moderate" # Noticeable impact
    HIGH = "high"         # Significant impairment
    CRITICAL = "critical" # Requires immediate intervention


class BasinInfluenceType(str, Enum):
    """
    Types of influence between attractor basins when new beliefs emerge.
    Ported from active-inference-core/attractor_basin_manager.py
    """
    REINFORCEMENT = "reinforcement"  # New belief strengthens existing basin
    COMPETITION = "competition"      # New belief competes with existing basin
    SYNTHESIS = "synthesis"          # New belief merges with existing basin
    EMERGENCE = "emergence"          # New belief creates entirely new basin


class PatternType(str, Enum):
    """
    Types of cognition patterns.
    Ported from Dionysus-2.0/cognition_base.py
    """
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    EMERGENT = "emergent"
    RECURSIVE = "recursive"
    HIERARCHICAL = "hierarchical"
    DYNAMIC = "dynamic"
    SELF_ORGANIZING = "self_organizing"
    META_COGNITIVE = "meta_cognitive"


# =============================================================================
# Decay Configuration
# =============================================================================


class DecayRate(BaseModel):
    """Configuration for differential decay rates by experiential dimension."""
    dimension: ExperientialDimension
    half_life_days: int = Field(ge=1, description="Days until 50% decay")


# Default decay rates based on cognitive research
# Peripheral details decay faster than central gist
DEFAULT_DECAY_RATES = [
    DecayRate(dimension=ExperientialDimension.SENSES, half_life_days=7),
    DecayRate(dimension=ExperientialDimension.OBSERVATION, half_life_days=14),
    DecayRate(dimension=ExperientialDimension.EMOTIONS, half_life_days=21),
    DecayRate(dimension=ExperientialDimension.ACTIONS, half_life_days=60),
    DecayRate(dimension=ExperientialDimension.MENTAL, half_life_days=90),
]


# =============================================================================
# Episodic Memory Entities
# =============================================================================


class FiveWindowCapture(BaseModel):
    """
    Context-rich autobiographical snapshot across five experiential dimensions.

    Episodic memories governed by time-based decay (efficiency protocol).
    Old captures are pruned unless marked as Turning Points.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(description="FK to sessions.id")

    # Five experiential windows
    mental: str | None = Field(None, description="Thoughts, cognitions")
    observation: str | None = Field(None, description="What was perceived")
    senses: str | None = Field(None, description="Sensory details")
    actions: str | None = Field(None, description="Behavioral responses")
    emotions: str | None = Field(None, description="Affective states")

    # Temporal context
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Surrounding conversation state"
    )

    # Intensity and preservation
    emotional_intensity: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="Emotional intensity rating 0-10"
    )
    preserve_indefinitely: bool = Field(
        default=False,
        description="Turning Point flag - exempt from decay"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_turning_point_candidate(self) -> bool:
        """Check if this capture might be a Turning Point based on intensity."""
        return self.emotional_intensity >= 8.0

    @property
    def age_days(self) -> int:
        """Days since capture was created."""
        return (datetime.utcnow() - self.created_at).days

    def should_decay(self, threshold_days: int = 180) -> bool:
        """Check if this capture should be decayed."""
        return (
            not self.preserve_indefinitely and
            self.age_days > threshold_days
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "660e8400-e29b-41d4-a716-446655440001",
                "mental": "Thinking about the deadline pressure",
                "observation": "User seemed stressed and distracted",
                "senses": "Rapid typing, tense voice tone",
                "actions": "Offered to help prioritize tasks",
                "emotions": "Empathy, slight concern",
                "emotional_intensity": 6.5,
                "preserve_indefinitely": False,
            }
        }
    }


class TurningPoint(BaseModel):
    """
    Marker for emotionally significant memories exempt from decay.

    Turning Points are the "flashbulb memories" marked "KEEP FOREVER".
    Based on amygdala-hippocampus interaction during encoding.
    """
    id: UUID = Field(default_factory=uuid4)
    capture_id: UUID = Field(description="FK to five_window_captures.id")

    # Trigger information
    trigger_type: TurningPointTrigger
    trigger_description: str | None = None

    # Autobiographical linking (from 005-mental-models spec)
    narrative_thread_id: UUID | None = Field(
        None,
        description="Link to autobiographical narrative thread"
    )
    life_chapter_id: UUID | None = Field(
        None,
        description="Link to life chapter"
    )

    # Metadata
    vividness_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Subjective confidence in recall vividness"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "capture_id": "550e8400-e29b-41d4-a716-446655440000",
                "trigger_type": "high_emotion",
                "trigger_description": "Major breakthrough in understanding",
                "vividness_score": 0.95,
            }
        }
    }


# =============================================================================
# Semantic Memory Entities
# =============================================================================


class BeliefRewrite(BaseModel):
    """
    Semantic belief indexed by confidence, not age.

    Semantic memories governed by confidence-based preservation (accuracy protocol).
    High-confidence beliefs persist indefinitely; low-confidence beliefs may be archived.
    """
    id: UUID = Field(default_factory=uuid4)
    old_belief_id: UUID | None = Field(
        None,
        description="Link to replaced belief for tracking transformation"
    )

    # Belief content
    new_belief: str = Field(min_length=1, description="The belief content")
    domain: str = Field(
        description="user, self, world, or task_specific"
    )

    # Confidence scoring
    adaptiveness_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence/adaptiveness proxy"
    )
    evidence_count: int = Field(
        default=0,
        ge=0,
        description="Number of supporting evidence instances"
    )
    last_verified: datetime | None = None

    # Prediction tracking
    prediction_success_count: int = Field(default=0, ge=0)
    prediction_failure_count: int = Field(default=0, ge=0)

    # Evolution tracking (from BasinInfluenceType)
    evolution_trigger: BasinInfluenceType | None = Field(
        None,
        description="What triggered this belief evolution"
    )

    # Lifecycle
    archived: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def accuracy(self) -> float:
        """Calculate prediction accuracy."""
        total = self.prediction_success_count + self.prediction_failure_count
        if total == 0:
            return 0.5  # Prior assumption
        return self.prediction_success_count / total

    @property
    def needs_revision(self) -> bool:
        """Check if belief needs revision based on accuracy threshold."""
        total = self.prediction_success_count + self.prediction_failure_count
        if total < 5:  # Not enough data
            return False
        return self.accuracy < 0.5  # Below 50% accuracy

    def update_confidence(self, prediction_correct: bool) -> None:
        """Update confidence based on prediction outcome."""
        if prediction_correct:
            self.prediction_success_count += 1
        else:
            self.prediction_failure_count += 1

        self.adaptiveness_score = self.accuracy
        self.last_verified = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "old_belief_id": None,
                "new_belief": "User works best with structured task breakdowns",
                "domain": "user",
                "adaptiveness_score": 0.78,
                "evidence_count": 12,
                "prediction_success_count": 18,
                "prediction_failure_count": 5,
                "evolution_trigger": "reinforcement",
            }
        }
    }


class MaladaptivePattern(BaseModel):
    """
    Recurring negative pattern tracked for intervention.

    When recurrence_count reaches threshold and severity is high,
    intervention is triggered.
    """
    id: UUID = Field(default_factory=uuid4)

    # Pattern identification
    belief_content: str = Field(min_length=1)
    domain: str = Field(description="user, self, world, or task_specific")

    # Severity metrics
    severity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )
    severity_level: PatternSeverity = PatternSeverity.LOW
    recurrence_count: int = Field(default=0, ge=0)

    # Intervention status
    intervention_triggered: bool = False
    last_intervention: datetime | None = None

    # Links
    linked_capture_ids: list[UUID] = Field(default_factory=list)
    linked_model_ids: list[UUID] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def increment_recurrence(self) -> None:
        """Increment recurrence count and reassess severity."""
        self.recurrence_count += 1
        self.updated_at = datetime.utcnow()

        # Auto-escalate severity based on recurrence
        if self.recurrence_count >= 10:
            self.severity_level = PatternSeverity.CRITICAL
            self.severity_score = min(1.0, self.severity_score + 0.1)
        elif self.recurrence_count >= 5:
            self.severity_level = PatternSeverity.HIGH
            self.severity_score = min(1.0, self.severity_score + 0.05)
        elif self.recurrence_count >= 3:
            self.severity_level = PatternSeverity.MODERATE

    @property
    def should_intervene(self) -> bool:
        """Check if intervention should be triggered."""
        return (
            self.severity_score >= 0.7 and
            self.recurrence_count >= 3 and
            not self.intervention_triggered
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "990e8400-e29b-41d4-a716-446655440000",
                "belief_content": "I always fail at important tasks",
                "domain": "self",
                "severity_score": 0.65,
                "severity_level": "moderate",
                "recurrence_count": 4,
                "intervention_triggered": False,
            }
        }
    }


class VerificationEncounter(BaseModel):
    """
    Log of when a belief was tested against reality.

    During MOSAEIC Phase 5 (Verification), updated beliefs are tested
    in new episodic contexts and outcomes are logged.
    """
    id: UUID = Field(default_factory=uuid4)

    # What was tested
    belief_id: UUID
    prediction_id: UUID

    # Outcome
    prediction_content: dict[str, Any] = Field(
        description="The prediction that was made"
    )
    observation: dict[str, Any] | None = Field(
        None,
        description="The actual outcome observed"
    )
    belief_activated: str | None = Field(
        None,
        description="'old' or 'new' - which belief version activated"
    )
    prediction_error: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Calculated error magnitude"
    )

    # Context
    session_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_resolved(self) -> bool:
        """Check if this encounter has been resolved."""
        return self.observation is not None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "aa0e8400-e29b-41d4-a716-446655440000",
                "belief_id": "880e8400-e29b-41d4-a716-446655440000",
                "prediction_id": "bb0e8400-e29b-41d4-a716-446655440000",
                "prediction_content": {"expected_state": "stress", "confidence": 0.8},
                "observation": {"actual_state": "focused", "notes": "Task completed"},
                "belief_activated": "new",
                "prediction_error": 0.3,
            }
        }
    }


# =============================================================================
# Pattern Evolution (ported from infomarket/pattern_evolution.py)
# =============================================================================


class KnowledgePattern(BaseModel):
    """
    Knowledge pattern with emergence tracking.
    Ported from infomarket/src/consciousness/pattern_evolution.py
    """
    pattern_id: str = Field(default_factory=lambda: str(uuid4()))
    generalized: bool = False
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    projects_used: list[str] = Field(default_factory=list)
    evolved_from: str | None = None

    def is_validated(
        self,
        min_success_rate: float = 0.7,
        min_projects: int = 2
    ) -> bool:
        """Validate pattern shows genuine learning."""
        return (
            self.generalized and
            self.success_rate >= min_success_rate and
            len(self.projects_used) >= min_projects
        )


class CognitionPattern(BaseModel):
    """
    Individual cognition pattern within the cognitive base.
    Ported from Dionysus-2.0/backend/src/models/cognition_base.py
    """
    pattern_id: str = Field(default_factory=lambda: str(uuid4()))
    pattern_name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10)
    pattern_type: PatternType

    # Pattern quality metrics
    success_rate: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reliability_score: float = Field(ge=0.0, le=1.0)

    # Usage and learning metrics
    usage_count: int = Field(default=0, ge=0)
    last_used: datetime = Field(default_factory=datetime.utcnow)
    creation_date: datetime = Field(default_factory=datetime.utcnow)

    # Pattern relationships and evolution
    parent_patterns: list[str] = Field(default_factory=list)
    child_patterns: list[str] = Field(default_factory=list)
    related_patterns: list[str] = Field(default_factory=list)
    evolution_history: list[dict[str, Any]] = Field(default_factory=list)

    # Consciousness emergence tracking
    consciousness_contribution: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )
    emergence_markers: list[str] = Field(default_factory=list)

    @field_validator("evolution_history")
    @classmethod
    def validate_evolution_history(cls, v: list[dict]) -> list[dict]:
        """Validate evolution history structure."""
        required_fields = ["timestamp", "change_type", "change_description"]
        for entry in v:
            for field in required_fields:
                if field not in entry:
                    raise ValueError(
                        f"Evolution history entry missing required field: {field}"
                    )
        return v


# =============================================================================
# Attractor Basin (ported from active-inference-core)
# =============================================================================


class AttractorBasin(BaseModel):
    """
    An attractor basin in the cognitive landscape.
    Ported from active-inference-core/src/caicore/dynamics/attractor_basin_manager.py
    """
    basin_id: str = Field(default_factory=lambda: str(uuid4()))
    center_concept: str = Field(description="Central concept that defines the basin")
    strength: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Basin depth/strength"
    )
    radius: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Basin influence radius"
    )
    thoughtseeds: set[str] = Field(default_factory=set)
    related_concepts: dict[str, float] = Field(
        default_factory=dict,
        description="concept -> similarity mapping"
    )
    formation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_modification: datetime = Field(default_factory=datetime.utcnow)
    activation_history: list[float] = Field(default_factory=list)

    def calculate_influence_on(
        self,
        concept_similarity: float
    ) -> tuple[BasinInfluenceType, float]:
        """
        Calculate how this basin would influence a new concept/thoughtseed.

        Args:
            concept_similarity: Similarity to basin center concept (0.0 - 1.0)

        Returns:
            Tuple of (influence_type, influence_strength)
        """
        # High similarity -> reinforcement or synthesis
        if concept_similarity > 0.8:
            if self.strength > 1.5:
                return (
                    BasinInfluenceType.REINFORCEMENT,
                    concept_similarity * self.strength
                )
            else:
                return BasinInfluenceType.SYNTHESIS, concept_similarity * 0.8

        # Medium similarity -> competition or synthesis
        elif concept_similarity > 0.5:
            if self.strength > 1.0:
                return (
                    BasinInfluenceType.COMPETITION,
                    (1.0 - concept_similarity) * self.strength
                )
            else:
                return BasinInfluenceType.SYNTHESIS, concept_similarity * 0.6

        # Low similarity -> emergence (new basin)
        else:
            return BasinInfluenceType.EMERGENCE, 1.0 - concept_similarity

    model_config = {"arbitrary_types_allowed": True}


# =============================================================================
# Request/Response Schemas
# =============================================================================


class CreateCaptureRequest(BaseModel):
    """Request to create a new FiveWindowCapture."""
    session_id: UUID
    mental: str | None = None
    observation: str | None = None
    senses: str | None = None
    actions: str | None = None
    emotions: str | None = None
    emotional_intensity: float = Field(default=5.0, ge=0.0, le=10.0)
    context: dict[str, Any] = Field(default_factory=dict)


class CreateBeliefRequest(BaseModel):
    """Request to create a new BeliefRewrite."""
    new_belief: str = Field(min_length=1)
    domain: str
    old_belief_id: UUID | None = None
    evidence_count: int = Field(default=0, ge=0)


class UpdateBeliefRequest(BaseModel):
    """Request to update an existing belief."""
    prediction_correct: bool | None = None
    archived: bool | None = None


class CaptureResponse(BaseModel):
    """Response with capture details."""
    id: UUID
    session_id: UUID
    emotional_intensity: float
    preserve_indefinitely: bool
    is_turning_point: bool
    created_at: datetime


class BeliefResponse(BaseModel):
    """Response with belief details."""
    id: UUID
    new_belief: str
    domain: str
    adaptiveness_score: float
    accuracy: float
    needs_revision: bool
    archived: bool
    created_at: datetime
    updated_at: datetime


class PatternResponse(BaseModel):
    """Response with maladaptive pattern details."""
    id: UUID
    belief_content: str
    domain: str
    severity_level: PatternSeverity
    recurrence_count: int
    should_intervene: bool
    created_at: datetime
