"""
ThoughtSeed-Particle Bridge Service

Feature: 040-metacognitive-particles
Based on: Integration requirements from spec 038 (ThoughtSeeds) and spec 040 (Metacognitive Particles)

Provides bidirectional conversion between:
- ThoughtSeed (5-layer cognitive hierarchy)
- MetacognitiveParticle (Markov blanket-based classification)

This bridge enables:
1. ThoughtSeeds to be analyzed for metacognitive properties
2. Particles to be instantiated as ThoughtSeeds
3. Round-trip consistency for cognitive entities

AUTHOR: Mani Saint-Victor, MD
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID, uuid4

from api.models.thought import ThoughtSeed, ThoughtLayer, CompetitionStatus
from api.models.metacognitive_particle import (
    MetacognitiveParticle,
    ParticleType,
)
from api.models.markov_blanket import MarkovBlanketPartition
from api.services.particle_classifier import ParticleClassifier

logger = logging.getLogger("dionysus.services.thoughtseed_particle_bridge")


# =============================================================================
# Layer-to-Particle Mapping
# =============================================================================

# Map ThoughtSeed layers to likely particle types
LAYER_TO_PARTICLE_HINT = {
    ThoughtLayer.SENSORIMOTOR: ParticleType.COGNITIVE,
    ThoughtLayer.PERCEPTUAL: ParticleType.COGNITIVE,
    ThoughtLayer.CONCEPTUAL: ParticleType.PASSIVE_METACOGNITIVE,
    ThoughtLayer.ABSTRACT: ParticleType.ACTIVE_METACOGNITIVE,
    ThoughtLayer.METACOGNITIVE: ParticleType.NESTED_N_LEVEL,
}

# Map particle types to suggested ThoughtSeed layers
PARTICLE_TO_LAYER_HINT = {
    ParticleType.COGNITIVE: ThoughtLayer.PERCEPTUAL,
    ParticleType.PASSIVE: ThoughtLayer.CONCEPTUAL,
    ParticleType.PASSIVE_METACOGNITIVE: ThoughtLayer.CONCEPTUAL,
    ParticleType.ACTIVE: ThoughtLayer.ABSTRACT,
    ParticleType.ACTIVE_METACOGNITIVE: ThoughtLayer.ABSTRACT,
    ParticleType.STRANGE: ThoughtLayer.ABSTRACT,
    ParticleType.STRANGE_METACOGNITIVE: ThoughtLayer.ABSTRACT,
    ParticleType.NESTED: ThoughtLayer.METACOGNITIVE,
    ParticleType.NESTED_N_LEVEL: ThoughtLayer.METACOGNITIVE,
    ParticleType.MULTIPLY_NESTED: ThoughtLayer.METACOGNITIVE,
}


class ThoughtSeedParticleBridge:
    """
    Bidirectional bridge between ThoughtSeeds and MetacognitiveParticles.

    Enables:
    - FR-021: thoughtseed_to_particle() conversion
    - FR-021: particle_to_thoughtseed() conversion
    - Round-trip consistency validation
    """

    def __init__(self):
        self._classifier = ParticleClassifier()

    async def thoughtseed_to_particle(
        self,
        thought: ThoughtSeed,
        blanket: Optional[MarkovBlanketPartition] = None
    ) -> Tuple[MetacognitiveParticle, float]:
        """
        Convert a ThoughtSeed to a MetacognitiveParticle.

        FR-021: Maps ThoughtSeed properties to particle classification.

        Args:
            thought: ThoughtSeed to convert
            blanket: Optional explicit blanket structure. If not provided,
                     a blanket is inferred from ThoughtSeed properties.

        Returns:
            Tuple of (MetacognitiveParticle, confidence_score)
        """
        # Infer or use provided blanket
        if blanket is None:
            blanket = self._infer_blanket_from_thought(thought)

        # Classify using ParticleClassifier
        particle_type, confidence, level, has_agency = await self._classifier.classify(
            agent_id=str(thought.id),
            blanket=blanket
        )

        # Create particle (ensure level is at least 1 per model constraint)
        effective_level = max(1, level)
        particle = MetacognitiveParticle(
            id=str(thought.id),
            name=f"Particle from ThoughtSeed {thought.layer.value}",
            particle_type=particle_type,
            metacognition_depth=effective_level,
            has_sense_of_agency=has_agency,
            cognitive_core_level=effective_level if level > 0 else None,
            blanket_id=str(uuid4()),  # New blanket ID
            source_paper="dionysus-bridge",
        )

        logger.info(
            f"Converted ThoughtSeed {thought.id} to {particle_type.value} "
            f"particle with confidence {confidence:.2f}"
        )

        return particle, confidence

    async def particle_to_thoughtseed(
        self,
        particle: MetacognitiveParticle,
        content: str = "",
        activation_level: Optional[float] = None
    ) -> ThoughtSeed:
        """
        Convert a MetacognitiveParticle to a ThoughtSeed.

        FR-021: Maps particle classification to ThoughtSeed properties.

        Args:
            particle: MetacognitiveParticle to convert
            content: Optional content for the ThoughtSeed
            activation_level: Optional activation level (0.0-1.0)

        Returns:
            ThoughtSeed with properties derived from particle
        """
        # Determine layer from particle type
        layer = PARTICLE_TO_LAYER_HINT.get(particle.particle_type, ThoughtLayer.CONCEPTUAL)

        # Determine activation from agency and depth
        if activation_level is None:
            # Higher metacognition depth and agency = higher activation
            base_activation = 0.5
            if particle.has_sense_of_agency:
                base_activation += 0.2
            depth_bonus = min(0.3, particle.metacognition_depth * 0.1)
            activation_level = min(1.0, base_activation + depth_bonus)

        thought = ThoughtSeed(
            id=UUID(particle.id) if len(particle.id) == 36 else uuid4(),
            layer=layer,
            content=content or f"ThoughtSeed from {particle.particle_type.value} particle",
            activation_level=activation_level,
            competition_status=CompetitionStatus.PENDING,
            source_id=particle.id,
            neuronal_packet={
                "source": "metacognitive_particle",
                "particle_type": particle.particle_type.value,
                "metacognition_depth": particle.metacognition_depth,
                "has_sense_of_agency": particle.has_sense_of_agency,
                "converted_at": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"Converted {particle.particle_type.value} particle to "
            f"ThoughtSeed at {layer.value} layer"
        )

        return thought

    def _infer_blanket_from_thought(self, thought: ThoughtSeed) -> MarkovBlanketPartition:
        """
        Infer a Markov blanket structure from ThoughtSeed properties.

        Uses layer, parent/child relationships, and activation level
        to construct a plausible blanket partition.
        """
        # Start with base paths based on layer
        external_paths = []
        sensory_paths = []
        active_paths = []
        internal_paths = []

        # Sensorimotor and perceptual layers have more external paths
        if thought.layer in [ThoughtLayer.SENSORIMOTOR, ThoughtLayer.PERCEPTUAL]:
            external_paths = ["environment", "sensory_input"]
            sensory_paths = ["perception", "feature_detection"]
            internal_paths = ["state_representation"]

        # Conceptual layer has balanced paths
        elif thought.layer == ThoughtLayer.CONCEPTUAL:
            external_paths = ["semantic_input"]
            sensory_paths = ["concept_detection", "pattern_recognition"]
            active_paths = ["concept_formation"]
            internal_paths = ["belief_1", "belief_2"]

        # Abstract layer has more internal/active paths
        elif thought.layer == ThoughtLayer.ABSTRACT:
            external_paths = ["abstract_input"]
            sensory_paths = ["abstract_detection"]
            active_paths = ["reasoning", "inference", "decision"]
            internal_paths = ["higher_belief_1", "higher_belief_2", "higher_belief_3"]

        # Metacognitive layer has deep internal structure
        elif thought.layer == ThoughtLayer.METACOGNITIVE:
            external_paths = ["meta_input"]
            sensory_paths = ["meta_observation"]
            active_paths = ["meta_control", "attention_modulation", "belief_revision"]
            internal_paths = [
                "meta_belief_1", "meta_belief_2", "meta_belief_3",
                "meta_belief_4", "meta_belief_5"
            ]

        # Add paths based on parent/child relationships
        if thought.parent_thought_id:
            internal_paths.append(f"parent_link_{thought.parent_thought_id}")

        for child_id in thought.child_thought_ids:
            active_paths.append(f"child_influence_{child_id}")

        # Higher activation suggests more active paths
        if thought.activation_level > 0.7:
            active_paths.append("high_activation_action")

        return MarkovBlanketPartition(
            external_paths=external_paths,
            sensory_paths=sensory_paths,
            active_paths=active_paths,
            internal_paths=internal_paths
        )

    async def validate_round_trip(
        self,
        thought: ThoughtSeed,
        blanket: Optional[MarkovBlanketPartition] = None
    ) -> dict:
        """
        Validate round-trip consistency: ThoughtSeed → Particle → ThoughtSeed.

        Checks that essential properties are preserved through conversion.

        Args:
            thought: Original ThoughtSeed
            blanket: Optional blanket for classification

        Returns:
            Dict with validation results and any differences
        """
        # Convert to particle
        particle, confidence = await self.thoughtseed_to_particle(thought, blanket)

        # Convert back to thought
        reconstructed = await self.particle_to_thoughtseed(
            particle,
            content=thought.content,
            activation_level=thought.activation_level
        )

        # Check consistency
        layer_match = thought.layer == reconstructed.layer
        activation_close = abs(thought.activation_level - reconstructed.activation_level) < 0.01

        # Layer should be close (within one level)
        layer_order = [
            ThoughtLayer.SENSORIMOTOR,
            ThoughtLayer.PERCEPTUAL,
            ThoughtLayer.CONCEPTUAL,
            ThoughtLayer.ABSTRACT,
            ThoughtLayer.METACOGNITIVE
        ]
        original_idx = layer_order.index(thought.layer)
        reconstructed_idx = layer_order.index(reconstructed.layer)
        layer_close = abs(original_idx - reconstructed_idx) <= 1

        result = {
            "valid": layer_close and activation_close,
            "layer_exact_match": layer_match,
            "layer_close_match": layer_close,
            "activation_preserved": activation_close,
            "original_layer": thought.layer.value,
            "reconstructed_layer": reconstructed.layer.value,
            "particle_type": particle.particle_type.value,
            "classification_confidence": confidence,
            "differences": []
        }

        if not layer_match:
            result["differences"].append(
                f"Layer changed: {thought.layer.value} -> {reconstructed.layer.value}"
            )

        if not activation_close:
            result["differences"].append(
                f"Activation changed: {thought.activation_level} -> {reconstructed.activation_level}"
            )

        logger.info(f"Round-trip validation: valid={result['valid']}")

        return result


# =============================================================================
# Factory Function
# =============================================================================

_bridge_instance: Optional[ThoughtSeedParticleBridge] = None


def get_thoughtseed_particle_bridge() -> ThoughtSeedParticleBridge:
    """Get singleton bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ThoughtSeedParticleBridge()
    return _bridge_instance
