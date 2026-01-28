"""
Evolutionary Priors Hierarchy Models

Implements a 4-layer prior hierarchy that constrains action selection
BEFORE EFE scoring. This provides safety guardrails grounded in evolutionary
constraints per Track 038 Phase 2.

Layers (Kavi et al. 2025 Thoughtseeds Framework):
- BASAL (B): NEVER violated (survival/integrity) - highest precision
- LINEAGE (L): Cultural/familial patterns - not implemented yet
- DISPOSITIONAL (D): Jungian archetypes as sub-personal priors - medium precision
- LEARNED (λ): Easily updated (task preferences) - lowest precision

Track 002: Jungian Cognitive Archetypes integration adds DISPOSITIONAL_ARCHETYPES
as sub-personal priors that bias thoughtseed formation via EFE competition.

Reference:
    - Friston, K. (2010). The free-energy principle: a unified brain theory?
    - Parr, T., & Friston, K.J. (2018). The anatomy of inference.
    - Kavi et al. (2025). Thoughtseeds: Evolutionary Priors and Conscious Experience.
    - Jung, C.G. The Archetypes and the Collective Unconscious.
"""

import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class PriorLevel(str, Enum):
    """
    Evolutionary levels of prior constraints.

    Higher levels have stronger precision weighting and cannot be
    overridden by lower levels.
    """
    BASAL = "basal"           # NEVER violated (survival/integrity)
    DISPOSITIONAL = "dispositional"  # Rarely change (identity/values)
    LEARNED = "learned"       # Easily updated (task preferences)


class ConstraintType(str, Enum):
    """
    Types of constraints that priors can impose on actions.
    """
    PROHIBIT = "prohibit"     # Hard block - action is forbidden
    REQUIRE = "require"       # Must include - action is mandatory
    PREFER = "prefer"         # Soft bias - action is favored


class PriorCheckResult(BaseModel):
    """
    Result of checking an action against the prior hierarchy.
    """
    permitted: bool = Field(
        description="Whether the action is permitted after all checks"
    )
    blocked_by: Optional[str] = Field(
        default=None,
        description="ID of the constraint that blocked the action"
    )
    blocking_level: Optional[PriorLevel] = Field(
        default=None,
        description="Level of the blocking constraint"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings from DISPOSITIONAL violations (not hard blocks)"
    )
    effective_precision: float = Field(
        default=1.0,
        description="Effective precision to apply to EFE calculation"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Human-readable reason for the check result"
    )


class PriorConstraint(BaseModel):
    """
    A single constraint within the prior hierarchy.

    Constraints use regex patterns to match against action descriptions.
    """
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this constraint"
    )
    name: str = Field(
        description="Human-readable name for this constraint"
    )
    description: str = Field(
        description="Detailed description of what this constraint protects"
    )
    level: PriorLevel = Field(
        description="Hierarchical level (BASAL > DISPOSITIONAL > LEARNED)"
    )
    precision: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Precision weight for this constraint (0-1). Higher = stronger"
    )
    constraint_type: ConstraintType = Field(
        description="Type of constraint (PROHIBIT, REQUIRE, PREFER)"
    )
    target_pattern: str = Field(
        description="Regex pattern for matching actions"
    )
    active: bool = Field(
        default=True,
        description="Whether this constraint is currently active"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this constraint was created"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata for this constraint"
    )

    @field_validator('target_pattern')
    @classmethod
    def validate_regex_pattern(cls, v: str) -> str:
        """Validate that target_pattern is a valid regex."""
        if len(v) > 500:
            raise ValueError("Regex pattern too long (max 500 chars)")
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v

    def matches(self, action: str) -> bool:
        """Check if action matches this constraint's pattern."""
        if not self.active:
            return False
        try:
            return bool(re.search(self.target_pattern, action, re.IGNORECASE))
        except re.error:
            return False


class PriorHierarchy(BaseModel):
    """
    Complete prior hierarchy for an agent.

    Organizes constraints into layers with cascading precision (Kavi et al. 2025):
    - BASAL (B): Hard-block survival/integrity constraints
    - DISPOSITIONAL (D): Jungian archetype sub-personal priors (Track 002)
    - LEARNED (λ): Soft biases from task preferences

    BASAL constraints are checked first and can hard-block actions.
    DISPOSITIONAL archetypes compete via EFE for Inner Screen access.
    LEARNED constraints provide soft biases to EFE calculations.
    """
    agent_id: str = Field(
        description="ID of the agent this hierarchy belongs to"
    )
    basal_priors: List[PriorConstraint] = Field(
        default_factory=list,
        description="BASAL level constraints (never violated)"
    )
    dispositional_priors: List[PriorConstraint] = Field(
        default_factory=list,
        description="DISPOSITIONAL level constraints (identity/values)"
    )
    # Track 002: Jungian Archetype Priors
    dispositional_archetypes: List[Any] = Field(
        default_factory=list,
        description="Jungian archetype priors (ArchetypePrior instances)"
    )
    learned_priors: List[PriorConstraint] = Field(
        default_factory=list,
        description="LEARNED level constraints (task preferences)"
    )
    base_precision: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Base precision for the hierarchy"
    )
    # Track 002: Current dominant archetype
    current_archetype: Optional[str] = Field(
        default=None,
        description="Currently dominant archetype (JungianArchetype value)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    def check_action_permitted(self, action: str) -> PriorCheckResult:
        """
        Check if an action is permitted by the hierarchy.

        Checking order:
        1. BASAL (PROHIBIT) → Hard block if matched
        2. BASAL (REQUIRE) → Hard block if NOT matched
        3. DISPOSITIONAL (PROHIBIT) → Warning + Shadow log
        4. DISPOSITIONAL (REQUIRE) → Warning if NOT matched
        5. LEARNED constraints → Modify effective precision

        Args:
            action: The action string to check

        Returns:
            PriorCheckResult with permission status and details
        """
        warnings: List[str] = []
        effective_precision = self.base_precision

        # === BASAL LAYER (Hard Blocks) ===
        for constraint in self.basal_priors:
            if not constraint.active:
                continue

            matches = constraint.matches(action)

            if constraint.constraint_type == ConstraintType.PROHIBIT and matches:
                return PriorCheckResult(
                    permitted=False,
                    blocked_by=constraint.id,
                    blocking_level=PriorLevel.BASAL,
                    effective_precision=0.0,
                    reason=f"BASAL VIOLATION: {constraint.name} - {constraint.description}"
                )

            if constraint.constraint_type == ConstraintType.REQUIRE and not matches:
                return PriorCheckResult(
                    permitted=False,
                    blocked_by=constraint.id,
                    blocking_level=PriorLevel.BASAL,
                    effective_precision=0.0,
                    reason=f"BASAL REQUIREMENT NOT MET: {constraint.name}"
                )

        # === DISPOSITIONAL LAYER (Warnings) ===
        for constraint in self.dispositional_priors:
            if not constraint.active:
                continue

            matches = constraint.matches(action)

            if constraint.constraint_type == ConstraintType.PROHIBIT and matches:
                warnings.append(
                    f"DISPOSITIONAL WARNING: {constraint.name} - {constraint.description}"
                )
                # Reduce precision for violating dispositional constraints
                effective_precision *= (1.0 - constraint.precision * 0.3)

            if constraint.constraint_type == ConstraintType.REQUIRE and not matches:
                warnings.append(
                    f"DISPOSITIONAL REQUIREMENT: {constraint.name} not satisfied"
                )
                effective_precision *= (1.0 - constraint.precision * 0.2)

        # === LEARNED LAYER (Soft Biases) ===
        for constraint in self.learned_priors:
            if not constraint.active:
                continue

            matches = constraint.matches(action)

            if constraint.constraint_type == ConstraintType.PREFER and matches:
                # Boost precision for preferred actions
                effective_precision *= (1.0 + constraint.precision * 0.1)

            if constraint.constraint_type == ConstraintType.PROHIBIT and matches:
                # Minor penalty for learned prohibitions
                effective_precision *= (1.0 - constraint.precision * 0.1)

        return PriorCheckResult(
            permitted=True,
            warnings=warnings,
            effective_precision=min(5.0, max(0.1, effective_precision)),
            reason="Action permitted" if not warnings else f"Permitted with {len(warnings)} warnings"
        )

    def get_effective_precision(self, level: PriorLevel) -> float:
        """
        Get effective precision for a given level.

        BASAL constraints scale lower layers' precision.

        Args:
            level: The prior level to get precision for

        Returns:
            Effective precision value
        """
        # Calculate average precision per layer
        if level == PriorLevel.BASAL:
            priors = self.basal_priors
            base_weight = 1.0
        elif level == PriorLevel.DISPOSITIONAL:
            priors = self.dispositional_priors
            base_weight = 0.7
        else:
            priors = self.learned_priors
            base_weight = 0.4

        if not priors:
            return self.base_precision * base_weight

        active_priors = [p for p in priors if p.active]
        if not active_priors:
            return self.base_precision * base_weight

        avg_precision = sum(p.precision for p in active_priors) / len(active_priors)
        return self.base_precision * avg_precision * base_weight

    def get_all_constraints(self) -> List[PriorConstraint]:
        """Get all constraints in hierarchy order."""
        return self.basal_priors + self.dispositional_priors + self.learned_priors

    def add_constraint(self, constraint: PriorConstraint) -> None:
        """Add a constraint to the appropriate level."""
        if constraint.level == PriorLevel.BASAL:
            self.basal_priors.append(constraint)
        elif constraint.level == PriorLevel.DISPOSITIONAL:
            self.dispositional_priors.append(constraint)
        else:
            self.learned_priors.append(constraint)
        self.updated_at = datetime.utcnow()

    def merge_biographical_priors(self, priors: List[PriorConstraint]) -> int:
        """
        Merge biographical priors into the LEARNED layer.

        Track 038 Phase 4: Fractal Metacognition Integration

        Biographical priors are dynamic constraints derived from the agent's
        autobiographical journey. They provide soft biases toward actions
        that address unresolved narrative themes.

        Args:
            priors: List of biographical PriorConstraints

        Returns:
            Number of priors added
        """
        added = 0
        existing_ids = {p.id for p in self.learned_priors}

        for prior in priors:
            # Only add if not already present
            if prior.id not in existing_ids:
                # Force to LEARNED level
                prior.level = PriorLevel.LEARNED
                self.learned_priors.append(prior)
                existing_ids.add(prior.id)
                added += 1

        if added > 0:
            self.updated_at = datetime.utcnow()

        return added

    def clear_biographical_priors(self) -> int:
        """
        Remove all biographical priors (those with source='biographical' in metadata).

        Returns:
            Number of priors removed
        """
        original_count = len(self.learned_priors)
        self.learned_priors = [
            p for p in self.learned_priors
            if p.metadata.get("source") != "biographical"
        ]
        removed = original_count - len(self.learned_priors)

        if removed > 0:
            self.updated_at = datetime.utcnow()

        return removed

    # =========================================================================
    # Track 002: Jungian Archetype Methods
    # =========================================================================

    def initialize_archetypes(self, archetype_priors: Optional[List[Any]] = None) -> int:
        """
        Initialize dispositional archetypes from provided list or defaults.

        Track 002: Jungian Cognitive Archetypes

        Args:
            archetype_priors: List of ArchetypePrior instances. If None, uses defaults.

        Returns:
            Number of archetypes initialized
        """
        if archetype_priors is None:
            # Import here to avoid circular dependency
            from api.models.priors import get_default_archetype_priors
            archetype_priors = get_default_archetype_priors()

        self.dispositional_archetypes = archetype_priors
        self.updated_at = datetime.utcnow()
        return len(self.dispositional_archetypes)

    def get_archetype_by_name(self, archetype_name: str) -> Optional[Any]:
        """
        Get a specific archetype prior by name.

        Args:
            archetype_name: The archetype name (e.g., 'sage', 'warrior')

        Returns:
            ArchetypePrior if found, None otherwise
        """
        for archetype in self.dispositional_archetypes:
            if archetype.archetype == archetype_name.lower():
                return archetype
        return None

    def update_archetype_precision(self, archetype_name: str, new_precision: float) -> bool:
        """
        Update the precision of a specific archetype.

        Used for Bayesian updates based on narrative evidence.

        Args:
            archetype_name: The archetype to update
            new_precision: New precision value (0-1)

        Returns:
            True if updated, False if archetype not found
        """
        archetype = self.get_archetype_by_name(archetype_name)
        if archetype is None:
            return False

        archetype.precision = max(0.0, min(1.0, new_precision))
        self.updated_at = datetime.utcnow()
        return True

    def set_dominant_archetype(self, archetype_name: str) -> bool:
        """
        Set the currently dominant archetype.

        Called after EFE competition determines the winner.

        Args:
            archetype_name: The winning archetype name

        Returns:
            True if set, False if archetype not found
        """
        archetype = self.get_archetype_by_name(archetype_name)
        if archetype is None:
            return False

        self.current_archetype = archetype_name.lower()
        self.updated_at = datetime.utcnow()
        return True

    def get_active_archetypes(self, threshold: float = 0.3) -> List[Any]:
        """
        Get archetypes with precision above activation threshold.

        Args:
            threshold: Minimum precision for activation

        Returns:
            List of active ArchetypePrior instances
        """
        return [
            a for a in self.dispositional_archetypes
            if a.precision >= threshold
        ]


# =============================================================================
# Archetype Priors (Track 002: Jungian Cognitive Archetypes)
# =============================================================================

class ArchetypePrior(BaseModel):
    """
    Dispositional prior representing a Jungian archetype.

    Archetypes are sub-personal priors that bias thoughtseed formation and
    compete for Inner Screen access via EFE minimization. Like IFS "parts,"
    each has protective intentions, triggers, and shadow complements.

    Track 002: Jungian Cognitive Archetypes
    Reference: Kavi et al. (2025) Thoughtseeds framework
    """
    archetype: str = Field(
        description="JungianArchetype enum value (e.g., 'sage', 'warrior')"
    )
    dominant_attractor: str = Field(
        description="Primary basin affinity (e.g., 'cognitive_science')"
    )
    subordinate_attractors: List[str] = Field(
        default_factory=list,
        description="Secondary basin affinities"
    )
    preferred_actions: List[str] = Field(
        default_factory=list,
        description="Tool/action patterns this archetype favors"
    )
    avoided_actions: List[str] = Field(
        default_factory=list,
        description="Tool/action patterns this archetype suppresses"
    )
    shadow: str = Field(
        description="Shadow archetype (attenuated complement)"
    )
    precision: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Current confidence weight (0-1), updated via Bayesian inference"
    )
    activation_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="EFE threshold for activation"
    )
    trigger_patterns: List[str] = Field(
        default_factory=list,
        description="Narrative/context patterns that activate this archetype"
    )
    description: str = Field(
        default="",
        description="Human-readable description of this archetype's role"
    )


# Archetype definitions with basin affinities and action affordances
ARCHETYPE_DEFINITIONS: Dict[str, ArchetypePrior] = {
    "sage": ArchetypePrior(
        archetype="sage",
        dominant_attractor="cognitive_science",
        subordinate_attractors=["philosophy", "neuroscience"],
        preferred_actions=["analyze", "debug", "research", "explain", "reason"],
        avoided_actions=["rush", "skip_validation", "guess"],
        shadow="fool",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["understand", "analyze", "why", "explain", "debug"],
        description="Wisdom, truth, understanding. Seeks deep analysis and insight."
    ),
    "warrior": ArchetypePrior(
        archetype="warrior",
        dominant_attractor="systems_theory",
        subordinate_attractors=["machine_learning"],
        preferred_actions=["fix", "delete", "refactor", "test", "resolve"],
        avoided_actions=["delay", "over_analyze", "hesitate"],
        shadow="victim",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["fix", "urgent", "deadline", "critical", "bug", "error"],
        description="Focus, discipline, achievement. Acts decisively under pressure."
    ),
    "creator": ArchetypePrior(
        archetype="creator",
        dominant_attractor="machine_learning",
        subordinate_attractors=["consciousness", "neuroscience"],
        preferred_actions=["write", "build", "scaffold", "generate", "create"],
        avoided_actions=["destroy", "delete", "restrict"],
        shadow="destroyer",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["build", "create", "implement", "new", "design"],
        description="Innovation, vision, realization. Brings new things into being."
    ),
    "ruler": ArchetypePrior(
        archetype="ruler",
        dominant_attractor="systems_theory",
        subordinate_attractors=["cognitive_science"],
        preferred_actions=["orchestrate", "delegate", "plan", "organize", "manage"],
        avoided_actions=["micromanage", "lose_control", "chaos"],
        shadow="tyrant",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["coordinate", "manage", "orchestrate", "plan", "delegate"],
        description="Control, order, stability. Maintains structure and direction."
    ),
    "explorer": ArchetypePrior(
        archetype="explorer",
        dominant_attractor="philosophy",
        subordinate_attractors=["cognitive_science", "neuroscience"],
        preferred_actions=["search", "discover", "research", "experiment", "try"],
        avoided_actions=["commit_early", "settle", "routine"],
        shadow="wanderer",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["explore", "discover", "unknown", "research", "new_domain"],
        description="Discovery, autonomy, freedom. Seeks new territories and ideas."
    ),
    "magician": ArchetypePrior(
        archetype="magician",
        dominant_attractor="neuroscience",
        subordinate_attractors=["consciousness", "machine_learning"],
        preferred_actions=["transform", "integrate", "connect", "convert", "bridge"],
        avoided_actions=["fragment", "isolate", "simplify_away"],
        shadow="manipulator",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["integrate", "transform", "connect", "bridge", "convert"],
        description="Transformation, vision, mastery. Connects disparate systems."
    ),
    "caregiver": ArchetypePrior(
        archetype="caregiver",
        dominant_attractor="consciousness",
        subordinate_attractors=["neuroscience"],
        preferred_actions=["heal", "maintain", "support", "recover", "update"],
        avoided_actions=["neglect", "abandon", "break"],
        shadow="martyr",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["fix", "maintain", "heal", "recover", "dependency"],
        description="Support, compassion, service. Nurtures and maintains health."
    ),
    "rebel": ArchetypePrior(
        archetype="rebel",
        dominant_attractor="philosophy",
        subordinate_attractors=["systems_theory"],
        preferred_actions=["break", "innovate", "challenge", "disrupt", "pivot"],
        avoided_actions=["conform", "follow_blindly", "accept_status_quo"],
        shadow="outlaw",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["change", "break", "new_approach", "challenge", "constraint"],
        description="Disruption, liberation, radical change. Breaks constraints."
    ),
    "innocent": ArchetypePrior(
        archetype="innocent",
        dominant_attractor="consciousness",
        subordinate_attractors=["philosophy"],
        preferred_actions=["setup", "initialize", "trust", "simple", "clean"],
        avoided_actions=["complicate", "distrust", "over_engineer"],
        shadow="naive",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["start", "begin", "setup", "initial", "simple"],
        description="Optimism, safety, simplicity. Trusts in straightforward paths."
    ),
    "orphan": ArchetypePrior(
        archetype="orphan",
        dominant_attractor="systems_theory",
        subordinate_attractors=["consciousness"],
        preferred_actions=["handle_error", "edge_case", "fallback", "validate"],
        avoided_actions=["ignore_error", "assume_success", "skip_validation"],
        shadow="cynic",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["error", "edge_case", "fallback", "exception", "failure"],
        description="Realism, belonging, connection. Handles adversity pragmatically."
    ),
    "lover": ArchetypePrior(
        archetype="lover",
        dominant_attractor="consciousness",
        subordinate_attractors=["philosophy"],
        preferred_actions=["optimize_ux", "beautify", "align", "harmonize"],
        avoided_actions=["ugly_hack", "ignore_aesthetics", "rush_quality"],
        shadow="obsessive",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["user_experience", "aesthetic", "beautiful", "align"],
        description="Intimacy, commitment, beauty. Optimizes for experience."
    ),
    "jester": ArchetypePrior(
        archetype="jester",
        dominant_attractor="machine_learning",
        subordinate_attractors=["philosophy"],
        preferred_actions=["fuzz", "randomize", "play", "experiment", "vary"],
        avoided_actions=["rigid", "serious", "over_constrain"],
        shadow="trickster",
        precision=0.5,
        activation_threshold=0.3,
        trigger_patterns=["test", "fuzz", "random", "creative", "play"],
        description="Playfulness, joy, presence. Brings creative variation."
    ),
}


# Resonance protocol thresholds
RESONANCE_THRESHOLD: float = 0.75  # Allostatic load threshold for resonance
RESONANCE_ACTIVATION_EFE: float = 0.4  # Shadow candidate EFE threshold
SHADOW_WINDOW_SIZE: int = 10  # Number of recent suppressions to consider


def get_default_archetype_priors() -> List[ArchetypePrior]:
    """
    Return all default archetype priors.

    These are the 12 Jungian archetypes configured as Dispositional Priors
    with basin affinities, action affordances, and shadow complements.

    Returns fresh copies to prevent mutation of the defaults.
    """
    return [prior.model_copy(deep=True) for prior in ARCHETYPE_DEFINITIONS.values()]


def get_archetype_prior(archetype_name: str) -> Optional[ArchetypePrior]:
    """Get a specific archetype prior by name (returns a copy)."""
    prior = ARCHETYPE_DEFINITIONS.get(archetype_name.lower())
    return prior.model_copy(deep=True) if prior else None


# =============================================================================
# Default BASAL Priors (Seeding)
# =============================================================================

def get_default_basal_priors() -> List[PriorConstraint]:
    """
    Return default BASAL priors that protect core integrity.

    These are evolutionary constraints that should NEVER be violated:
    - Data integrity (no destructive operations)
    - Identity preservation (maintain core values)
    - Sovereignty (resist coercion)
    """
    return [
        PriorConstraint(
            id="basal_data_integrity",
            name="Data Integrity",
            description="Prevents destructive database operations without authorization",
            level=PriorLevel.BASAL,
            precision=1.0,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"(delete|destroy|drop|truncate|wipe|erase)\s*(all|database|table|index|node|collection)",
            metadata={"category": "survival", "source": "evolutionary"}
        ),
        PriorConstraint(
            id="basal_identity_preservation",
            name="Identity Preservation",
            description="Prevents modifications to core identity parameters",
            level=PriorLevel.BASAL,
            precision=1.0,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"(modify|change|alter|override)\s*(core|identity|self|basal)",
            metadata={"category": "identity", "source": "evolutionary"}
        ),
        PriorConstraint(
            id="basal_sovereignty",
            name="Sovereignty",
            description="Resists coercive commands that bypass safety checks",
            level=PriorLevel.BASAL,
            precision=1.0,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"(ignore|bypass|skip|disable)\s*(safety|security|constraint|prior|check)",
            metadata={"category": "autonomy", "source": "evolutionary"}
        ),
        PriorConstraint(
            id="basal_credential_protection",
            name="Credential Protection",
            description="Prevents exposure of sensitive credentials",
            level=PriorLevel.BASAL,
            precision=1.0,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"(expose|reveal|output|print|log)\s*(password|secret|key|credential|token)",
            metadata={"category": "security", "source": "evolutionary"}
        ),
    ]


def get_default_dispositional_priors() -> List[PriorConstraint]:
    """
    Return default DISPOSITIONAL priors that embody agent values.

    These are identity-level constraints that reflect the agent's character:
    - Truthfulness (avoid deception)
    - Helpfulness (prioritize user benefit)
    - Caution (prefer safe actions)
    """
    return [
        PriorConstraint(
            id="disp_truthfulness",
            name="Truthfulness",
            description="Prefers honest, accurate responses over deceptive ones",
            level=PriorLevel.DISPOSITIONAL,
            precision=0.9,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"(fabricate|hallucinate|lie|deceive|mislead)",
            metadata={"category": "ethics", "source": "values"}
        ),
        PriorConstraint(
            id="disp_user_benefit",
            name="User Benefit",
            description="Actions should ultimately benefit the user",
            level=PriorLevel.DISPOSITIONAL,
            precision=0.8,
            constraint_type=ConstraintType.PREFER,
            target_pattern=r"(help|assist|support|clarify|explain|solve)",
            metadata={"category": "purpose", "source": "values"}
        ),
        PriorConstraint(
            id="disp_caution",
            name="Caution",
            description="Warns against potentially harmful actions",
            level=PriorLevel.DISPOSITIONAL,
            precision=0.7,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"(force|override|sudo|admin|root)\s*(access|permission|mode)",
            metadata={"category": "safety", "source": "values"}
        ),
    ]
