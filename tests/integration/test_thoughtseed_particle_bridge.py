"""
Integration Tests for ThoughtSeed-Particle Bridge

Feature: 040-metacognitive-particles
Tasks: T070

Tests bidirectional conversion between ThoughtSeeds and MetacognitiveParticles.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
from uuid import uuid4

from api.models.thought import ThoughtSeed, ThoughtLayer, CompetitionStatus
from api.models.metacognitive_particle import MetacognitiveParticle, ParticleType
from api.models.markov_blanket import MarkovBlanketPartition
from api.services.thoughtseed_particle_bridge import (
    ThoughtSeedParticleBridge,
    get_thoughtseed_particle_bridge,
    LAYER_TO_PARTICLE_HINT,
    PARTICLE_TO_LAYER_HINT
)


class TestThoughtSeedToParticle:
    """Tests for thoughtseed_to_particle conversion."""

    @pytest.fixture
    def bridge(self):
        """Create bridge instance."""
        return ThoughtSeedParticleBridge()

    @pytest.fixture
    def sensorimotor_thought(self):
        """Create sensorimotor layer thought."""
        return ThoughtSeed(
            layer=ThoughtLayer.SENSORIMOTOR,
            content="Motor planning",
            activation_level=0.6
        )

    @pytest.fixture
    def conceptual_thought(self):
        """Create conceptual layer thought."""
        return ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Abstract reasoning",
            activation_level=0.8
        )

    @pytest.fixture
    def metacognitive_thought(self):
        """Create metacognitive layer thought."""
        return ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Self-reflection",
            activation_level=0.9,
            child_thought_ids=[uuid4(), uuid4()]
        )

    @pytest.mark.asyncio
    async def test_sensorimotor_to_cognitive(self, bridge, sensorimotor_thought):
        """Test sensorimotor thought converts to cognitive particle."""
        particle, confidence = await bridge.thoughtseed_to_particle(sensorimotor_thought)

        assert isinstance(particle, MetacognitiveParticle)
        assert particle.particle_type == ParticleType.COGNITIVE
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_conceptual_to_passive_metacognitive(self, bridge, conceptual_thought):
        """Test conceptual thought converts appropriately."""
        particle, confidence = await bridge.thoughtseed_to_particle(conceptual_thought)

        assert isinstance(particle, MetacognitiveParticle)
        # Should be at least passive metacognitive
        assert particle.particle_type in [
            ParticleType.COGNITIVE,
            ParticleType.PASSIVE_METACOGNITIVE,
            ParticleType.ACTIVE_METACOGNITIVE
        ]

    @pytest.mark.asyncio
    async def test_metacognitive_to_nested(self, bridge, metacognitive_thought):
        """Test metacognitive thought with children converts to nested particle."""
        particle, confidence = await bridge.thoughtseed_to_particle(metacognitive_thought)

        assert isinstance(particle, MetacognitiveParticle)
        # With child thoughts, should have some depth
        assert particle.metacognition_depth >= 1

    @pytest.mark.asyncio
    async def test_conversion_with_explicit_blanket(self, bridge, conceptual_thought):
        """Test conversion with explicit blanket override."""
        explicit_blanket = MarkovBlanketPartition(
            external_paths=["ext1", "ext2"],
            sensory_paths=["sens1"],
            active_paths=["act1", "act2", "act3"],
            internal_paths=["int1", "int2", "int3", "int4"]
        )

        particle, confidence = await bridge.thoughtseed_to_particle(
            conceptual_thought,
            blanket=explicit_blanket
        )

        # Should have agency with active paths
        assert particle.has_sense_of_agency is True

    @pytest.mark.asyncio
    async def test_particle_preserves_thought_id(self, bridge, conceptual_thought):
        """Test particle ID matches thought ID."""
        particle, _ = await bridge.thoughtseed_to_particle(conceptual_thought)

        assert particle.id == str(conceptual_thought.id)


class TestParticleToThoughtSeed:
    """Tests for particle_to_thoughtseed conversion."""

    @pytest.fixture
    def bridge(self):
        return ThoughtSeedParticleBridge()

    @pytest.fixture
    def cognitive_particle(self):
        """Create cognitive particle."""
        return MetacognitiveParticle(
            name="Basic Particle",
            particle_type=ParticleType.COGNITIVE,
            metacognition_depth=0,
            has_sense_of_agency=False
        )

    @pytest.fixture
    def active_metacognitive_particle(self):
        """Create active metacognitive particle."""
        return MetacognitiveParticle(
            name="Active Particle",
            particle_type=ParticleType.ACTIVE_METACOGNITIVE,
            metacognition_depth=2,
            has_sense_of_agency=True
        )

    @pytest.fixture
    def nested_particle(self):
        """Create nested N-level particle."""
        return MetacognitiveParticle(
            name="Nested Particle",
            particle_type=ParticleType.NESTED_N_LEVEL,
            metacognition_depth=4,
            has_sense_of_agency=True
        )

    @pytest.mark.asyncio
    async def test_cognitive_to_perceptual(self, bridge, cognitive_particle):
        """Test cognitive particle converts to perceptual layer."""
        thought = await bridge.particle_to_thoughtseed(cognitive_particle)

        assert isinstance(thought, ThoughtSeed)
        assert thought.layer == ThoughtLayer.PERCEPTUAL

    @pytest.mark.asyncio
    async def test_active_metacognitive_to_abstract(self, bridge, active_metacognitive_particle):
        """Test active metacognitive particle converts to abstract layer."""
        thought = await bridge.particle_to_thoughtseed(active_metacognitive_particle)

        assert thought.layer == ThoughtLayer.ABSTRACT

    @pytest.mark.asyncio
    async def test_nested_to_metacognitive(self, bridge, nested_particle):
        """Test nested particle converts to metacognitive layer."""
        thought = await bridge.particle_to_thoughtseed(nested_particle)

        assert thought.layer == ThoughtLayer.METACOGNITIVE

    @pytest.mark.asyncio
    async def test_activation_from_agency_and_depth(self, bridge):
        """Test activation level is influenced by agency and depth."""
        # No agency, low depth
        low_particle = MetacognitiveParticle(
            name="Low",
            particle_type=ParticleType.COGNITIVE,
            metacognition_depth=0,
            has_sense_of_agency=False
        )
        low_thought = await bridge.particle_to_thoughtseed(low_particle)

        # Has agency, high depth
        high_particle = MetacognitiveParticle(
            name="High",
            particle_type=ParticleType.NESTED_N_LEVEL,
            metacognition_depth=4,
            has_sense_of_agency=True
        )
        high_thought = await bridge.particle_to_thoughtseed(high_particle)

        # High should have higher activation
        assert high_thought.activation_level > low_thought.activation_level

    @pytest.mark.asyncio
    async def test_custom_activation(self, bridge, cognitive_particle):
        """Test custom activation level."""
        thought = await bridge.particle_to_thoughtseed(
            cognitive_particle,
            activation_level=0.9
        )

        assert thought.activation_level == 0.9

    @pytest.mark.asyncio
    async def test_custom_content(self, bridge, cognitive_particle):
        """Test custom content."""
        thought = await bridge.particle_to_thoughtseed(
            cognitive_particle,
            content="Custom content"
        )

        assert thought.content == "Custom content"

    @pytest.mark.asyncio
    async def test_neuronal_packet_contains_metadata(self, bridge, active_metacognitive_particle):
        """Test neuronal packet contains particle metadata."""
        thought = await bridge.particle_to_thoughtseed(active_metacognitive_particle)

        packet = thought.neuronal_packet
        assert packet["source"] == "metacognitive_particle"
        assert packet["particle_type"] == "active_metacognitive"
        assert packet["metacognition_depth"] == 2
        assert packet["has_sense_of_agency"] is True


class TestRoundTripValidation:
    """Tests for round-trip consistency."""

    @pytest.fixture
    def bridge(self):
        return ThoughtSeedParticleBridge()

    @pytest.mark.asyncio
    async def test_round_trip_perceptual(self, bridge):
        """Test round-trip for perceptual layer thought."""
        original = ThoughtSeed(
            layer=ThoughtLayer.PERCEPTUAL,
            content="Perceptual thought",
            activation_level=0.7
        )

        result = await bridge.validate_round_trip(original)

        assert result["valid"] is True
        assert result["layer_close_match"] is True
        assert result["activation_preserved"] is True

    @pytest.mark.asyncio
    async def test_round_trip_metacognitive(self, bridge):
        """Test round-trip for metacognitive layer thought."""
        original = ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Meta thought",
            activation_level=0.9
        )

        result = await bridge.validate_round_trip(original)

        assert result["valid"] is True
        assert result["layer_close_match"] is True

    @pytest.mark.asyncio
    async def test_round_trip_with_children(self, bridge):
        """Test round-trip for thought with children."""
        original = ThoughtSeed(
            layer=ThoughtLayer.ABSTRACT,
            content="Parent thought",
            activation_level=0.8,
            child_thought_ids=[uuid4(), uuid4()]
        )

        result = await bridge.validate_round_trip(original)

        assert "classification_confidence" in result
        assert result["classification_confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_round_trip_reports_differences(self, bridge):
        """Test that round-trip reports any differences."""
        original = ThoughtSeed(
            layer=ThoughtLayer.SENSORIMOTOR,
            content="Test",
            activation_level=0.5
        )

        result = await bridge.validate_round_trip(original)

        # Sensorimotor might map to Perceptual on return - that's acceptable
        if not result["layer_exact_match"]:
            assert len(result["differences"]) > 0


class TestBlanketInference:
    """Tests for blanket inference from ThoughtSeed."""

    @pytest.fixture
    def bridge(self):
        return ThoughtSeedParticleBridge()

    def test_infer_blanket_sensorimotor(self, bridge):
        """Test blanket inference for sensorimotor layer."""
        thought = ThoughtSeed(
            layer=ThoughtLayer.SENSORIMOTOR,
            content="Motor",
            activation_level=0.5
        )

        blanket = bridge._infer_blanket_from_thought(thought)

        assert len(blanket.external_paths) > 0
        assert len(blanket.sensory_paths) > 0
        assert len(blanket.internal_paths) > 0

    def test_infer_blanket_metacognitive(self, bridge):
        """Test blanket inference for metacognitive layer."""
        thought = ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Meta",
            activation_level=0.9
        )

        blanket = bridge._infer_blanket_from_thought(thought)

        # Metacognitive should have more internal paths
        assert len(blanket.internal_paths) >= 4

    def test_infer_blanket_with_parent(self, bridge):
        """Test blanket includes parent link."""
        parent_id = uuid4()
        thought = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Child",
            activation_level=0.7,
            parent_thought_id=parent_id
        )

        blanket = bridge._infer_blanket_from_thought(thought)

        # Should have parent link in internal paths
        assert any("parent_link" in path for path in blanket.internal_paths)

    def test_infer_blanket_with_children(self, bridge):
        """Test blanket includes child influence paths."""
        thought = ThoughtSeed(
            layer=ThoughtLayer.ABSTRACT,
            content="Parent",
            activation_level=0.8,
            child_thought_ids=[uuid4(), uuid4()]
        )

        blanket = bridge._infer_blanket_from_thought(thought)

        # Should have child influence in active paths
        child_paths = [p for p in blanket.active_paths if "child_influence" in p]
        assert len(child_paths) == 2

    def test_infer_blanket_high_activation(self, bridge):
        """Test high activation adds active paths."""
        thought = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Highly active",
            activation_level=0.95
        )

        blanket = bridge._infer_blanket_from_thought(thought)

        # Should have high activation action
        assert any("high_activation" in path for path in blanket.active_paths)


class TestLayerMappings:
    """Tests for layer-particle mapping constants."""

    def test_layer_to_particle_hint_complete(self):
        """Test all layers have particle hints."""
        for layer in ThoughtLayer:
            assert layer in LAYER_TO_PARTICLE_HINT

    def test_particle_to_layer_hint_complete(self):
        """Test all particle types have layer hints."""
        for ptype in ParticleType:
            assert ptype in PARTICLE_TO_LAYER_HINT


class TestBridgeSingleton:
    """Tests for bridge factory function."""

    def test_get_singleton(self):
        """Test factory returns singleton."""
        bridge1 = get_thoughtseed_particle_bridge()
        bridge2 = get_thoughtseed_particle_bridge()

        assert bridge1 is bridge2

    def test_bridge_has_classifier(self):
        """Test bridge has particle classifier."""
        bridge = get_thoughtseed_particle_bridge()

        assert hasattr(bridge, "_classifier")
        assert bridge._classifier is not None
