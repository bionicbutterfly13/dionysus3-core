import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Particle Type Classification
# =============================================================================

class ParticleType(str, Enum):
    """
    Types of metacognitive particles based on Markov blanket structure.
    
    From Sandved-Smith & Da Costa (2024):
    - COGNITIVE: Basic beliefs about external (μ → Q_μ(η))
    - PASSIVE_METACOGNITIVE: Beliefs about beliefs, no direct control
    - ACTIVE_METACOGNITIVE: Has internal blanket with active paths
    - STRANGE_METACOGNITIVE: Actions inferred via sensory (a¹ does NOT influence μ¹)
    - NESTED_N_LEVEL: Multiple internal Markov blankets
    """
    COGNITIVE = "cognitive"
    PASSIVE = "passive"
    PASSIVE_METACOGNITIVE = "passive_metacognitive"
    ACTIVE = "active"
    ACTIVE_METACOGNITIVE = "active_metacognitive"
    STRANGE = "strange"
    STRANGE_METACOGNITIVE = "strange_metacognitive"
    NESTED = "nested"
    NESTED_N_LEVEL = "nested_n_level"
    MULTIPLY_NESTED = "multiply_nested"


class MentalActionType(str, Enum):
    """Types of mental actions for procedural metacognition."""
    PRECISION_DELTA = "precision_delta"
    SET_PRECISION = "set_precision"
    FOCUS_TARGET = "focus_target"
    SPOTLIGHT_PRECISION = "spotlight_precision"


# Constants
MAX_NESTING_DEPTH = 5


# =============================================================================
# Cognitive Core Enforcement (FR-015, FR-016, FR-017)
# =============================================================================

class CognitiveCoreViolation(Exception):
    """
    Raised when metacognitive nesting exceeds MAX_NESTING_DEPTH.

    Prevents infinite metacognitive regress per Sandved-Smith & Da Costa (2024).
    """
    pass


def enforce_cognitive_core(level: int) -> None:
    """
    Enforce cognitive core constraint on nesting depth.

    Raises CognitiveCoreViolation if level exceeds MAX_NESTING_DEPTH.

    Args:
        level: The metacognitive nesting level to validate

    Raises:
        CognitiveCoreViolation: If level > MAX_NESTING_DEPTH
    """
    if level > MAX_NESTING_DEPTH:
        raise CognitiveCoreViolation(
            f"Cannot create metacognitive level {level}. "
            f"Maximum allowed is level {MAX_NESTING_DEPTH}. Cognitive core reached."
        )


def maintains_cognitive_core(particle_type: ParticleType) -> bool:
    """
    Check if particle type maintains cognitive core constraint.

    Returns True if particle type is within cognitive core bounds.
    """
    return particle_type in [
        ParticleType.COGNITIVE,
        ParticleType.PASSIVE_METACOGNITIVE,
        ParticleType.ACTIVE_METACOGNITIVE,
    ]


class CognitiveCore(BaseModel):
    """
    Represents the cognitive core constraint for a particle.

    The cognitive core prevents infinite metacognitive regress by limiting
    the depth of nested Markov blankets.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    particle_id: str = Field(..., description="ID of the particle this core constrains")
    max_recursion_level: int = Field(
        default=MAX_NESTING_DEPTH,
        ge=1,
        le=MAX_NESTING_DEPTH,
        description="Maximum allowed nesting depth"
    )
    complexity_bound: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Normalized complexity bound for the cognitive core"
    )
    beliefs_encoded: Optional[str] = Field(
        None,
        description="Formal representation of beliefs encoded at this level (e.g., Q_{mu^n}(eta, mu^1, ...))"
    )


class ClassificationResult(BaseModel):
    """Result from particle classification."""
    particle_id: str
    particle_type: ParticleType
    confidence: float = Field(ge=0.0, le=1.0)
    level: int = Field(ge=0)
    has_agency: bool


class MetacognitiveParticle(BaseModel):
    """
    Atomic unit of thought in the Dionysus cognitive architecture.
    
    A Particle represents a single cognitive event, observation, or deduction.
    It carries epistemic metadata (precision, entropy) to support Active Inference.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="The textual representation of the thought.")
    source_agent: str = Field(..., description="ID of the agent/process that generated this.")
    context_id: Optional[str] = Field(None, description="UUID of the Session or Journey context.")
    provenance_ids: List[str] = Field(default_factory=list, description="IDs of Neuronal Packets (Nodes) this thought is derived from.")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Active Inference States
    precision: float = Field(default=1.0, ge=0.0, le=5.0, description="Inverse variance (Confidence).")
    entropy: float = Field(default=0.0, ge=0.0, description="Uncertainty measure.")
    
    # Global Workspace Dynamics
    resonance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Activation level in GW.")
    is_active: bool = Field(default=True, description="Whether the particle is currently held in working memory.")
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('precision')
    @classmethod
    def validate_precision(cls, v):
        """Ensure precision is within reasonable bounds (0.0 to 5.0)."""
        return max(0.0, min(5.0, v))

    def decay(self, rate: float = 0.1) -> None:
        """Apply temporal decay to resonance."""
        self.resonance_score = max(0.0, self.resonance_score * (1.0 - rate))
        if self.resonance_score < 0.05:
            self.is_active = False

    def reinforce(self, amount: float = 0.2) -> None:
        """Boost resonance (Attention)."""
        self.resonance_score = min(1.0, self.resonance_score + amount)
        self.is_active = True

    def to_graphiti_node(self) -> Dict[str, Any]:
        """Convert to Graphiti-compatible node dictionary."""
        return {
            "type": "MetacognitiveParticle",
            "name": self.content[:50] + "..." if len(self.content) > 50 else self.content,
            "summary": self.content,
            "created_at": self.timestamp.isoformat(),
            "valid_at": self.timestamp.isoformat(),
            "res_score": self.resonance_score,
            "precision": self.precision,
            "source": self.source_agent,
            "context_id": self.context_id,
            "provenance": self.provenance_ids
        }

    def calculate_free_energy(self) -> float:
        """
        Calculate Variational Free Energy (VFE).
        F = Complexity - Accuracy
        Currently a placeholder using Entropy and Precision as proxies.
        """
        # Complexity ≈ Entropy (Divergence from prior)
        # Accuracy ≈ Precision (Confidence in prediction)
        # High Precision -> Low VFE (Good)
        # High Entropy -> High VFE (Bad/Uncertain)
        return self.entropy - (self.precision / 5.0)
