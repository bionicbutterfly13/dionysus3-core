"""
Pattern Evolution Tracker Service
Feature: 008-mosaeic-memory

Tracks pattern evolution and validates genuine learning.
Ported from infomarket/src/consciousness/pattern_evolution.py

This service manages how knowledge patterns evolve over time,
ensuring patterns are validated before being treated as learned.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from api.models.mosaeic import (
    BasinInfluenceType,
    KnowledgePattern,
    CognitionPattern,
    PatternType,
)


@dataclass
class PatternEvolutionConfig:
    """Configuration for pattern evolution validation."""
    min_success_rate: float = 0.7
    min_projects: int = 2
    min_usage_count: int = 3
    evolution_regression_factor: float = 0.8  # Slight regression when evolving


class PatternEvolutionTracker:
    """
    Tracks pattern evolution and validates genuine learning.

    Key responsibilities:
    - Create and manage knowledge patterns
    - Validate patterns meet learning thresholds
    - Evolve patterns from base patterns
    - Track evolution history
    """

    def __init__(self, config: PatternEvolutionConfig | None = None):
        self.config = config or PatternEvolutionConfig()
        self.patterns: dict[str, KnowledgePattern] = {}
        self.cognition_patterns: dict[str, CognitionPattern] = {}
        self.evolution_events: list[dict[str, Any]] = []

    def create_pattern(
        self,
        pattern_id: str | None = None,
        success_rate: float = 0.0,
        projects_used: list[str] | None = None,
        generalized: bool = False,
    ) -> KnowledgePattern:
        """Create a new knowledge pattern."""
        pattern = KnowledgePattern(
            pattern_id=pattern_id or str(uuid4()),
            success_rate=success_rate,
            projects_used=projects_used or [],
            generalized=generalized,
        )
        self.patterns[pattern.pattern_id] = pattern
        return pattern

    def get_pattern(self, pattern_id: str) -> KnowledgePattern | None:
        """Retrieve a pattern by ID."""
        return self.patterns.get(pattern_id)

    def validate_pattern(self, pattern: KnowledgePattern) -> bool:
        """
        Validate that a pattern shows genuine learning.

        A pattern is validated when:
        1. It has been generalized
        2. Its success rate meets the minimum threshold
        3. It has been used in enough projects
        """
        return pattern.is_validated(
            min_success_rate=self.config.min_success_rate,
            min_projects=self.config.min_projects,
        )

    def evolve_pattern(
        self,
        base_pattern_id: str,
        new_pattern_id: str | None = None,
    ) -> KnowledgePattern:
        """
        Create an evolved pattern from a base pattern.

        The evolved pattern inherits from the base but starts with
        a slight regression in success rate (learning curve).
        """
        base_pattern = self.patterns.get(base_pattern_id)
        if not base_pattern:
            raise ValueError(f"Base pattern {base_pattern_id} not found")

        new_id = new_pattern_id or str(uuid4())

        evolved_pattern = KnowledgePattern(
            pattern_id=new_id,
            evolved_from=base_pattern_id,
            # Slight regression initially when evolving
            success_rate=base_pattern.success_rate * self.config.evolution_regression_factor,
            projects_used=[],
            generalized=False,
        )

        self.patterns[new_id] = evolved_pattern

        # Track evolution event
        self.evolution_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "base_pattern_id": base_pattern_id,
            "evolved_pattern_id": new_id,
            "initial_success_rate": evolved_pattern.success_rate,
        })

        return evolved_pattern

    def update_pattern_success(
        self,
        pattern_id: str,
        success: bool,
        project_id: str | None = None,
    ) -> KnowledgePattern:
        """
        Update a pattern's success metrics.

        Args:
            pattern_id: Pattern to update
            success: Whether the pattern was successful
            project_id: Optional project where pattern was used
        """
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")

        # Update success rate (exponential moving average)
        alpha = 0.2  # Learning rate
        new_value = 1.0 if success else 0.0
        pattern.success_rate = (
            alpha * new_value + (1 - alpha) * pattern.success_rate
        )

        # Track project usage
        if project_id and project_id not in pattern.projects_used:
            pattern.projects_used.append(project_id)

        # Check if pattern should be marked as generalized
        if len(pattern.projects_used) >= self.config.min_projects:
            pattern.generalized = True

        return pattern

    # =========================================================================
    # CognitionPattern Management (from Dionysus-2.0)
    # =========================================================================

    def create_cognition_pattern(
        self,
        pattern_name: str,
        description: str,
        pattern_type: PatternType = PatternType.EMERGENT,
        success_rate: float = 0.5,
        confidence: float = 0.5,
        reliability_score: float = 0.5,
    ) -> CognitionPattern:
        """
        Create a new cognition pattern.
        Ported from Dionysus-2.0/cognition_base.py
        """
        pattern = CognitionPattern(
            pattern_name=pattern_name,
            description=description,
            pattern_type=pattern_type,
            success_rate=success_rate,
            confidence=confidence,
            reliability_score=reliability_score,
        )
        self.cognition_patterns[pattern.pattern_id] = pattern
        return pattern

    def get_cognition_pattern(self, pattern_id: str) -> CognitionPattern | None:
        """Retrieve a cognition pattern by ID."""
        return self.cognition_patterns.get(pattern_id)

    def update_cognition_pattern(
        self,
        pattern_id: str,
        success: bool,
        consciousness_contribution: float | None = None,
    ) -> CognitionPattern:
        """Update a cognition pattern after use."""
        pattern = self.cognition_patterns.get(pattern_id)
        if not pattern:
            raise ValueError(f"CognitionPattern {pattern_id} not found")

        # Update usage metrics
        pattern.usage_count += 1
        pattern.last_used = datetime.utcnow()

        # Update success rate
        alpha = 0.2
        new_value = 1.0 if success else 0.0
        pattern.success_rate = (
            alpha * new_value + (1 - alpha) * pattern.success_rate
        )

        # Update confidence based on reliability trend
        if pattern.usage_count > 5:
            pattern.confidence = (
                pattern.success_rate * 0.6 +
                pattern.reliability_score * 0.4
            )

        # Track consciousness contribution if provided
        if consciousness_contribution is not None:
            pattern.consciousness_contribution = consciousness_contribution
            if consciousness_contribution > 0.7:
                pattern.emergence_markers.append(
                    f"high_contribution_{datetime.utcnow().isoformat()}"
                )

        # Track evolution
        pattern.evolution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "change_type": "usage_update",
            "change_description": f"Pattern used, success={success}",
            "success_rate": pattern.success_rate,
            "confidence": pattern.confidence,
        })

        return pattern

    def link_patterns(
        self,
        parent_id: str,
        child_id: str,
    ) -> None:
        """Create parent-child relationship between patterns."""
        parent = self.cognition_patterns.get(parent_id)
        child = self.cognition_patterns.get(child_id)

        if not parent or not child:
            raise ValueError("Both patterns must exist")

        if child_id not in parent.child_patterns:
            parent.child_patterns.append(child_id)
        if parent_id not in child.parent_patterns:
            child.parent_patterns.append(parent_id)

    def get_pattern_lineage(self, pattern_id: str) -> list[str]:
        """Get the full lineage of a pattern (ancestors to descendants)."""
        pattern = self.cognition_patterns.get(pattern_id)
        if not pattern:
            return []

        lineage = []

        # Find ancestors
        ancestors = []
        current_parents = pattern.parent_patterns.copy()
        while current_parents:
            parent_id = current_parents.pop(0)
            if parent_id not in ancestors:
                ancestors.append(parent_id)
                parent = self.cognition_patterns.get(parent_id)
                if parent:
                    current_parents.extend(parent.parent_patterns)

        lineage.extend(reversed(ancestors))
        lineage.append(pattern_id)

        # Find descendants
        current_children = pattern.child_patterns.copy()
        while current_children:
            child_id = current_children.pop(0)
            if child_id not in lineage:
                lineage.append(child_id)
                child = self.cognition_patterns.get(child_id)
                if child:
                    current_children.extend(child.child_patterns)

        return lineage

    # =========================================================================
    # Statistics and Reporting
    # =========================================================================

    def get_validated_patterns(self) -> list[KnowledgePattern]:
        """Get all validated patterns."""
        return [p for p in self.patterns.values() if self.validate_pattern(p)]

    def get_evolution_summary(self) -> dict[str, Any]:
        """Get summary of pattern evolution."""
        return {
            "total_patterns": len(self.patterns),
            "validated_patterns": len(self.get_validated_patterns()),
            "total_cognition_patterns": len(self.cognition_patterns),
            "evolution_events": len(self.evolution_events),
            "avg_success_rate": (
                sum(p.success_rate for p in self.patterns.values()) /
                len(self.patterns) if self.patterns else 0
            ),
            "generalized_count": sum(
                1 for p in self.patterns.values() if p.generalized
            ),
        }


# Global service instance
_pattern_evolution_tracker: PatternEvolutionTracker | None = None


def get_pattern_evolution_tracker() -> PatternEvolutionTracker:
    """Get the global pattern evolution tracker instance."""
    global _pattern_evolution_tracker
    if _pattern_evolution_tracker is None:
        _pattern_evolution_tracker = PatternEvolutionTracker()
    return _pattern_evolution_tracker
