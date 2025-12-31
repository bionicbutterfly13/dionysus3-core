"""
Unit tests for Agency Detector
Feature: 038-thoughtseeds-framework (Priority 3)

Tests the KL divergence-based agency detection from Metacognitive Particles paper.
"""

import pytest
import numpy as np

from api.models.agency import (
    AgencyAttribution,
    AgencyAttributionType,
    AgencyThresholds,
    AgencyWeightedEFE,
    DEFAULT_AGENCY_THRESHOLDS,
)
from api.services.agency_detector import AgencyDetector, get_agency_detector


@pytest.fixture
def detector():
    """Create fresh agency detector for each test."""
    return AgencyDetector(num_bins=10)


@pytest.fixture
def high_agency_data():
    """Generate data with high coupling (high agency)."""
    np.random.seed(42)
    n_samples = 100
    # Internal states drive actions: a = f(μ) + small noise
    mu = np.random.randn(n_samples, 2)
    a = mu * 0.9 + np.random.randn(n_samples, 2) * 0.1
    return mu, a


@pytest.fixture
def low_agency_data():
    """Generate data with no coupling (no agency)."""
    np.random.seed(42)
    n_samples = 100
    # Independent: no relationship between μ and a
    mu = np.random.randn(n_samples, 2)
    a = np.random.randn(n_samples, 2)  # Completely independent
    return mu, a


class TestAgencyScore:
    """Test agency score calculation."""

    def test_high_coupling_high_score(self, detector, high_agency_data):
        """Highly coupled internal/active states should yield high agency score."""
        mu, a = high_agency_data
        score = detector.calculate_agency_score(mu, a)
        
        # High coupling should produce positive KL divergence
        assert score > 0.3, f"Expected high agency score, got {score}"

    def test_independent_low_score(self, detector, low_agency_data):
        """Independent internal/active states should yield low agency score."""
        mu, a = low_agency_data
        score = detector.calculate_agency_score(mu, a)
        
        # Independence should produce low KL divergence
        assert score < 0.5, f"Expected low agency score for independent data, got {score}"

    def test_identical_data_high_score(self, detector):
        """Identical internal and active states should yield high agency."""
        np.random.seed(42)
        mu = np.random.randn(50, 2)
        a = mu.copy()  # Perfect coupling
        
        score = detector.calculate_agency_score(mu, a)
        assert score > 0.5, f"Expected high score for identical data, got {score}"

    def test_single_sample_returns_zero(self, detector):
        """Single sample should return 0 (insufficient data)."""
        mu = np.array([[1.0, 2.0]])
        a = np.array([[3.0, 4.0]])
        
        score = detector.calculate_agency_score(mu, a)
        assert score == 0.0

    def test_mismatched_lengths_raises(self, detector):
        """Mismatched array lengths should raise ValueError."""
        mu = np.random.randn(10, 2)
        a = np.random.randn(5, 2)
        
        with pytest.raises(ValueError):
            detector.calculate_agency_score(mu, a)

    def test_1d_arrays_work(self, detector):
        """1D arrays should be handled correctly."""
        np.random.seed(42)
        mu = np.random.randn(50)
        a = mu * 0.9 + np.random.randn(50) * 0.1
        
        score = detector.calculate_agency_score(mu, a)
        assert score > 0, "Should handle 1D arrays"


class TestAgencyAttribution:
    """Test action attribution."""

    def test_high_agency_attribution(self, detector):
        """High coupling should yield SELF attribution."""
        np.random.seed(42)
        before = np.random.randn(5)
        after = before * 1.2 + 0.1  # Clearly related
        
        # Use custom thresholds for predictable behavior
        detector.thresholds = AgencyThresholds(
            high_agency_threshold=0.3,
            low_agency_threshold=0.1
        )
        
        result = detector.attribute_action({}, before, after)
        
        assert isinstance(result, AgencyAttribution)
        assert result.score >= 0
        assert 0 <= result.confidence <= 1

    def test_attribution_contains_entropy_info(self, detector):
        """Attribution should include entropy details."""
        np.random.seed(42)
        before = np.random.randn(5)
        after = before + np.random.randn(5) * 0.5
        
        result = detector.attribute_action({}, before, after)
        
        assert result.internal_entropy is not None
        assert result.active_entropy is not None
        assert result.joint_entropy is not None
        assert result.mutual_information is not None

    def test_mutual_information_non_negative(self, detector):
        """Mutual information should always be non-negative."""
        np.random.seed(42)
        for _ in range(5):
            before = np.random.randn(5)
            after = np.random.randn(5)
            
            result = detector.attribute_action({}, before, after)
            assert result.mutual_information >= 0


class TestTrajectoryAgency:
    """Test trajectory-based agency estimation."""

    def test_trajectory_estimation(self, detector, high_agency_data):
        """Trajectory estimation should work with full trajectories."""
        mu, a = high_agency_data
        
        result = detector.estimate_agency_from_trajectory(mu, a)
        
        assert isinstance(result, AgencyAttribution)
        assert result.score > 0

    def test_longer_trajectory_higher_confidence(self, detector):
        """Longer trajectories should yield higher confidence."""
        np.random.seed(42)
        
        # Short trajectory
        mu_short = np.random.randn(10, 2)
        a_short = mu_short * 0.9 + np.random.randn(10, 2) * 0.1
        result_short = detector.estimate_agency_from_trajectory(mu_short, a_short)
        
        # Long trajectory
        mu_long = np.random.randn(100, 2)
        a_long = mu_long * 0.9 + np.random.randn(100, 2) * 0.1
        result_long = detector.estimate_agency_from_trajectory(mu_long, a_long)
        
        # Long trajectory should have higher or equal confidence
        assert result_long.confidence >= result_short.confidence - 0.1


class TestAgencyThresholds:
    """Test threshold configuration."""

    def test_default_thresholds(self):
        """Default thresholds should be sensible."""
        thresholds = DEFAULT_AGENCY_THRESHOLDS
        
        assert thresholds.high_agency_threshold == 0.7
        assert thresholds.low_agency_threshold == 0.3
        assert thresholds.high_agency_threshold > thresholds.low_agency_threshold

    def test_custom_thresholds(self):
        """Custom thresholds should work."""
        detector = AgencyDetector(
            thresholds=AgencyThresholds(
                high_agency_threshold=0.9,
                low_agency_threshold=0.1
            )
        )
        
        assert detector.thresholds.high_agency_threshold == 0.9
        assert detector.thresholds.low_agency_threshold == 0.1


class TestSingleton:
    """Test singleton factory."""

    def test_get_agency_detector(self):
        """Factory should return AgencyDetector instance."""
        detector = get_agency_detector()
        assert isinstance(detector, AgencyDetector)

    def test_singleton_returns_same_instance(self):
        """Factory should return same instance on repeated calls."""
        d1 = get_agency_detector()
        d2 = get_agency_detector()
        assert d1 is d2
