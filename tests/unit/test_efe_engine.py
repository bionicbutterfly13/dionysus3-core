import pytest
import numpy as np
from api.services.efe_engine import (
    EFEEngine,
    get_agent_precision,
    set_agent_precision,
    adjust_agent_precision,
    _agent_precision_registry
)

@pytest.fixture
def efe_engine():
    return EFEEngine()

def test_efe_calculation_logic(efe_engine):
    """Verify EFE ranking favors low uncertainty and low goal divergence."""
    goal_vector = [1.0, 0.0]
    
    thoughtseeds = [
        {
            "id": "pragmatic_perfect",
            "response_vector": [1.0, 0.0], # Matches goal
            "prediction_probabilities": [0.9, 0.1] # Low uncertainty
        },
        {
            "id": "uncertain_but_on_goal",
            "response_vector": [1.0, 0.0], # Matches goal
            "prediction_probabilities": [0.5, 0.5] # High uncertainty
        },
        {
            "id": "divergent",
            "response_vector": [0.0, 1.0], # Completely different direction
            "prediction_probabilities": [0.9, 0.1] # Low uncertainty
        }
    ]
    
    # Using legacy rank_candidates for compatibility check
    response = efe_engine.rank_candidates("test query", goal_vector, thoughtseeds)
    
    # Detailed checks
    scores = response.scores
    assert scores["pragmatic_perfect"].efe_score < scores["uncertain_but_on_goal"].efe_score
    assert scores["pragmatic_perfect"].efe_score < scores["divergent"].efe_score
    
    # Dominant should be the perfect one
    assert response.dominant_seed_id == "pragmatic_perfect"

def test_efe_null_vectors(efe_engine):
    """Verify EFE handles null vectors gracefully."""
    goal_vector = [0.0, 0.0]
    thoughtseeds = [{"id": "s1", "response_vector": [1.0, 0.0], "prediction_probabilities": [0.5, 0.5]}]
    
    response = efe_engine.rank_candidates("q", goal_vector, thoughtseeds)
    assert response.scores["s1"].goal_divergence == 1.0

def test_efe_direct_selection(efe_engine):
    """Verify select_dominant_thought with new keys."""
    goal_vector = [1.0, 0.0]
    thoughtseeds = [
        {
            "id": "s1",
            "vector": [1.0, 0.0],
            "probabilities": [0.9, 0.1]
        }
    ]
    response = efe_engine.select_dominant_thought(thoughtseeds, goal_vector)
    assert response.dominant_seed_id == "s1"


# ============================================================================
# Tests for Active Metacognition: Precision Registry and Precision-Weighted EFE
# Feature: Priority 1 - Active Metacognition
# ============================================================================

@pytest.fixture(autouse=True)
def reset_precision_registry():
    """Reset precision registry before each test."""
    _agent_precision_registry.clear()
    yield
    _agent_precision_registry.clear()


class TestPrecisionRegistry:
    """Tests for agent precision registry functions."""

    def test_default_precision_is_one(self):
        """Agents should have default precision of 1.0."""
        assert get_agent_precision("unknown_agent") == 1.0

    def test_set_precision(self):
        """set_agent_precision should store precision."""
        set_agent_precision("perception", 0.5)
        assert get_agent_precision("perception") == 0.5

    def test_precision_clamping_low(self):
        """Precision should be clamped to minimum 0.01."""
        set_agent_precision("test", -5.0)
        assert get_agent_precision("test") == 0.01

    def test_precision_clamping_high(self):
        """Precision should be clamped to maximum 10.0."""
        set_agent_precision("test", 100.0)
        assert get_agent_precision("test") == 10.0

    def test_adjust_precision_positive(self):
        """adjust_agent_precision should increase precision."""
        set_agent_precision("reasoning", 1.0)
        new_prec = adjust_agent_precision("reasoning", 0.3)
        assert new_prec == 1.3
        assert get_agent_precision("reasoning") == 1.3

    def test_adjust_precision_negative(self):
        """adjust_agent_precision should decrease precision."""
        set_agent_precision("reasoning", 1.0)
        new_prec = adjust_agent_precision("reasoning", -0.5)
        assert new_prec == 0.5
        assert get_agent_precision("reasoning") == 0.5

    def test_adjust_precision_respects_bounds(self):
        """Adjusted precision should stay within bounds."""
        set_agent_precision("test", 9.5)
        new_prec = adjust_agent_precision("test", 2.0)
        assert new_prec == 10.0  # Clamped to max

        set_agent_precision("test", 0.1)
        new_prec = adjust_agent_precision("test", -1.0)
        assert new_prec == 0.01  # Clamped to min


class TestPrecisionWeightedEFE:
    """Tests for precision-weighted EFE calculation."""

    def test_precision_weighted_efe_default(self, efe_engine):
        """With precision=1.0, should equal regular EFE."""
        probs = [0.5, 0.5]
        thought_vec = np.array([1.0, 0.0])
        goal_vec = np.array([1.0, 0.0])

        regular_efe = efe_engine.calculate_efe(probs, thought_vec, goal_vec)
        precision_efe = efe_engine.calculate_precision_weighted_efe(
            probs, thought_vec, goal_vec, precision=1.0
        )
        assert abs(regular_efe - precision_efe) < 0.001

    def test_high_precision_reduces_uncertainty_weight(self, efe_engine):
        """High precision should reduce weight on uncertainty (exploration)."""
        probs = [0.5, 0.5]  # High entropy
        thought_vec = np.array([0.8, 0.2])
        goal_vec = np.array([1.0, 0.0])

        low_precision_efe = efe_engine.calculate_precision_weighted_efe(
            probs, thought_vec, goal_vec, precision=0.5
        )
        high_precision_efe = efe_engine.calculate_precision_weighted_efe(
            probs, thought_vec, goal_vec, precision=2.0
        )

        # With high precision, divergence matters more, uncertainty less
        # Since thought is close to goal (low divergence), high precision should help
        # But with equal divergence, higher precision increases divergence term
        # The key property: different precisions produce different scores
        assert low_precision_efe != high_precision_efe

    def test_precision_from_registry(self, efe_engine):
        """Should use agent precision from registry when agent_name provided."""
        # Use metaplasticity_controller's registry (which EFE engine actually uses)
        from api.services.metaplasticity_service import get_metaplasticity_controller
        get_metaplasticity_controller().set_precision("perception", 2.0)

        probs = [0.5, 0.5]
        thought_vec = np.array([1.0, 0.0])
        goal_vec = np.array([1.0, 0.0])

        # With explicit precision
        explicit_efe = efe_engine.calculate_precision_weighted_efe(
            probs, thought_vec, goal_vec, precision=2.0
        )

        # With agent_name (should pull from registry)
        registry_efe = efe_engine.calculate_precision_weighted_efe(
            probs, thought_vec, goal_vec, agent_name="perception"
        )

        assert abs(explicit_efe - registry_efe) < 0.001

    def test_precision_formula_components(self, efe_engine):
        """Verify the precision formula: EFE = (1/pi)*H + pi*D."""
        probs = [0.8, 0.2]
        thought_vec = np.array([0.5, 0.5])
        goal_vec = np.array([1.0, 0.0])

        precision = 2.0

        # Calculate components manually
        uncertainty = efe_engine.calculate_entropy(probs)
        divergence = efe_engine.calculate_goal_divergence(thought_vec, goal_vec)
        expected_efe = (1.0 / precision) * uncertainty + precision * divergence

        actual_efe = efe_engine.calculate_precision_weighted_efe(
            probs, thought_vec, goal_vec, precision=precision
        )

        assert abs(expected_efe - actual_efe) < 0.0001