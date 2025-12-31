"""
Unit Tests for EpistemicGainService

Feature: 040-metacognitive-particles
Tasks: T040

Tests epistemic gain ("Aha!" moment) detection.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
import numpy as np
from api.services.epistemic_gain_service import (
    EpistemicGainService,
    EpistemicGainEvent,
    EPISTEMIC_GAIN_THRESHOLD
)
from api.models.belief_state import BeliefState


class TestEpistemicGainService:
    """Test suite for EpistemicGainService."""

    @pytest.fixture
    def service(self):
        """Create EpistemicGainService instance."""
        return EpistemicGainService()

    @pytest.fixture
    def high_entropy_belief(self):
        """Create high entropy (uncertain) belief state."""
        return BeliefState(
            mean=[0.0],
            precision=[[0.1]]  # Low precision = high entropy
        )

    @pytest.fixture
    def low_entropy_belief(self):
        """Create low entropy (certain) belief state."""
        return BeliefState(
            mean=[0.0],
            precision=[[10.0]]  # High precision = low entropy
        )

    @pytest.mark.asyncio
    async def test_check_gain_significant_reduction(self, service, high_entropy_belief, low_entropy_belief):
        """Test detection of significant epistemic gain."""
        event = await service.check_gain(
            prior_belief=high_entropy_belief,
            posterior_belief=low_entropy_belief
        )

        assert event is not None
        assert isinstance(event, EpistemicGainEvent)
        assert event.magnitude > 0.0
        assert event.prior_entropy > event.posterior_entropy

    @pytest.mark.asyncio
    async def test_check_gain_no_significant_change(self, service):
        """Test no gain detected for insignificant entropy change."""
        belief1 = BeliefState(mean=[0.0], precision=[[1.0]])
        belief2 = BeliefState(mean=[0.0], precision=[[1.1]])  # Minimal change

        event = await service.check_gain(
            prior_belief=belief1,
            posterior_belief=belief2
        )

        assert event is None

    @pytest.mark.asyncio
    async def test_check_gain_entropy_increase(self, service, high_entropy_belief, low_entropy_belief):
        """Test no gain when entropy increases (more uncertain)."""
        event = await service.check_gain(
            prior_belief=low_entropy_belief,
            posterior_belief=high_entropy_belief  # Reversed - entropy increases
        )

        assert event is None

    @pytest.mark.asyncio
    async def test_check_gain_custom_threshold(self, service, high_entropy_belief, low_entropy_belief):
        """Test custom threshold parameter."""
        # Very high threshold - no gain detected
        event = await service.check_gain(
            prior_belief=high_entropy_belief,
            posterior_belief=low_entropy_belief,
            threshold=0.99
        )
        assert event is None

        # Very low threshold - gain detected
        event = await service.check_gain(
            prior_belief=high_entropy_belief,
            posterior_belief=low_entropy_belief,
            threshold=0.01
        )
        assert event is not None

    @pytest.mark.asyncio
    async def test_compute_magnitude(self, service):
        """Test magnitude calculation."""
        prior_entropy = 2.0
        posterior_entropy = 1.0

        magnitude = service._compute_magnitude(prior_entropy, posterior_entropy)

        # (2.0 - 1.0) / 2.0 = 0.5
        assert abs(magnitude - 0.5) < 0.01

    @pytest.mark.asyncio
    async def test_compute_magnitude_zero_prior(self, service):
        """Test magnitude with zero prior entropy."""
        magnitude = service._compute_magnitude(0.0, 1.0)
        assert magnitude == 0.0

    @pytest.mark.asyncio
    async def test_compute_magnitude_negative_reduction(self, service):
        """Test magnitude is clamped for negative reduction."""
        magnitude = service._compute_magnitude(1.0, 2.0)  # Entropy increased
        assert magnitude == 0.0

    @pytest.mark.asyncio
    async def test_noetic_quality_detection(self, service):
        """Test noetic quality detection."""
        # High precision increase without proportional entropy reduction
        prior = BeliefState(mean=[0.0], precision=[[1.0]])
        posterior = BeliefState(mean=[0.0], precision=[[5.0]])  # 5x precision

        noetic = service._detect_noetic_quality(prior, posterior, magnitude=0.1)

        # Should be noetic - precision increased much more than entropy reduced
        assert noetic is True

    @pytest.mark.asyncio
    async def test_non_noetic_gain(self, service):
        """Test non-noetic gain (proportional evidence)."""
        prior = BeliefState(mean=[0.0], precision=[[1.0]])
        posterior = BeliefState(mean=[0.0], precision=[[1.5]])  # Modest increase

        noetic = service._detect_noetic_quality(prior, posterior, magnitude=0.5)

        # Should not be noetic - precision increase proportional to magnitude
        assert noetic is False


class TestAdaptiveThreshold:
    """Test adaptive threshold functionality."""

    @pytest.fixture
    def adaptive_service(self):
        """Create service with adaptive threshold enabled."""
        return EpistemicGainService(adaptive=True, history_size=10)

    @pytest.mark.asyncio
    async def test_current_threshold_no_history(self, adaptive_service):
        """Test threshold without history uses base threshold."""
        threshold = adaptive_service.current_threshold
        assert threshold == adaptive_service.base_threshold

    @pytest.mark.asyncio
    async def test_current_threshold_with_history(self, adaptive_service):
        """Test threshold adapts with history."""
        # Add some gain history
        for _ in range(15):
            adaptive_service.gain_history.append(0.4)

        threshold = adaptive_service.current_threshold

        # Should be different from base (adaptive)
        # mean(0.4) + std(0) = 0.4
        assert abs(threshold - 0.4) < 0.01

    @pytest.mark.asyncio
    async def test_history_stats(self, adaptive_service):
        """Test history statistics."""
        adaptive_service.gain_history.extend([0.3, 0.4, 0.5])

        stats = adaptive_service.history_stats

        assert stats["count"] == 3
        assert abs(stats["mean"] - 0.4) < 0.01

    @pytest.mark.asyncio
    async def test_reset_history(self, adaptive_service):
        """Test resetting gain history."""
        adaptive_service.gain_history.extend([0.3, 0.4, 0.5])
        adaptive_service.reset_history()

        assert len(adaptive_service.gain_history) == 0


class TestEpistemicGainEvent:
    """Test EpistemicGainEvent model."""

    def test_event_creation(self):
        """Test creating an epistemic gain event."""
        event = EpistemicGainEvent(
            id="test-id",
            magnitude=0.5,
            prior_entropy=2.0,
            posterior_entropy=1.0,
            noetic_quality=False
        )

        assert event.id == "test-id"
        assert event.magnitude == 0.5
        assert event.prior_entropy == 2.0
        assert event.posterior_entropy == 1.0
        assert event.noetic_quality is False
        assert event.detected_at is not None


class TestDefaultThreshold:
    """Test default threshold constant."""

    def test_default_threshold_value(self):
        """Test EPISTEMIC_GAIN_THRESHOLD constant."""
        assert EPISTEMIC_GAIN_THRESHOLD == 0.3

    def test_service_default_threshold(self):
        """Test service uses default threshold."""
        service = EpistemicGainService()
        assert service.base_threshold == EPISTEMIC_GAIN_THRESHOLD
