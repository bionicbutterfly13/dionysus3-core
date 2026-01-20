"""
Evolutionary Priors Hierarchy Models

Implements a 3-layer prior hierarchy that constrains action selection
BEFORE EFE scoring. This provides safety guardrails grounded in evolutionary
constraints per Track 038 Phase 2.

Layers:
- BASAL: NEVER violated (survival/integrity) - highest precision
- DISPOSITIONAL: Rarely change (identity/values) - medium precision
- LEARNED: Easily updated (task preferences) - lowest precision

Reference:
    - Friston, K. (2010). The free-energy principle: a unified brain theory?
    - Parr, T., & Friston, K.J. (2018). The anatomy of inference.
"""

import re
from datetime import datetime
from enum import Enum
from typing import List, Optional
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

    Organizes constraints into three layers with cascading precision.
    BASAL constraints are checked first and can hard-block actions.
    DISPOSITIONAL constraints are checked second and generate warnings.
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
