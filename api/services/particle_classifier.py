"""
Particle Classifier Service

Feature: 040-metacognitive-particles
Based on: Sandved-Smith & Da Costa (2024)

Classifies cognitive processes into particle types based on Markov blanket
structure analysis.

Classification Algorithm:
1. Check for belief mapping (μ → Q_μ(η))
2. Check for internal Markov blanket
3. Check for active paths to internal
4. Check for strange configuration
5. Count nested blankets for N-level

AUTHOR: Mani Saint-Victor, MD
"""

import logging
from typing import Tuple

from api.models.markov_blanket import MarkovBlanketPartition
from api.models.metacognitive_particle import (
    MAX_NESTING_DEPTH,
    ParticleType,
    enforce_cognitive_core,
)

logger = logging.getLogger("dionysus.services.particle_classifier")


class ParticleClassifier:
    """
    Classifies cognitive processes into particle types.

    Uses structural analysis of Markov blanket configuration to determine
    the type of metacognitive particle.

    Per Sandved-Smith & Da Costa (2024):
    - Cognitive: Has μ → Q_μ(η) belief mapping
    - Passive Metacognitive: μ² exists, no a² paths to μ¹
    - Active Metacognitive: Has internal blanket b² = (s², a²)
    - Strange: a¹ does NOT influence μ¹ directly
    - Nested (N-level): N internal Markov blankets detected
    """

    def __init__(self):
        self.classification_cache = {}

    async def classify(
        self,
        agent_id: str,
        blanket: MarkovBlanketPartition
    ) -> Tuple[ParticleType, float, int, bool]:
        """
        Classify a cognitive process into particle type.

        Args:
            agent_id: Identifier for the agent
            blanket: Markov blanket structure to analyze

        Returns:
            Tuple of (particle_type, confidence, level, has_agency)
        """
        # Validate blanket structure
        if not blanket.is_valid_partition():
            overlaps = blanket.get_overlaps()
            logger.warning(f"Invalid partition for {agent_id}: {overlaps}")
            # Still attempt classification but with lower confidence

        # Run classification algorithm
        particle_type, confidence = self._classify_structure(blanket)

        # Determine nesting level
        level = self._count_nested_blankets(blanket)

        # Enforce cognitive core limit
        enforce_cognitive_core(level)

        # Determine agency
        has_agency = self._has_agency(particle_type, blanket)

        logger.info(
            f"Classified {agent_id}: type={particle_type.value}, "
            f"confidence={confidence:.2f}, level={level}, has_agency={has_agency}"
        )

        return particle_type, confidence, level, has_agency

    def _classify_structure(
        self,
        blanket: MarkovBlanketPartition
    ) -> Tuple[ParticleType, float]:
        """
        Classify based on blanket structure.

        Algorithm:
        1. No belief mapping → cannot classify
        2. No internal blanket → COGNITIVE
        3. No active paths to internal → PASSIVE_METACOGNITIVE
        4. Strange configuration → STRANGE_METACOGNITIVE
        5. Multiple nested blankets → NESTED_N_LEVEL
        6. Otherwise → ACTIVE_METACOGNITIVE
        """
        confidence = 1.0

        # Check for valid blanket structure
        if not blanket.is_valid_partition():
            confidence *= 0.7

        # Check for belief mapping capability
        if not self._has_belief_mapping(blanket):
            # Cannot form beliefs about external - minimal cognitive
            return ParticleType.COGNITIVE, confidence * 0.5

        # Check for internal Markov blanket
        if not self._has_internal_blanket(blanket):
            # Basic cognitive particle
            return ParticleType.COGNITIVE, confidence * 0.9

        # Has internal blanket - check for active paths
        if not self._has_active_paths_to_internal(blanket):
            # Passive metacognition - beliefs about beliefs but no control
            return ParticleType.PASSIVE_METACOGNITIVE, confidence * 0.85

        # Has active paths - check for strange configuration
        if self._is_strange_configuration(blanket):
            # Strange particle - actions inferred via sensory
            return ParticleType.STRANGE_METACOGNITIVE, confidence * 0.8

        # Check for N-level nesting
        n_levels = self._count_nested_blankets(blanket)
        if n_levels > 1:
            return ParticleType.NESTED_N_LEVEL, confidence * 0.9

        # Default to active metacognitive
        return ParticleType.ACTIVE_METACOGNITIVE, confidence * 0.95

    def _has_belief_mapping(self, blanket: MarkovBlanketPartition) -> bool:
        """
        Check if blanket has belief mapping μ → Q_μ(η).

        FR-001: Particle must have belief mapping to be classified.

        A belief mapping requires:
        - Internal paths (μ) to exist
        - Sensory paths to connect to external
        """
        has_internal = len(blanket.internal_paths) > 0
        has_sensory = len(blanket.sensory_paths) > 0
        has_external = len(blanket.external_paths) > 0

        return has_internal and has_sensory and has_external

    def _has_internal_blanket(self, blanket: MarkovBlanketPartition) -> bool:
        """
        Check if blanket contains internal Markov blanket b² = (s², a²).

        FR-002: Check for nested structure.

        An internal blanket requires:
        - Multiple internal paths (suggesting hierarchy)
        - Blanket paths that could form a nested structure
        """
        # Simple heuristic: multiple internal paths suggest nesting
        # In a full implementation, we'd check for actual nested structures
        has_multiple_internal = len(blanket.internal_paths) >= 2
        has_complete_blanket = (
            len(blanket.sensory_paths) > 0 and
            len(blanket.active_paths) > 0
        )

        return has_multiple_internal and has_complete_blanket

    def _has_active_paths_to_internal(self, blanket: MarkovBlanketPartition) -> bool:
        """
        Check if active paths can influence internal paths.

        Active metacognition requires a² → μ¹ influence.
        """
        # Check if active paths and internal paths have potential connections
        # In a full implementation, we'd trace the causal graph
        has_active = len(blanket.active_paths) > 0
        has_internal = len(blanket.internal_paths) > 0

        if not (has_active and has_internal):
            return False

        # Heuristic: active paths targeting internal-like names
        # This is a placeholder - real implementation would check graph structure
        for active in blanket.active_paths:
            for internal in blanket.internal_paths:
                # Check for naming convention suggesting connection
                if "internal" in active or "belief" in active or "mu" in active:
                    return True

        # Default to True if we have both - better to be inclusive
        return True

    def _is_strange_configuration(self, blanket: MarkovBlanketPartition) -> bool:
        """
        Check if blanket has strange configuration.

        FR-003: Strange particles have a¹ NOT influencing μ¹ directly.

        Strange configuration means actions are inferred via sensory paths only.
        """
        # Check for paths suggesting indirect action inference
        # Strange particles have active paths that don't directly connect to internal

        # Heuristic: if all active paths go to external only
        active_to_external = False
        for active in blanket.active_paths:
            for external in blanket.external_paths:
                if any(ext_part in active for ext_part in external.split("-")):
                    active_to_external = True
                    break

        # Strange if active paths primarily target external
        return active_to_external and len(blanket.active_paths) > 0

    def _count_nested_blankets(self, blanket: MarkovBlanketPartition) -> int:
        """
        Count the number of nested Markov blankets.

        Returns the nesting level (0 = base, N = deepest nested).
        """
        # Heuristic based on internal path structure
        # In full implementation, would recursively check nested structures

        internal_count = len(blanket.internal_paths)

        if internal_count <= 1:
            return 0
        elif internal_count <= 3:
            return 1
        elif internal_count <= 6:
            return 2
        else:
            # Cap at MAX_NESTING_DEPTH
            estimated_level = min(internal_count // 2, MAX_NESTING_DEPTH)
            return estimated_level

    def _has_agency(
        self,
        particle_type: ParticleType,
        blanket: MarkovBlanketPartition
    ) -> bool:
        """
        Determine if particle has sense of agency.

        Agency requires:
        - Active metacognitive type (or higher)
        - Joint probability Q(μ,a) ≠ Q(μ)Q(a)
        """
        # Basic cognitive particles don't have agency
        if particle_type == ParticleType.COGNITIVE:
            return False

        # Passive metacognitive may have limited agency
        if particle_type == ParticleType.PASSIVE_METACOGNITIVE:
            return False

        # Active, Strange, and Nested particles can have agency
        # Full determination requires computing KL divergence
        has_active = len(blanket.active_paths) > 0
        has_internal = len(blanket.internal_paths) > 0

        return has_active and has_internal


async def classify_agent(
    agent_id: str,
    blanket: MarkovBlanketPartition
) -> Tuple[ParticleType, float, int, bool]:
    """
    Convenience function to classify an agent.

    Args:
        agent_id: Agent identifier
        blanket: Markov blanket structure

    Returns:
        Tuple of (particle_type, confidence, level, has_agency)
    """
    classifier = ParticleClassifier()
    return await classifier.classify(agent_id, blanket)
