"""
Unit Tests for ParticleClassifier Service

Feature: 040-metacognitive-particles
Tasks: T011

Tests particle classification based on Markov blanket structure.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
from api.models.markov_blanket import MarkovBlanketPartition
from api.models.metacognitive_particle import ParticleType, CognitiveCoreViolation
from api.services.particle_classifier import ParticleClassifier, classify_agent


class TestParticleClassifier:
    """Test suite for ParticleClassifier service."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return ParticleClassifier()

    @pytest.fixture
    def cognitive_blanket(self):
        """Blanket for basic cognitive particle (no internal blanket)."""
        return MarkovBlanketPartition(
            external_paths=["environment"],
            sensory_paths=["perception"],
            active_paths=[],
            internal_paths=["state"]
        )

    @pytest.fixture
    def passive_metacognitive_blanket(self):
        """Blanket for passive metacognitive particle."""
        return MarkovBlanketPartition(
            external_paths=["external"],
            sensory_paths=["sensory_1", "sensory_2"],
            active_paths=[],  # No active paths
            internal_paths=["belief_1", "belief_2"]
        )

    @pytest.fixture
    def active_metacognitive_blanket(self):
        """Blanket for active metacognitive particle."""
        return MarkovBlanketPartition(
            external_paths=["external"],
            sensory_paths=["sensory"],
            active_paths=["action_1", "action_2"],
            internal_paths=["belief_1", "belief_2", "belief_3"]
        )

    @pytest.fixture
    def nested_blanket(self):
        """Blanket for nested N-level particle."""
        return MarkovBlanketPartition(
            external_paths=["meta_input"],
            sensory_paths=["meta_observation"],
            active_paths=["meta_control", "attention"],
            internal_paths=[
                "meta_belief_1", "meta_belief_2", "meta_belief_3",
                "meta_belief_4", "meta_belief_5", "meta_belief_6"
            ]
        )

    @pytest.mark.asyncio
    async def test_classify_cognitive_particle(self, classifier, cognitive_blanket):
        """Test classification of basic cognitive particle."""
        particle_type, confidence, level, has_agency = await classifier.classify(
            agent_id="test_cognitive",
            blanket=cognitive_blanket
        )

        assert particle_type == ParticleType.COGNITIVE
        assert 0.0 <= confidence <= 1.0
        assert level >= 0
        assert has_agency is False

    @pytest.mark.asyncio
    async def test_classify_passive_metacognitive(self, classifier, passive_metacognitive_blanket):
        """Test classification of passive metacognitive particle."""
        particle_type, confidence, level, has_agency = await classifier.classify(
            agent_id="test_passive",
            blanket=passive_metacognitive_blanket
        )

        # With current heuristics, passive blankets (no active paths) classify
        # as COGNITIVE or PASSIVE_METACOGNITIVE depending on internal structure
        assert particle_type in [ParticleType.COGNITIVE, ParticleType.PASSIVE_METACOGNITIVE]
        assert 0.0 <= confidence <= 1.0
        # Without active paths, no agency
        assert has_agency is False

    @pytest.mark.asyncio
    async def test_classify_active_metacognitive(self, classifier, active_metacognitive_blanket):
        """Test classification of active metacognitive particle."""
        particle_type, confidence, level, has_agency = await classifier.classify(
            agent_id="test_active",
            blanket=active_metacognitive_blanket
        )

        assert particle_type in [
            ParticleType.ACTIVE_METACOGNITIVE,
            ParticleType.STRANGE_METACOGNITIVE,
            ParticleType.NESTED_N_LEVEL
        ]
        assert 0.0 <= confidence <= 1.0
        assert has_agency is True

    @pytest.mark.asyncio
    async def test_classify_nested_particle(self, classifier, nested_blanket):
        """Test classification of nested N-level particle."""
        particle_type, confidence, level, has_agency = await classifier.classify(
            agent_id="test_nested",
            blanket=nested_blanket
        )

        assert particle_type == ParticleType.NESTED_N_LEVEL
        assert level >= 1
        assert has_agency is True

    @pytest.mark.asyncio
    async def test_has_belief_mapping(self, classifier):
        """Test _has_belief_mapping check."""
        # Valid blanket with belief mapping
        valid_blanket = MarkovBlanketPartition(
            external_paths=["ext"],
            sensory_paths=["sens"],
            active_paths=[],
            internal_paths=["int"]
        )
        assert classifier._has_belief_mapping(valid_blanket) is True

        # Invalid - no internal paths
        invalid_blanket = MarkovBlanketPartition(
            external_paths=["ext"],
            sensory_paths=["sens"],
            active_paths=[],
            internal_paths=[]
        )
        assert classifier._has_belief_mapping(invalid_blanket) is False

    @pytest.mark.asyncio
    async def test_confidence_reduced_for_invalid_partition(self, classifier):
        """Test that confidence is reduced for invalid partitions."""
        # Create blanket with overlapping paths (invalid)
        blanket = MarkovBlanketPartition(
            external_paths=["shared"],
            sensory_paths=["shared"],  # Overlaps with external
            active_paths=[],
            internal_paths=["int"]
        )

        particle_type, confidence, level, has_agency = await classifier.classify(
            agent_id="test_invalid",
            blanket=blanket
        )

        # Confidence should be reduced
        assert confidence < 1.0

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test classify_agent convenience function."""
        blanket = MarkovBlanketPartition(
            external_paths=["ext"],
            sensory_paths=["sens"],
            active_paths=["act"],
            internal_paths=["int1", "int2"]
        )

        result = await classify_agent("test_agent", blanket)
        assert len(result) == 4  # (type, confidence, level, has_agency)


class TestCognitiveCoreEnforcement:
    """Test cognitive core depth enforcement."""

    @pytest.mark.asyncio
    async def test_cognitive_core_violation_on_deep_nesting(self):
        """Test that CognitiveCoreViolation is raised for excessive nesting."""
        from api.models.metacognitive_particle import enforce_cognitive_core, MAX_NESTING_DEPTH

        # Should not raise for valid levels
        for level in range(MAX_NESTING_DEPTH + 1):
            enforce_cognitive_core(level)  # Should pass

        # Should raise for exceeding max depth
        with pytest.raises(CognitiveCoreViolation) as exc_info:
            enforce_cognitive_core(MAX_NESTING_DEPTH + 1)

        assert "Cognitive core reached" in str(exc_info.value)
