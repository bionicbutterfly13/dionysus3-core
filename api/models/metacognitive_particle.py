"""
Metacognitive Particle Models for Knowledge Graph Entities.

Feature: 038-thoughtseeds-framework
Sources:
- Sandved-Smith & Da Costa (2024): Metacognitive particles, mental action and the sense of agency
- Seragnoli et al. (2025): Metacognitive Feelings of Epistemic Gain

Implements Bayesian mechanics framework for metacognition:
- Nested Markov blankets (eta, b=(s,a), mu)
- Passive vs Active metacognitive particles
- Mental actions via higher-level active paths
- Sense of agency as D_KL measure
- Metacognitive feelings and epistemic gain
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("dionysus.metacognitive_particle")

# ---------------------------------------------------------------------------
# Configuration (Feature 040)
# ---------------------------------------------------------------------------

MAX_NESTING_DEPTH = int(os.getenv("METACOGNITIVE_MAX_DEPTH", "5"))


# ---------------------------------------------------------------------------
# Exceptions (Feature 040)
# ---------------------------------------------------------------------------


class CognitiveCoreViolation(Exception):
    """
    Raised when attempting to exceed the maximum nesting depth.

    Per the paper: "I can never conceive what it is like to be me"
    The innermost cognitive core μ^N cannot be the target of higher beliefs.
    """
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ParticleType(str, Enum):
    """
    Type of metacognitive particle from Sandved-Smith & Da Costa (2024).

    Classification based on Markov blanket structure:
    - COGNITIVE: Has belief mapping μ → Q_μ(η), basic level
    - PASSIVE: Beliefs about subset of parameters via blanket (no direct control)
    - ACTIVE: Higher-level internal paths with internal Markov blanket
    - STRANGE: Active paths hidden from internal paths (a¹ does NOT influence μ¹)
    - NESTED: Particle within particle
    - MULTIPLY_NESTED: N levels of nesting

    Feature 040 aliases for API compatibility:
    - PASSIVE_METACOGNITIVE = PASSIVE
    - ACTIVE_METACOGNITIVE = ACTIVE
    - STRANGE_METACOGNITIVE = STRANGE
    - NESTED_N_LEVEL = MULTIPLY_NESTED
    """
    # Original types from Spec 038
    PASSIVE = "passive"
    ACTIVE = "active"
    STRANGE = "strange"
    NESTED = "nested"
    MULTIPLY_NESTED = "multiply_nested"

    # Feature 040 additions
    COGNITIVE = "cognitive"  # Base cognitive particle with beliefs about external
    PASSIVE_METACOGNITIVE = "passive_metacognitive"  # Alias for PASSIVE
    ACTIVE_METACOGNITIVE = "active_metacognitive"    # Alias for ACTIVE
    STRANGE_METACOGNITIVE = "strange_metacognitive"  # Alias for STRANGE
    NESTED_N_LEVEL = "nested_n_level"                # Alias for MULTIPLY_NESTED


class BeliefType(str, Enum):
    """Level of metacognitive belief."""
    FIRST_ORDER = "first_order"    # Beliefs about world (eta)
    SECOND_ORDER = "second_order"  # Beliefs about beliefs (mu^(1))
    HIGHER_ORDER = "higher_order"  # N-th level beliefs


class BeliefTarget(str, Enum):
    """What the belief is about."""
    EXTERNAL_PATHS = "external_paths"  # eta
    INTERNAL_PATHS = "internal_paths"  # mu^(n-1)
    ACTIVE_PATHS = "active_paths"      # a^(n)
    JOINT = "joint"                    # (mu, a) jointly


class MentalActionType(str, Enum):
    """Type of mental action from active metacognition."""
    PRECISION_MODULATION = "precision_modulation"  # Modulate posterior precision
    ATTENTION_CONTROL = "attention_control"        # Direct attention
    BELIEF_REVISION = "belief_revision"            # Update belief parameters
    POLICY_SELECTION = "policy_selection"          # Select action policies
    # T005: Additional mental action types per spec
    PRECISION_DELTA = "precision_delta"            # Change precision by delta
    SET_PRECISION = "set_precision"                # Set absolute precision
    FOCUS_TARGET = "focus_target"                  # Set attention focus target
    SPOTLIGHT_PRECISION = "spotlight_precision"    # Precision of attentional spotlight


class ModulatedParameter(str, Enum):
    """Which sufficient statistic is modulated by mental action."""
    MEAN = "mean"            # m(mu)
    PRECISION = "precision"  # Pi(mu) - inverse covariance
    COVARIANCE = "covariance"
    POLICY_PRIOR = "policy_prior"


class FeelingType(str, Enum):
    """Types of metacognitive feelings from Seragnoli et al. (2025)."""
    TIP_OF_TONGUE = "tip_of_tongue"  # Feeling of almost knowing
    AHA_EUREKA = "aha_eureka"        # Insight moment
    CURIOSITY = "curiosity"          # Drive to explore
    CONFUSION = "confusion"          # Uncertainty feeling
    FLUENCY = "fluency"              # Ease of processing
    DIFFICULTY = "difficulty"        # Processing strain
    FAMILIARITY = "familiarity"      # Recognition feeling
    NOVELTY = "novelty"              # Newness detection


class FeelingCategory(str, Enum):
    """When in cognitive action cycle feeling arises."""
    GOAL_RELATED = "goal_related"        # During goal setting
    PROCESS_RELATED = "process_related"  # During cognitive processing
    OUTCOME_RELATED = "outcome_related"  # After action completion


class EpistemicGainType(str, Enum):
    """Types of epistemic gain outcomes."""
    INSIGHT = "insight"          # Novel understanding
    RESOLUTION = "resolution"    # Ambiguity resolved
    VERIFICATION = "verification"  # Hypothesis confirmed
    DISCOVERY = "discovery"      # New knowledge acquired


class CognitiveActionPhase(str, Enum):
    """Phases in cognitive action cycle."""
    HYPOTHESIS = "hypothesis"      # Forming prediction
    EXPLORATION = "exploration"    # Gathering information
    VERIFICATION = "verification"  # Testing prediction
    APPRAISAL = "appraisal"        # Evaluating outcome


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


class MetacognitiveParticle(BaseModel):
    """
    A cognitive particle possessing beliefs about its own beliefs.
    
    Central entity from Sandved-Smith & Da Costa (2024).
    
    Key properties:
    - particle_type: passive, active, strange, nested, multiply_nested
    - metacognition_depth: N levels of nested metacognition
    - has_sense_of_agency: can form belief about a^(1) depending on mu^(1)
    - cognitive_core_level: innermost mu^(N) that cannot be further targeted
    
    Equations:
    - Passive: Q^(2)_{mu^(2)}(mu^(1)) via sensory paths only
    - Active: Q_{mu^(2)}(mu^(1)) = P(mu^(1) | s^(2), a^(2))
    - Agency: D_KL[Q(mu^(1), a^(1)) | Q(mu^(1))Q(a^(1))]
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(description="Human-readable particle name")
    particle_type: ParticleType = Field(
        default=ParticleType.PASSIVE,
        description="Passive/Active/Strange/Nested classification"
    )
    metacognition_depth: int = Field(
        default=1,
        ge=1,
        description="N levels of nested metacognition"
    )
    has_sense_of_agency: bool = Field(
        default=False,
        description="Can form belief about causal dependency of a^(1) on mu^(1)"
    )
    cognitive_core_level: Optional[int] = Field(
        default=None,
        description="Innermost level mu^(N) not target of further beliefs"
    )
    
    # Associated blanket and beliefs
    blanket_id: Optional[str] = Field(default=None, description="Primary Markov blanket ID")
    belief_ids: List[str] = Field(default_factory=list, description="Associated belief IDs")
    
    # Metadata
    source_paper: str = Field(default="sandved-smith-2024")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "particle-001",
                "name": "Active Metacognitive Agent",
                "particle_type": "active",
                "metacognition_depth": 2,
                "has_sense_of_agency": True,
                "cognitive_core_level": 2
            }
        }
    }


class MetacognitiveBelief(BaseModel):
    """
    Belief parameterized by internal paths about external or lower-level paths.
    
    Forms the core of metacognition: beliefs about beliefs.
    
    Mathematical form:
    - First-order: Q_{mu^(1)}(eta) = P(eta | s^(1), a^(1))
    - Second-order: Q_{mu^(2)}(mu^(1)) = P(mu^(1) | s^(2), a^(2))
    - Higher-order: Q_{mu^(n)}(mu^(n-1))
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    belief_type: BeliefType = Field(description="Order of belief")
    level: int = Field(ge=1, description="Level in hierarchy (1 = first-order)")
    target_type: BeliefTarget = Field(description="What is being believed about")
    
    parameterizing_paths: str = Field(
        description="mu^(n) - internal paths that parameterize this belief"
    )
    target_paths: str = Field(
        description="What is being believed about (eta, mu^(n-1), a, or joint)"
    )
    posterior_form: Optional[str] = Field(
        default=None,
        description="Mathematical form: Q_{mu^(n)}(target)"
    )
    is_comprehensive: bool = Field(
        default=False,
        description="True if beliefs about ALL sufficient statistics of lower-level"
    )
    
    # Link to particle
    particle_id: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MentalAction(BaseModel):
    """
    Higher-level active paths a^(2) that modulate lower-level belief parameters.
    
    From active metacognition: the ability to control one's own cognitive processes.
    
    Examples:
    - Precision modulation: attention as a^(2) -> Pi(mu^(1))
    - Belief revision: updating generative model parameters
    - Policy selection: choosing action policies via EFE minimization
    
    Equation: a^(2) -> mu^(1) via f_{mu^(1)}(s^(1), mu^(1), b^(2))
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: MentalActionType = Field(description="Type of mental action")
    
    source_level: int = Field(
        ge=1,
        description="Level of internal paths initiating action (n+1)"
    )
    target_level: int = Field(
        ge=0,
        description="Level of internal paths being modulated (n)"
    )
    modulated_parameter: ModulatedParameter = Field(
        description="Which sufficient statistic is being modulated"
    )
    
    expected_free_energy_reduction: Optional[float] = Field(
        default=None,
        description="EFE minimization achieved by this mental action"
    )
    
    # Links
    particle_id: Optional[str] = Field(default=None)
    target_blanket_id: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('target_level')
    @classmethod
    def target_below_source(cls, v, info):
        if 'source_level' in info.data and v >= info.data['source_level']:
            raise ValueError("target_level must be below source_level")
        return v


class SenseOfAgency(BaseModel):
    """
    Joint probability distribution capturing action-internal coupling.
    
    The sense of agency emerges from metacognitive beliefs about the relationship
    between internal paths mu^(1) and active paths a^(1).
    
    Equations:
    - Joint belief: Q_{mu^(2)}(mu^(1), a^(1)) = P(mu^(1) | s^(2), a^(2)) * P(a^(1) | s^(1))
    - Agency strength: D_KL[Q(mu^(1), a^(1)) | Q(mu^(1))Q(a^(1))]
    - No agency: when Q(mu^(1), a^(1)) = Q(mu^(1)) * Q(a^(1))
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    particle_id: str = Field(description="Associated metacognitive particle")
    
    joint_distribution: Optional[str] = Field(
        default=None,
        description="Q_{mu^(2)}(mu^(1), a^(1)) representation"
    )
    agency_strength: float = Field(
        default=0.0,
        ge=0.0,
        description="D_KL measure - mutual information between mu^(1) and a^(1)"
    )
    no_agency_condition: bool = Field(
        default=False,
        description="True when internal and active paths are independent"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CognitiveCore(BaseModel):
    """
    Innermost internal paths mu^(N) that cannot be target of further beliefs.
    
    Represents the fundamental limitation on self-representation:
    "I can never conceive of what it is like to be me, because that would require
    the number of recursions I can physically entertain, plus one."
    
    Despite nested separation, the cognitive core's beliefs capture all information
    on lower blankets via the unified belief product:
    Q_{mu^(N)}(eta, mu^(1), ..., mu^(N-1)) = Q_{mu^(1)}(eta) * prod_n Q_{mu^(n)}(mu^(n-1))
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    particle_id: str = Field(description="Associated metacognitive particle")
    
    max_recursion_level: int = Field(
        ge=1,
        description="N - maximum level of metacognitive recursion"
    )
    complexity_bound: Optional[float] = Field(
        default=None,
        description="Free energy complexity cost limiting further nesting"
    )
    beliefs_encoded: Optional[str] = Field(
        default=None,
        description="Q_{mu^(N)}(eta, mu^(1), ..., mu^(N-1)) - unified experience"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Metacognitive Feelings (Seragnoli et al. 2025)
# ---------------------------------------------------------------------------


class MetacognitiveFeeling(BaseModel):
    """
    Phenomenal experience arising from cognitive action outcomes.
    
    From Seragnoli et al. (2025) - procedural metacognition produces feelings
    that guide cognition:
    - Goal-related: curiosity, interest
    - Process-related: fluency, difficulty, tip-of-tongue
    - Outcome-related: aha/eureka, satisfaction, confusion
    
    Key properties:
    - valence: affective quality (-1 to +1)
    - epistemic_value: information gain associated
    - noetic_quality: sense of direct knowing (high in mystical experiences)
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    feeling_type: FeelingType = Field(description="Type of metacognitive feeling")
    feeling_category: FeelingCategory = Field(
        description="When in cognitive action cycle this arises"
    )
    
    valence: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Affective valence (-1 negative, +1 positive)"
    )
    epistemic_value: float = Field(
        default=0.0,
        ge=0.0,
        description="Information gain associated with this feeling"
    )
    noetic_quality: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Sense of direct knowing/insight (high in mystical experiences)"
    )
    
    # Link to cognitive action
    cognitive_action_id: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EpistemicGain(BaseModel):
    """
    Outcome-related feeling from successful cognitive action.
    
    The 'Aha!' or 'Eureka' moment representing successful epistemic update.
    
    Models considered:
    - REBUS: Relaxed Beliefs Under Psychedelics - flattened precision landscape
    - FIBUS: False Insights and Beliefs Under Psychedelics - high noetic but non-veridical
    
    Key properties:
    - surprise_reduction: VFE/prediction error reduction
    - belief_confidence_change: posterior precision increase
    - noetic_intensity: strength of 'knowing' quality
    - is_veridical: true insight vs false insight
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    cognitive_action_id: Optional[str] = Field(default=None)
    
    gain_type: EpistemicGainType = Field(description="Type of epistemic gain")
    
    surprise_reduction: float = Field(
        default=0.0,
        description="Reduction in VFE / prediction error"
    )
    belief_confidence_change: float = Field(
        default=0.0,
        description="Change in posterior precision"
    )
    noetic_intensity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Intensity of 'knowing' quality"
    )
    is_veridical: bool = Field(
        default=True,
        description="True insight vs false insight (FIBUS consideration)"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CognitiveAction(BaseModel):
    """
    Deliberate cognitive operation in procedural metacognition.
    
    Phases: hypothesis -> exploration -> verification -> appraisal
    
    Procedural metacognition involves:
    - Monitoring: tracking cognitive process state
    - Control: adjusting cognitive strategies
    
    Each phase associated with different metacognitive feelings:
    - Hypothesis: curiosity
    - Exploration: fluency/difficulty
    - Verification: tip-of-tongue
    - Appraisal: aha/confusion
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    action_phase: CognitiveActionPhase = Field(description="Phase in cognitive cycle")
    
    monitoring_active: bool = Field(
        default=True,
        description="Whether metacognitive monitoring is engaged"
    )
    control_engaged: bool = Field(
        default=False,
        description="Whether metacognitive control is engaged"
    )
    
    goal_state: Optional[str] = Field(
        default=None,
        description="Target epistemic/pragmatic goal"
    )
    current_feeling: Optional[FeelingType] = Field(
        default=None,
        description="Current metacognitive feeling"
    )
    
    expected_epistemic_value: float = Field(
        default=0.0,
        description="Expected information gain from this action"
    )
    expected_pragmatic_value: float = Field(
        default=0.0,
        description="Expected goal fulfillment from this action"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Attractor Basin for Training
# ---------------------------------------------------------------------------


class MetacognitiveAttractorBasin(BaseModel):
    """
    Stable attentional/cognitive state in free energy landscape.
    
    Training target for Dionysus attractor basin system.
    Categories derived from paper synthesis:
    - metacognition: beliefs about beliefs
    - agency: action-internal coupling
    - epistemic: learning/insight dynamics
    - affect: valence of cognitive outcomes
    - consciousness: unified experience
    - bayesian_mechanics: formal framework
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    basin_name: str = Field(description="Human-readable basin name")
    basin_category: str = Field(
        description="metacognition|agency|epistemic|affect|consciousness|bayesian_mechanics"
    )
    
    depth: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Binding energy / stability of attractor"
    )
    width: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Volume of state space captured"
    )
    
    core_concepts: List[str] = Field(
        default_factory=list,
        description="Central concepts defining this basin"
    )
    related_basins: List[str] = Field(
        default_factory=list,
        description="Names of related attractor basins"
    )
    key_equations: List[str] = Field(
        default_factory=list,
        description="Key mathematical equations for this basin"
    )
    
    transition_barriers: Dict[str, float] = Field(
        default_factory=dict,
        description="Energy barriers to neighboring attractors"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------------


def create_metacognition_basin() -> MetacognitiveAttractorBasin:
    """Create the Metacognition attractor basin with core concepts."""
    return MetacognitiveAttractorBasin(
        basin_name="Metacognition",
        basin_category="metacognition",
        depth=0.8,
        width=0.7,
        core_concepts=[
            "beliefs_about_beliefs",
            "metacognitive_particle",
            "passive_metacognition",
            "active_metacognition",
            "metacognitive_monitoring",
            "metacognitive_control",
            "higher_order_thought",
            "self_representation",
            "introspection",
            "meta_awareness"
        ],
        related_basins=["consciousness", "agency", "epistemic"],
        key_equations=[
            "Q^(2)_{mu^(2)}(mu^(1))",
            "mu^(2) -> Q_{mu^(2)}(mu^(1))"
        ],
        transition_barriers={
            "consciousness": 0.3,
            "agency": 0.2,
            "epistemic": 0.25
        }
    )


def create_agency_basin() -> MetacognitiveAttractorBasin:
    """Create the Agency attractor basin with core concepts."""
    return MetacognitiveAttractorBasin(
        basin_name="Agency",
        basin_category="agency",
        depth=0.75,
        width=0.6,
        core_concepts=[
            "sense_of_agency",
            "action_internal_coupling",
            "mental_action",
            "active_paths",
            "strange_particle",
            "empowerment",
            "control",
            "voluntary_action",
            "self_as_agent"
        ],
        related_basins=["metacognition", "consciousness"],
        key_equations=[
            "D_KL[Q(mu^(1), a^(1)) | Q(mu^(1))Q(a^(1))]",
            "a^(2) -> mu^(1)"
        ],
        transition_barriers={
            "metacognition": 0.2,
            "consciousness": 0.35
        }
    )


def create_epistemic_basin() -> MetacognitiveAttractorBasin:
    """Create the Epistemic attractor basin with core concepts."""
    return MetacognitiveAttractorBasin(
        basin_name="Epistemic",
        basin_category="epistemic",
        depth=0.7,
        width=0.65,
        core_concepts=[
            "epistemic_gain",
            "insight",
            "aha_moment",
            "eureka",
            "learning",
            "information_gain",
            "surprise_reduction",
            "curiosity",
            "exploration",
            "hypothesis_verification"
        ],
        related_basins=["metacognition", "affect"],
        key_equations=[
            "expected_information_gain",
            "VFE_reduction",
            "posterior_precision_increase"
        ],
        transition_barriers={
            "metacognition": 0.25,
            "affect": 0.15
        }
    )


def create_affect_basin() -> MetacognitiveAttractorBasin:
    """Create the Affect attractor basin with core concepts."""
    return MetacognitiveAttractorBasin(
        basin_name="Affect",
        basin_category="affect",
        depth=0.65,
        width=0.7,
        core_concepts=[
            "metacognitive_feeling",
            "valence",
            "tip_of_tongue",
            "confusion",
            "fluency",
            "difficulty",
            "noetic_quality",
            "feeling_of_knowing",
            "cognitive_emotion"
        ],
        related_basins=["epistemic", "metacognition"],
        key_equations=[
            "valence = f(surprise_reduction)",
            "noetic_intensity"
        ],
        transition_barriers={
            "epistemic": 0.15,
            "metacognition": 0.3
        }
    )


def create_consciousness_basin() -> MetacognitiveAttractorBasin:
    """Create the Consciousness attractor basin with core concepts."""
    return MetacognitiveAttractorBasin(
        basin_name="Consciousness",
        basin_category="consciousness",
        depth=0.9,
        width=0.5,
        core_concepts=[
            "cognitive_core",
            "unified_experience",
            "inner_screen",
            "phenomenal_experience",
            "self_model",
            "markov_blanket",
            "irreducible_blanket",
            "non_dual_experience",
            "subject_object_separation"
        ],
        related_basins=["metacognition", "agency"],
        key_equations=[
            "Q_{mu^(N)}(eta, mu^(1), ..., mu^(N-1))",
            "unified_belief_product"
        ],
        transition_barriers={
            "metacognition": 0.3,
            "agency": 0.35
        }
    )


def create_all_training_basins() -> List[MetacognitiveAttractorBasin]:
    """Create all attractor basins for training targets."""
    return [
        create_metacognition_basin(),
        create_agency_basin(),
        create_epistemic_basin(),
        create_affect_basin(),
        create_consciousness_basin()
    ]


# ---------------------------------------------------------------------------
# Feature 040: Classification API Models
# ---------------------------------------------------------------------------


class ClassificationResult(BaseModel):
    """
    Result of particle classification from ParticleClassifier service.

    Contains the classification outcome with confidence score and metadata.
    Used as response model for POST /api/v1/metacognition/classify endpoint.
    """
    particle_id: str = Field(description="UUID of the classified particle")
    particle_type: ParticleType = Field(description="Classification result")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    level: int = Field(ge=0, description="Nesting level detected")
    has_agency: bool = Field(description="Whether particle has sense of agency")
    classified_at: datetime = Field(default_factory=datetime.utcnow)


def enforce_cognitive_core(level: int) -> None:
    """
    Enforce the cognitive core nesting limit.

    Args:
        level: The nesting level to validate

    Raises:
        CognitiveCoreViolation: If level exceeds MAX_NESTING_DEPTH
    """
    if level > MAX_NESTING_DEPTH:
        raise CognitiveCoreViolation(
            f"Cannot create metacognitive level {level}. "
            f"Cognitive core reached at level {MAX_NESTING_DEPTH}."
        )
