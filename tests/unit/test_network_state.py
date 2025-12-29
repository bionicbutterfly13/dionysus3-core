"""
Unit tests for Network State models and services.

Part of 034-network-self-modeling feature.
Tests T008-T009: NetworkState model validation and delta calculation.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

from api.models.network_state import (
    NetworkState,
    NetworkStateDiff,
    NetworkStateConfig,
    SnapshotTrigger,
    AdaptationMode,
    SelfModelState,
    TimingState,
    ValueChange,
    get_network_state_config,
)
from api.services.network_state_service import NetworkStateService
from api.utils.math_utils import (
    weight_bounds_enforcer,
    sigmoid_squash,
    hebbian_update,
    weight_decay,
    treur_state_update,
)


# ---------------------------------------------------------------------------
# T008: NetworkState Model Validation Tests
# ---------------------------------------------------------------------------


class TestNetworkStateModel:
    """Tests for NetworkState Pydantic model validation (T008)."""

    def test_create_network_state_basic(self):
        """Test basic NetworkState creation with required fields."""
        state = NetworkState(
            agent_id="test-agent-001",
            trigger=SnapshotTrigger.CHANGE_EVENT,
        )

        assert state.agent_id == "test-agent-001"
        assert state.trigger == SnapshotTrigger.CHANGE_EVENT
        assert state.id is not None
        assert state.timestamp is not None
        assert state.connection_weights == {}
        assert state.thresholds == {}
        assert state.speed_factors == {}

    def test_create_network_state_with_wth_values(self):
        """Test NetworkState with W/T/H values."""
        state = NetworkState(
            agent_id="perception-agent-001",
            trigger=SnapshotTrigger.DAILY_CHECKPOINT,
            connection_weights={"input->hidden": 0.75, "hidden->output": 0.6},
            thresholds={"hidden": 0.5, "output": 0.3},
            speed_factors={"hidden": 0.1, "output": 0.05},
        )

        assert state.connection_weights["input->hidden"] == 0.75
        assert state.thresholds["hidden"] == 0.5
        assert state.speed_factors["output"] == 0.05

    def test_network_state_checksum(self):
        """Test checksum computation for integrity verification."""
        state = NetworkState(
            agent_id="test-agent",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 0.5},
        )

        checksum = state.compute_checksum()
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex digest

        # Same state should produce same checksum
        assert state.compute_checksum() == checksum

    def test_network_state_checksum_changes(self):
        """Test that checksum changes when state changes."""
        state1 = NetworkState(
            agent_id="test-agent",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 0.5},
        )
        state2 = NetworkState(
            agent_id="test-agent",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 0.6},  # Different weight
        )

        assert state1.compute_checksum() != state2.compute_checksum()

    def test_snapshot_trigger_enum_values(self):
        """Test SnapshotTrigger enum has correct values."""
        assert SnapshotTrigger.CHANGE_EVENT.value == "CHANGE_EVENT"
        assert SnapshotTrigger.DAILY_CHECKPOINT.value == "DAILY_CHECKPOINT"
        assert SnapshotTrigger.MANUAL.value == "MANUAL"

    def test_adaptation_mode_enum_values(self):
        """Test AdaptationMode enum has correct values."""
        assert AdaptationMode.ACCELERATING.value == "ACCELERATING"
        assert AdaptationMode.STABLE.value == "STABLE"
        assert AdaptationMode.DECELERATING.value == "DECELERATING"
        assert AdaptationMode.STRESSED.value == "STRESSED"

    def test_network_state_serialization(self):
        """Test NetworkState JSON serialization/deserialization."""
        state = NetworkState(
            agent_id="test-agent",
            trigger=SnapshotTrigger.CHANGE_EVENT,
            connection_weights={"a->b": 0.5},
            thresholds={"a": 0.3},
            speed_factors={"a": 0.1},
            delta_from_previous=0.08,
        )

        # Serialize
        json_data = state.model_dump()
        assert json_data["agent_id"] == "test-agent"
        assert json_data["trigger"] == "CHANGE_EVENT"

        # Deserialize
        restored = NetworkState.model_validate(json_data)
        assert restored.agent_id == state.agent_id
        assert restored.connection_weights == state.connection_weights


# ---------------------------------------------------------------------------
# T009: Delta Calculation Tests
# ---------------------------------------------------------------------------


class TestDeltaCalculation:
    """Tests for L2 norm delta calculation with 5% threshold (T009)."""

    def test_state_to_vector_empty(self):
        """Test state_to_vector with empty state."""
        service = NetworkStateService()
        state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
        )

        vec = service.state_to_vector(state)
        assert vec.shape == (1,)  # Returns [0.0] for empty state
        assert vec[0] == 0.0

    def test_state_to_vector_with_values(self):
        """Test state_to_vector with W/T/H values."""
        service = NetworkStateService()
        state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 0.5, "b->c": 0.7},
            thresholds={"a": 0.3},
            speed_factors={"a": 0.1, "b": 0.2},
        )

        vec = service.state_to_vector(state)
        # Should have 2 weights + 1 threshold + 2 speeds = 5 values
        assert vec.shape == (5,)

    def test_state_to_vector_sorted_keys(self):
        """Test that state_to_vector uses sorted keys for consistency."""
        service = NetworkStateService()

        # Create two states with same values but different key order
        state1 = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 0.5, "c->d": 0.7},
        )
        state2 = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"c->d": 0.7, "a->b": 0.5},
        )

        vec1 = service.state_to_vector(state1)
        vec2 = service.state_to_vector(state2)

        np.testing.assert_array_equal(vec1, vec2)

    def test_calculate_delta_zero_state(self):
        """Test delta calculation from zero state always returns 1.0."""
        service = NetworkStateService()

        old_state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
        )
        new_state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.CHANGE_EVENT,
            connection_weights={"a->b": 0.5},
        )

        delta = service.calculate_delta(old_state, new_state)
        assert delta == 1.0  # Force snapshot from zero

    def test_calculate_delta_identical_states(self):
        """Test delta calculation for identical states returns 0."""
        service = NetworkStateService()

        state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 0.5},
            thresholds={"a": 0.3},
        )

        delta = service.calculate_delta(state, state)
        assert delta == 0.0

    def test_calculate_delta_5_percent_threshold(self):
        """Test that 5% threshold is correctly applied."""
        service = NetworkStateService()

        old_state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 1.0},
        )

        # 4% change - below threshold
        new_state_below = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.CHANGE_EVENT,
            connection_weights={"a->b": 1.04},
        )
        delta_below = service.calculate_delta(old_state, new_state_below)
        assert delta_below < 0.05

        # 6% change - above threshold
        new_state_above = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.CHANGE_EVENT,
            connection_weights={"a->b": 1.06},
        )
        delta_above = service.calculate_delta(old_state, new_state_above)
        assert delta_above > 0.05

    def test_calculate_delta_dimension_mismatch(self):
        """Test delta returns 1.0 on dimension mismatch."""
        service = NetworkStateService()

        old_state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.MANUAL,
            connection_weights={"a->b": 0.5},
        )
        new_state = NetworkState(
            agent_id="test",
            trigger=SnapshotTrigger.CHANGE_EVENT,
            connection_weights={"a->b": 0.5, "c->d": 0.6},  # Extra key
        )

        delta = service.calculate_delta(old_state, new_state)
        assert delta == 1.0  # Force snapshot on structure change


# ---------------------------------------------------------------------------
# Math Utils Tests (T005)
# ---------------------------------------------------------------------------


class TestMathUtils:
    """Tests for math utility functions (T005)."""

    def test_weight_bounds_enforcer_in_range(self):
        """Test weight_bounds_enforcer returns value unchanged if in bounds."""
        assert weight_bounds_enforcer(0.5) == 0.5
        assert weight_bounds_enforcer(0.01) == 0.01
        assert weight_bounds_enforcer(0.99) == 0.99

    def test_weight_bounds_enforcer_below_min(self):
        """Test weight_bounds_enforcer handles values below minimum."""
        result = weight_bounds_enforcer(-0.5)
        assert 0.01 <= result <= 0.99

    def test_weight_bounds_enforcer_above_max(self):
        """Test weight_bounds_enforcer handles values above maximum."""
        result = weight_bounds_enforcer(1.5)
        assert 0.01 <= result <= 0.99

    def test_sigmoid_squash_bounds(self):
        """Test sigmoid_squash keeps values in bounds."""
        assert 0.01 <= sigmoid_squash(-100) <= 0.99
        assert 0.01 <= sigmoid_squash(100) <= 0.99
        assert 0.01 <= sigmoid_squash(0) <= 0.99

    def test_hebbian_update_formula(self):
        """Test Hebbian update formula: hebbμ(V1,V2,W) = V1·V2·(1-W) + μ·W."""
        # Full activation
        result = hebbian_update(v1=1.0, v2=1.0, w=0.5, mu=0.9)
        expected = 1.0 * 1.0 * (1 - 0.5) + 0.9 * 0.5
        assert result == pytest.approx(expected)

        # No activation
        result = hebbian_update(v1=0.0, v2=0.0, w=0.5, mu=0.9)
        expected = 0.0 * 0.0 * (1 - 0.5) + 0.9 * 0.5
        assert result == pytest.approx(expected)

    def test_weight_decay_formula(self):
        """Test exponential decay formula."""
        result = weight_decay(weight=0.5, decay_rate=0.01, time_since_activation=0)
        assert result == pytest.approx(0.5)  # No decay at t=0

        result = weight_decay(weight=0.5, decay_rate=0.01, time_since_activation=100)
        assert result < 0.5  # Should have decayed
        assert result >= 0.01  # Minimum bound

    def test_treur_state_update_formula(self):
        """Test Treur temporal-causal update: Y += η(c-Y)Δt."""
        result = treur_state_update(current=0.5, target=1.0, speed=0.1, dt=1.0)
        expected = 0.5 + 0.1 * (1.0 - 0.5) * 1.0
        assert result == pytest.approx(expected)


# ---------------------------------------------------------------------------
# SelfModelState and TimingState Tests (T063-T065)
# ---------------------------------------------------------------------------


class TestSelfModelState:
    """Tests for SelfModelState model (T063)."""

    def test_create_self_model_state(self):
        """Test SelfModelState creation."""
        state = SelfModelState(
            agent_id="test-agent",
            network_state_id="net-state-123",
            w_states={"a->b": 0.5},
            t_states={"a": 0.3},
            observation_confidence=0.8,
        )

        assert state.agent_id == "test-agent"
        assert state.w_states["a->b"] == 0.5
        assert state.observation_confidence == 0.8

    def test_observation_confidence_bounds(self):
        """Test observation_confidence must be in [0, 1]."""
        # Valid values
        SelfModelState(
            agent_id="test",
            network_state_id="123",
            observation_confidence=0.0,
        )
        SelfModelState(
            agent_id="test",
            network_state_id="123",
            observation_confidence=1.0,
        )


class TestTimingState:
    """Tests for TimingState model (T064)."""

    def test_create_timing_state(self):
        """Test TimingState creation."""
        state = TimingState(
            agent_id="test-agent",
            self_model_state_id="self-model-123",
            h_states={"hidden": 0.1},
            adaptation_mode=AdaptationMode.STABLE,
            stress_level=0.2,
        )

        assert state.agent_id == "test-agent"
        assert state.h_states["hidden"] == 0.1
        assert state.adaptation_mode == AdaptationMode.STABLE
        assert state.stress_level == 0.2

    def test_adaptation_mode_transitions(self):
        """Test AdaptationMode enum values for mode transitions (T065)."""
        # Verify all modes exist
        modes = [
            AdaptationMode.ACCELERATING,
            AdaptationMode.STABLE,
            AdaptationMode.DECELERATING,
            AdaptationMode.STRESSED,
        ]
        assert len(modes) == 4

        # Test mode assignment
        state = TimingState(
            agent_id="test",
            self_model_state_id="123",
            adaptation_mode=AdaptationMode.ACCELERATING,
        )
        assert state.adaptation_mode == AdaptationMode.ACCELERATING

        # Mode can be changed
        state.adaptation_mode = AdaptationMode.STRESSED
        assert state.adaptation_mode == AdaptationMode.STRESSED

    def test_stress_level_bounds(self):
        """Test stress_level must be in [0, 1]."""
        TimingState(
            agent_id="test",
            self_model_state_id="123",
            stress_level=0.0,
        )
        TimingState(
            agent_id="test",
            self_model_state_id="123",
            stress_level=1.0,
        )


# ---------------------------------------------------------------------------
# Config Tests
# ---------------------------------------------------------------------------


class TestNetworkStateConfig:
    """Tests for NetworkStateConfig."""

    def test_default_config_disabled(self):
        """Test that all features are disabled by default."""
        config = NetworkStateConfig()

        # All features should be disabled by default (SC-009, SC-010)
        assert config.network_state_enabled is False
        assert config.self_modeling_enabled is False
        assert config.hebbian_learning_enabled is False
        assert config.role_matrix_enabled is False

    def test_config_delta_threshold(self):
        """Test default delta threshold is 5%."""
        config = NetworkStateConfig()
        assert config.delta_threshold == 0.05

    def test_config_explicit_values(self):
        """Test config with explicit values."""
        config = NetworkStateConfig(
            network_state_enabled=True,
            self_modeling_enabled=True,
            delta_threshold=0.10,
        )

        assert config.network_state_enabled is True
        assert config.self_modeling_enabled is True
        assert config.delta_threshold == 0.10


# ---------------------------------------------------------------------------
# NetworkStateDiff Tests
# ---------------------------------------------------------------------------


class TestNetworkStateDiff:
    """Tests for NetworkStateDiff model."""

    def test_create_diff(self):
        """Test NetworkStateDiff creation."""
        diff = NetworkStateDiff(
            from_snapshot_id="snap-1",
            to_snapshot_id="snap-2",
            weight_changes={
                "a->b": ValueChange(old=0.5, new=0.6, delta=0.1),
            },
            total_delta=0.1,
        )

        assert diff.from_snapshot_id == "snap-1"
        assert diff.weight_changes["a->b"].delta == 0.1
        assert diff.total_delta == 0.1
