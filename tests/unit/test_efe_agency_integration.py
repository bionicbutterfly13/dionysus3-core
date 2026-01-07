"""
Unit tests for EFE Engine agency integration
Feature: 038-thoughtseeds-framework (Priority 3)

Tests the integration of agency-weighted EFE calculation.
"""

import pytest
import numpy as np

from api.services.efe_engine import EFEEngine, get_efe_engine
from api.services.agency_detector import get_agency_detector


@pytest.fixture
def efe_engine():
    """Create fresh EFE engine."""
    return EFEEngine()


@pytest.fixture
def high_agency_states():
    """Internal and active states with high coupling."""
    np.random.seed(42)
    mu = np.random.randn(50, 2)
    a = mu * 0.9 + np.random.randn(50, 2) * 0.1
    return mu, a


@pytest.fixture
def low_agency_states():
    """Internal and active states with low coupling."""
    np.random.seed(42)
    mu = np.random.randn(50, 2)
    a = np.random.randn(50, 2)  # Independent
    return mu, a


class TestAgencyWeightedEFE:
    """Test agency-weighted EFE calculation."""

    def test_high_agency_reduces_efe(self, efe_engine):
        """High agency score should reduce effective EFE."""
        probs = [0.5, 0.5]
        thought = np.array([1.0, 0.0])
        goal = np.array([0.8, 0.2])
        
        # Calculate with high vs low agency
        efe_high_agency = efe_engine.agency_weighted_efe(probs, thought, goal, agency_score=1.5)
        efe_low_agency = efe_engine.agency_weighted_efe(probs, thought, goal, agency_score=0.1)
        
        # High agency should yield lower EFE (more confidence)
        assert efe_high_agency < efe_low_agency

    def test_zero_agency_no_reduction(self, efe_engine):
        """Zero agency score should not reduce EFE."""
        probs = [0.5, 0.5]
        thought = np.array([1.0, 0.0])
        goal = np.array([0.8, 0.2])
        
        base_efe = efe_engine.calculate_efe(probs, thought, goal)
        weighted_efe = efe_engine.agency_weighted_efe(probs, thought, goal, agency_score=0.0)
        
        # Zero agency should give approximately same EFE
        assert abs(base_efe - weighted_efe) < 0.01

    def test_agency_weight_parameter(self, efe_engine):
        """Agency weight parameter should control reduction magnitude."""
        probs = [0.5, 0.5]
        thought = np.array([1.0, 0.0])
        goal = np.array([0.8, 0.2])
        
        # Same agency score, different weights
        efe_low_weight = efe_engine.agency_weighted_efe(
            probs, thought, goal, agency_score=1.0, agency_weight=0.1
        )
        efe_high_weight = efe_engine.agency_weighted_efe(
            probs, thought, goal, agency_score=1.0, agency_weight=0.5
        )
        
        # Higher weight should produce more reduction
        assert efe_high_weight < efe_low_weight

    def test_weighted_efe_always_positive(self, efe_engine):
        """Weighted EFE should always be non-negative."""
        probs = [0.9, 0.1]
        thought = np.array([1.0, 0.0])
        goal = np.array([1.0, 0.0])  # Perfect alignment
        
        weighted_efe = efe_engine.agency_weighted_efe(
            probs, thought, goal, agency_score=2.0, agency_weight=0.5
        )
        
        assert weighted_efe >= 0


class TestAgencyWeightedSelection:
    """Test thought selection with agency weighting."""

    def test_selection_with_agency(self, efe_engine, high_agency_states):
        """Selection should work with agency-weighted EFE."""
        mu, a = high_agency_states
        
        candidates = [
            {"id": "thought_1", "vector": [1.0, 0.0], "probabilities": [0.8, 0.2]},
            {"id": "thought_2", "vector": [0.5, 0.5], "probabilities": [0.5, 0.5]},
        ]
        goal_vector = [1.0, 0.0]
        
        response = efe_engine.select_dominant_thought_with_agency(
            candidates, goal_vector, mu, a
        )
        
        assert response.dominant_seed_id in ["thought_1", "thought_2"]
        assert len(response.scores) == 2

    def test_selection_prefers_goal_aligned(self, efe_engine, high_agency_states):
        """Selection should still prefer goal-aligned thoughts."""
        mu, a = high_agency_states
        
        candidates = [
            {"id": "aligned", "vector": [1.0, 0.0], "probabilities": [0.8, 0.2]},
            {"id": "misaligned", "vector": [0.0, 1.0], "probabilities": [0.8, 0.2]},
        ]
        goal_vector = [1.0, 0.0]
        
        response = efe_engine.select_dominant_thought_with_agency(
            candidates, goal_vector, mu, a
        )
        
        # Aligned thought should win
        assert response.dominant_seed_id == "aligned"

    def test_empty_candidates(self, efe_engine, high_agency_states):
        """Empty candidates should return 'none'."""
        mu, a = high_agency_states
        
        response = efe_engine.select_dominant_thought_with_agency(
            [], [1.0, 0.0], mu, a
        )
        
        assert response.dominant_seed_id == "none"

    def test_scores_contain_all_candidates(self, efe_engine, high_agency_states):
        """Response should contain scores for all candidates."""
        mu, a = high_agency_states
        
        candidates = [
            {"id": "t1", "vector": [1.0, 0.0], "probabilities": [0.7, 0.3]},
            {"id": "t2", "vector": [0.5, 0.5], "probabilities": [0.5, 0.5]},
            {"id": "t3", "vector": [0.0, 1.0], "probabilities": [0.6, 0.4]},
        ]
        
        response = efe_engine.select_dominant_thought_with_agency(
            candidates, [1.0, 0.0], mu, a
        )
        
        assert set(response.scores.keys()) == {"t1", "t2", "t3"}


class TestAgencyIntegration:
    """Test full integration between agency detector and EFE engine."""

    def test_detector_integration(self, high_agency_states):
        """Agency detector should integrate with EFE engine."""
        mu, a = high_agency_states
        
        detector = get_agency_detector()
        engine = get_efe_engine()
        
        # Calculate agency score
        agency_score = detector.calculate_agency_score(mu, a)
        
        # Use in EFE calculation
        weighted_efe = engine.agency_weighted_efe(
            [0.5, 0.5],
            np.array([1.0, 0.0]),
            np.array([0.8, 0.2]),
            agency_score
        )
        
        assert weighted_efe > 0
        assert agency_score > 0

    def test_full_pipeline(self, high_agency_states):
        """Test full agency-aware thought selection pipeline."""
        mu, a = high_agency_states
        engine = EFEEngine()
        
        # Simulate thought selection scenario
        candidates = [
            {
                "id": "confident_thought",
                "vector": [0.9, 0.1],
                "probabilities": [0.85, 0.15]
            },
            {
                "id": "uncertain_thought",
                "vector": [0.8, 0.2],
                "probabilities": [0.5, 0.5]
            },
        ]
        
        response = engine.select_dominant_thought_with_agency(
            candidates,
            goal_vector=[1.0, 0.0],
            internal_states=mu,
            active_states=a,
            agency_weight=0.3
        )
        
        # Confident, goal-aligned thought should win
        assert response.dominant_seed_id == "confident_thought"
        
        # All scores should be computed
        for seed_id, result in response.scores.items():
            assert result.efe_score >= 0
            assert result.uncertainty >= 0
            assert result.goal_divergence >= 0
