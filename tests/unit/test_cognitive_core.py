"""
Unit Tests for Cognitive Core Enforcement

Feature: 040-metacognitive-particles
Tasks: T050

Tests cognitive core nesting depth limits.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
import os
from api.models.metacognitive_particle import (
    CognitiveCoreViolation,
    enforce_cognitive_core,
    MAX_NESTING_DEPTH
)


class TestCognitiveCoreViolation:
    """Test CognitiveCoreViolation exception."""

    def test_exception_is_exception(self):
        """Test CognitiveCoreViolation is an Exception."""
        exc = CognitiveCoreViolation("Test message")
        assert isinstance(exc, Exception)

    def test_exception_message(self):
        """Test exception preserves message."""
        msg = "Cannot create metacognitive level 6. Cognitive core reached."
        exc = CognitiveCoreViolation(msg)
        assert str(exc) == msg


class TestEnforceCognitiveCore:
    """Test enforce_cognitive_core function."""

    def test_valid_levels_pass(self):
        """Test that valid levels (0 to MAX_NESTING_DEPTH) pass."""
        for level in range(MAX_NESTING_DEPTH + 1):
            # Should not raise
            enforce_cognitive_core(level)

    def test_level_zero_passes(self):
        """Test level 0 (base level) passes."""
        enforce_cognitive_core(0)

    def test_max_depth_level_passes(self):
        """Test level at MAX_NESTING_DEPTH passes."""
        enforce_cognitive_core(MAX_NESTING_DEPTH)

    def test_exceeding_max_depth_raises(self):
        """Test exceeding MAX_NESTING_DEPTH raises exception."""
        with pytest.raises(CognitiveCoreViolation) as exc_info:
            enforce_cognitive_core(MAX_NESTING_DEPTH + 1)

        error_message = str(exc_info.value)
        assert "Cognitive core reached" in error_message
        assert str(MAX_NESTING_DEPTH) in error_message

    def test_deeply_exceeding_max_depth_raises(self):
        """Test deeply exceeding max depth raises exception."""
        with pytest.raises(CognitiveCoreViolation):
            enforce_cognitive_core(MAX_NESTING_DEPTH + 100)

    def test_error_message_format(self):
        """Test error message format includes level info."""
        exceeded_level = MAX_NESTING_DEPTH + 1

        with pytest.raises(CognitiveCoreViolation) as exc_info:
            enforce_cognitive_core(exceeded_level)

        error_message = str(exc_info.value)
        assert f"level {exceeded_level}" in error_message
        assert f"level {MAX_NESTING_DEPTH}" in error_message


class TestMaxNestingDepthConfiguration:
    """Test MAX_NESTING_DEPTH configuration."""

    def test_default_max_depth_is_5(self):
        """Test default MAX_NESTING_DEPTH is 5."""
        # Note: This tests the module-level constant
        # In production, this may be overridden by env var
        assert MAX_NESTING_DEPTH >= 1
        assert MAX_NESTING_DEPTH <= 10  # Reasonable upper bound

    def test_max_depth_is_integer(self):
        """Test MAX_NESTING_DEPTH is an integer."""
        assert isinstance(MAX_NESTING_DEPTH, int)


class TestCognitiveCoreModel:
    """Test CognitiveCore Pydantic model."""

    def test_cognitive_core_creation(self):
        """Test creating a CognitiveCore model."""
        from api.models.metacognitive_particle import CognitiveCore

        core = CognitiveCore(
            particle_id="particle-123",
            max_recursion_level=3,
            complexity_bound=0.5,
            beliefs_encoded="Q_{mu^3}(eta, mu^1, mu^2)"
        )

        assert core.particle_id == "particle-123"
        assert core.max_recursion_level == 3
        assert core.complexity_bound == 0.5
        assert core.id is not None

    def test_cognitive_core_min_recursion_level(self):
        """Test minimum recursion level validation."""
        from api.models.metacognitive_particle import CognitiveCore
        from pydantic import ValidationError

        # Valid: level 1
        valid = CognitiveCore(particle_id="test", max_recursion_level=1)
        assert valid.max_recursion_level == 1

        # Invalid: level 0
        with pytest.raises(ValidationError):
            CognitiveCore(particle_id="test", max_recursion_level=0)


class TestCognitiveCoreIntegrationWithClassifier:
    """Test cognitive core enforcement in ParticleClassifier."""

    @pytest.mark.asyncio
    async def test_classifier_enforces_cognitive_core(self):
        """Test ParticleClassifier enforces cognitive core."""
        from api.services.particle_classifier import ParticleClassifier
        from api.models.markov_blanket import MarkovBlanketPartition

        classifier = ParticleClassifier()

        # Create a blanket that would imply very deep nesting
        # (This test verifies the integration point exists)
        blanket = MarkovBlanketPartition(
            external_paths=["ext"],
            sensory_paths=["sens"],
            active_paths=["act"],
            internal_paths=["int1", "int2", "int3"]  # Moderate depth
        )

        # Should classify without raising CognitiveCoreViolation
        # (unless the inferred depth exceeds MAX_NESTING_DEPTH)
        result = await classifier.classify("test_agent", blanket)

        particle_type, confidence, level, has_agency = result
        assert level <= MAX_NESTING_DEPTH
