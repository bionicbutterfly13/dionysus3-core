"""
Basin Reorganization Service
Feature: 008-mosaeic-memory

Manages attractor basin dynamics when new beliefs emerge.
Ported from active-inference-core/src/caicore/dynamics/attractor_basin_manager.py

Implements the four basin influence types:
- REINFORCEMENT: New belief strengthens existing basin
- COMPETITION: New belief competes with existing basin
- SYNTHESIS: New belief merges with existing basin
- EMERGENCE: New belief creates entirely new basin
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from api.models.mosaeic import (
    AttractorBasin,
    BasinInfluenceType,
    BeliefRewrite,
)

logger = logging.getLogger(__name__)


@dataclass
class BasinReorganizationConfig:
    """Configuration for basin reorganization dynamics."""
    reinforcement_threshold: float = 0.8   # Similarity for reinforcement
    competition_threshold: float = 0.5     # Similarity for competition
    synthesis_strength_threshold: float = 1.5  # Basin strength for synthesis vs reinforcement
    emergence_similarity_max: float = 0.5  # Below this, new basin emerges
    default_basin_radius: float = 0.5
    default_basin_strength: float = 1.0


@dataclass
class ThoughtSeedIntegrationEvent:
    """
    Event representing integration of a new thoughtseed/belief into the basin landscape.
    Ported from active-inference-core.
    """
    event_id: str = field(default_factory=lambda: str(uuid4()))
    thoughtseed_id: str = ""
    concept_description: str = ""
    target_basin_id: str | None = None
    influence_type: BasinInfluenceType = BasinInfluenceType.EMERGENCE
    influence_strength: float = 0.0
    pre_integration_state: dict[str, Any] = field(default_factory=dict)
    post_integration_state: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class BasinReorganizationService:
    """
    Manages the dynamic attractor basin landscape for belief integration.

    When new beliefs emerge from prediction error learning or schema extraction,
    this service determines how they affect existing basins:

    - REINFORCEMENT: High similarity + strong existing basin -> strengthens it
    - SYNTHESIS: High similarity + weak basin -> merges with it
    - COMPETITION: Medium similarity + strong basin -> competes
    - EMERGENCE: Low similarity -> creates new basin
    """

    def __init__(self, config: BasinReorganizationConfig | None = None):
        self.config = config or BasinReorganizationConfig()
        self.basins: dict[str, AttractorBasin] = {}
        self.integration_events: list[ThoughtSeedIntegrationEvent] = []

        # Initialize default basin
        self._create_default_basin()

    def _create_default_basin(self) -> None:
        """Create a default attractor basin for system initialization."""
        default_basin = AttractorBasin(
            basin_id="default_cognitive_basin",
            center_concept="general_learning",
            strength=self.config.default_basin_strength,
            radius=self.config.default_basin_radius,
            thoughtseeds=set(),
            related_concepts={
                "learning": 0.9,
                "adaptation": 0.8,
                "pattern_recognition": 0.7
            }
        )
        self.basins[default_basin.basin_id] = default_basin

    def calculate_concept_similarity(
        self,
        concept1: str,
        concept2: str,
    ) -> float:
        """
        Calculate semantic similarity between two concepts.

        This is a simplified implementation using Jaccard similarity.
        In production, use semantic embeddings for better results.
        """
        concept1_words = set(concept1.lower().split())
        concept2_words = set(concept2.lower().split())

        if not concept1_words or not concept2_words:
            return 0.0

        intersection = len(concept1_words.intersection(concept2_words))
        union = len(concept1_words.union(concept2_words))

        jaccard_similarity = intersection / union if union > 0 else 0.0

        # Semantic bonus for related terms
        related_terms = {
            "learning": ["adaptation", "training", "evolution", "improvement"],
            "consciousness": ["awareness", "attention", "reflection", "cognition"],
            "memory": ["recall", "remembering", "encoding", "storage"],
            "belief": ["conviction", "assumption", "expectation", "model"],
        }

        semantic_bonus = 0.0
        for key, related in related_terms.items():
            if key in concept1.lower():
                for term in related:
                    if term in concept2.lower():
                        semantic_bonus = max(semantic_bonus, 0.2)
            if key in concept2.lower():
                for term in related:
                    if term in concept1.lower():
                        semantic_bonus = max(semantic_bonus, 0.2)

        return min(1.0, jaccard_similarity + semantic_bonus)

    def determine_influence_type(
        self,
        belief_content: str,
        context_basins: list[str] | None = None,
    ) -> tuple[BasinInfluenceType, str | None, float]:
        """
        Determine how a new belief should influence existing basins.

        Args:
            belief_content: The content of the new belief
            context_basins: Optional list of basin IDs to consider

        Returns:
            Tuple of (influence_type, target_basin_id, influence_strength)
        """
        basins_to_check = (
            [self.basins[bid] for bid in context_basins if bid in self.basins]
            if context_basins
            else list(self.basins.values())
        )

        if not basins_to_check:
            return BasinInfluenceType.EMERGENCE, None, 1.0

        # Calculate similarities to all basins
        similarities: dict[str, float] = {}
        for basin in basins_to_check:
            sim = self.calculate_concept_similarity(
                belief_content,
                basin.center_concept
            )
            # Also check related concepts
            for concept, weight in basin.related_concepts.items():
                concept_sim = self.calculate_concept_similarity(
                    belief_content,
                    concept
                )
                sim = max(sim, concept_sim * weight)

            similarities[basin.basin_id] = sim

        if not similarities:
            return BasinInfluenceType.EMERGENCE, None, 1.0

        # Find most similar basin
        max_basin_id = max(similarities, key=similarities.get)  # type: ignore
        max_similarity = similarities[max_basin_id]
        target_basin = self.basins[max_basin_id]

        # Use basin's own influence calculation
        influence_type, influence_strength = target_basin.calculate_influence_on(
            max_similarity
        )

        return influence_type, max_basin_id, influence_strength

    def integrate_belief(
        self,
        belief: BeliefRewrite,
        context_basins: list[str] | None = None,
    ) -> ThoughtSeedIntegrationEvent:
        """
        Integrate a new belief into the basin landscape.

        Args:
            belief: The belief to integrate
            context_basins: Optional list of relevant basin IDs

        Returns:
            Integration event describing what happened
        """
        # Determine influence type
        influence_type, target_basin_id, influence_strength = (
            self.determine_influence_type(belief.new_belief, context_basins)
        )

        # Capture pre-integration state
        pre_state = {
            basin_id: {
                "strength": basin.strength,
                "thoughtseed_count": len(basin.thoughtseeds),
            }
            for basin_id, basin in self.basins.items()
        }

        # Apply the appropriate reorganization
        if influence_type == BasinInfluenceType.REINFORCEMENT:
            self._apply_reinforcement(target_basin_id, belief, influence_strength)

        elif influence_type == BasinInfluenceType.SYNTHESIS:
            self._apply_synthesis(target_basin_id, belief, influence_strength)

        elif influence_type == BasinInfluenceType.COMPETITION:
            self._apply_competition(target_basin_id, belief, influence_strength)

        else:  # EMERGENCE
            target_basin_id = self._apply_emergence(belief, influence_strength)

        # Capture post-integration state
        post_state = {
            basin_id: {
                "strength": basin.strength,
                "thoughtseed_count": len(basin.thoughtseeds),
            }
            for basin_id, basin in self.basins.items()
        }

        # Create integration event
        event = ThoughtSeedIntegrationEvent(
            thoughtseed_id=str(belief.id),
            concept_description=belief.new_belief,
            target_basin_id=target_basin_id,
            influence_type=influence_type,
            influence_strength=influence_strength,
            pre_integration_state=pre_state,
            post_integration_state=post_state,
        )

        self.integration_events.append(event)

        # Update belief with evolution trigger
        belief.evolution_trigger = influence_type

        logger.info(
            f"Integrated belief {belief.id} via {influence_type.value} "
            f"to basin {target_basin_id} with strength {influence_strength:.3f}"
        )

        return event

    def _apply_reinforcement(
        self,
        basin_id: str | None,
        belief: BeliefRewrite,
        strength: float,
    ) -> None:
        """
        Apply REINFORCEMENT: Strengthen existing basin.

        The new belief aligns strongly with an already-strong basin,
        making it even more prominent in the cognitive landscape.
        """
        if not basin_id or basin_id not in self.basins:
            return

        basin = self.basins[basin_id]

        # Increase basin strength (up to max of 2.0)
        basin.strength = min(2.0, basin.strength + strength * 0.1)

        # Add belief to basin's thoughtseeds
        basin.thoughtseeds.add(str(belief.id))

        # Update activation history
        basin.activation_history.append(strength)
        if len(basin.activation_history) > 100:
            basin.activation_history = basin.activation_history[-100:]

        basin.last_modification = datetime.utcnow()

    def _apply_synthesis(
        self,
        basin_id: str | None,
        belief: BeliefRewrite,
        strength: float,
    ) -> None:
        """
        Apply SYNTHESIS: Merge with existing basin.

        The new belief is similar to an existing basin but the basin
        isn't strong enough for pure reinforcement. The belief expands
        the basin's conceptual territory.
        """
        if not basin_id or basin_id not in self.basins:
            return

        basin = self.basins[basin_id]

        # Moderate strength increase
        basin.strength = min(2.0, basin.strength + strength * 0.05)

        # Expand radius slightly to accommodate new concept
        basin.radius = min(1.0, basin.radius + 0.02)

        # Add to related concepts
        basin.related_concepts[belief.new_belief[:50]] = strength

        # Add belief to basin's thoughtseeds
        basin.thoughtseeds.add(str(belief.id))

        basin.last_modification = datetime.utcnow()

    def _apply_competition(
        self,
        basin_id: str | None,
        belief: BeliefRewrite,
        strength: float,
    ) -> None:
        """
        Apply COMPETITION: Compete with existing basin.

        The new belief has medium similarity but challenges the
        existing basin. This may weaken the existing basin while
        creating tension in the cognitive landscape.
        """
        if not basin_id or basin_id not in self.basins:
            return

        basin = self.basins[basin_id]

        # Slight decrease in existing basin strength (competition weakens it)
        basin.strength = max(0.1, basin.strength - strength * 0.05)

        # Create a competing sub-basin or marker
        competition_marker = f"competition_{str(belief.id)[:8]}"
        basin.related_concepts[competition_marker] = -strength  # Negative = competing

        basin.last_modification = datetime.utcnow()

        # The belief might spawn its own basin if competition is strong enough
        if strength > 0.7:
            self._apply_emergence(belief, strength * 0.5)

    def _apply_emergence(
        self,
        belief: BeliefRewrite,
        strength: float,
    ) -> str:
        """
        Apply EMERGENCE: Create entirely new basin.

        The new belief is sufficiently different from existing basins
        that it warrants its own attractor in the cognitive landscape.
        """
        new_basin = AttractorBasin(
            center_concept=belief.new_belief[:100],
            strength=self.config.default_basin_strength * strength,
            radius=self.config.default_basin_radius,
            thoughtseeds={str(belief.id)},
            related_concepts={
                belief.domain: 0.8,
            },
        )

        self.basins[new_basin.basin_id] = new_basin

        logger.info(f"Created new basin {new_basin.basin_id} for belief {belief.id}")

        return new_basin.basin_id

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_basin(self, basin_id: str) -> AttractorBasin | None:
        """Get a basin by ID."""
        return self.basins.get(basin_id)

    def get_basins_for_domain(self, domain: str) -> list[AttractorBasin]:
        """Get all basins related to a domain."""
        return [
            basin for basin in self.basins.values()
            if domain in basin.related_concepts
        ]

    def get_strongest_basins(self, limit: int = 5) -> list[AttractorBasin]:
        """Get the strongest basins in the landscape."""
        sorted_basins = sorted(
            self.basins.values(),
            key=lambda b: b.strength,
            reverse=True
        )
        return sorted_basins[:limit]

    def get_integration_history(
        self,
        influence_type: BasinInfluenceType | None = None,
        limit: int = 100,
    ) -> list[ThoughtSeedIntegrationEvent]:
        """Get integration event history, optionally filtered by type."""
        events = self.integration_events

        if influence_type:
            events = [e for e in events if e.influence_type == influence_type]

        return events[-limit:]

    def get_landscape_summary(self) -> dict[str, Any]:
        """Get a summary of the current basin landscape."""
        influence_counts = {t.value: 0 for t in BasinInfluenceType}
        for event in self.integration_events:
            influence_counts[event.influence_type.value] += 1

        return {
            "total_basins": len(self.basins),
            "avg_strength": (
                sum(b.strength for b in self.basins.values()) /
                len(self.basins) if self.basins else 0
            ),
            "total_thoughtseeds": sum(
                len(b.thoughtseeds) for b in self.basins.values()
            ),
            "integration_events": len(self.integration_events),
            "influence_type_distribution": influence_counts,
            "strongest_basin": (
                max(self.basins.values(), key=lambda b: b.strength).basin_id
                if self.basins else None
            ),
        }


# Global service instance
_basin_service: BasinReorganizationService | None = None


def get_basin_reorganization_service() -> BasinReorganizationService:
    """Get the global basin reorganization service instance."""
    global _basin_service
    if _basin_service is None:
        _basin_service = BasinReorganizationService()
    return _basin_service
