"""
Unit tests for Hebbian Learning models and service.

Part of 034-network-self-modeling feature.
Tests T038-T041: HebbianConnection model and learning formulas.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from api.models.hebbian import HebbianConnection
from api.services.hebbian_service import HebbianService
from api.utils.math_utils import hebbian_update, weight_decay, weight_bounds_enforcer


# ---------------------------------------------------------------------------
# T038: HebbianConnection Model Tests
# ---------------------------------------------------------------------------


class TestHebbianConnectionModel:
    """Tests for HebbianConnection Pydantic model (T038)."""

    def test_create_connection_basic(self):
        """Test basic HebbianConnection creation."""
        conn = HebbianConnection(
            source_id="node-a",
            target_id="node-b",
            weight=0.5
        )

        assert conn.source_id == "node-a"
        assert conn.target_id == "node-b"
        assert conn.weight == 0.5
        assert conn.last_activated is not None

    def test_create_connection_default_weight(self):
        """Test default weight is 0.5."""
        conn = HebbianConnection(
            source_id="a",
            target_id="b"
        )
        assert conn.weight == 0.5

    def test_weight_bounds_validation(self):
        """Test weight must be in [0.01, 0.99] range."""
        # Valid bounds
        HebbianConnection(source_id="a", target_id="b", weight=0.01)
        HebbianConnection(source_id="a", target_id="b", weight=0.99)

        # Invalid: below minimum
        with pytest.raises(ValueError):
            HebbianConnection(source_id="a", target_id="b", weight=0.0)

        # Invalid: above maximum
        with pytest.raises(ValueError):
            HebbianConnection(source_id="a", target_id="b", weight=1.0)

    def test_connection_serialization(self):
        """Test HebbianConnection JSON serialization."""
        conn = HebbianConnection(
            source_id="a",
            target_id="b",
            weight=0.7
        )

        data = conn.model_dump()
        assert data["source_id"] == "a"
        assert data["target_id"] == "b"
        assert data["weight"] == 0.7

        # Deserialize
        restored = HebbianConnection.model_validate(data)
        assert restored.source_id == conn.source_id
        assert restored.weight == conn.weight


# ---------------------------------------------------------------------------
# T039: Hebbian Weight Update Formula Tests
# ---------------------------------------------------------------------------


class TestHebbianUpdateFormula:
    """Tests for Hebbian weight update formula (T039).

    Formula: hebbμ(V1, V2, W) = V1·V2·(1-W) + μ·W
    """

    def test_hebbian_update_full_coactivation(self):
        """Test Hebbian update with full co-activation (V1=V2=1)."""
        # With full activation, weight should increase
        result = hebbian_update(v1=1.0, v2=1.0, w=0.5, mu=0.9)
        # Expected: 1*1*(1-0.5) + 0.9*0.5 = 0.5 + 0.45 = 0.95
        assert result == pytest.approx(0.95)

    def test_hebbian_update_no_coactivation(self):
        """Test Hebbian update with no co-activation (V1=V2=0)."""
        # With no activation, weight decays toward μ*W
        result = hebbian_update(v1=0.0, v2=0.0, w=0.5, mu=0.9)
        # Expected: 0*0*(1-0.5) + 0.9*0.5 = 0 + 0.45 = 0.45
        assert result == pytest.approx(0.45)

    def test_hebbian_update_partial_coactivation(self):
        """Test Hebbian update with partial co-activation."""
        result = hebbian_update(v1=0.5, v2=0.5, w=0.5, mu=0.9)
        # Expected: 0.5*0.5*(1-0.5) + 0.9*0.5 = 0.125 + 0.45 = 0.575
        assert result == pytest.approx(0.575)

    def test_hebbian_update_low_persistence(self):
        """Test Hebbian update with low persistence (μ=0.1)."""
        result = hebbian_update(v1=0.0, v2=0.0, w=0.5, mu=0.1)
        # Expected: 0 + 0.1*0.5 = 0.05
        assert result == pytest.approx(0.05)

    def test_hebbian_update_preserves_learning(self):
        """Test that repeated co-activation increases weight."""
        weight = 0.5
        for _ in range(5):
            weight = hebbian_update(v1=1.0, v2=1.0, w=weight, mu=0.9)

        # After 5 full co-activations, weight should be high
        assert weight > 0.9

    def test_connection_apply_hebbian_update(self):
        """Test HebbianConnection.apply_hebbian_update method."""
        conn = HebbianConnection(source_id="a", target_id="b", weight=0.5)
        original_time = conn.last_activated

        conn.apply_hebbian_update(v1=1.0, v2=1.0, mu=0.9)

        assert conn.weight == pytest.approx(0.95)
        assert conn.last_activated >= original_time


# ---------------------------------------------------------------------------
# T040: Exponential Decay Calculation Tests
# ---------------------------------------------------------------------------


class TestExponentialDecay:
    """Tests for exponential decay calculation (T040).

    Formula: W_new = W_old * e^(-decay_rate * time)
    """

    def test_weight_decay_no_time(self):
        """Test no decay at t=0."""
        result = weight_decay(weight=0.5, decay_rate=0.01, time_since_activation=0)
        assert result == pytest.approx(0.5)

    def test_weight_decay_short_time(self):
        """Test decay over short time period."""
        result = weight_decay(weight=0.5, decay_rate=0.01, time_since_activation=1)
        # Expected: 0.5 * e^(-0.01) ≈ 0.495
        assert 0.49 < result < 0.50

    def test_weight_decay_long_time(self):
        """Test decay over long time period."""
        result = weight_decay(weight=0.5, decay_rate=0.01, time_since_activation=100)
        # After 100 days with rate 0.01, significant decay
        assert result < 0.5
        assert result >= 0.01  # Minimum bound

    def test_weight_decay_minimum_bound(self):
        """Test decay enforces minimum bound of 0.01."""
        result = weight_decay(weight=0.5, decay_rate=1.0, time_since_activation=100)
        # Extreme decay should hit minimum
        assert result >= 0.01

    def test_connection_apply_decay(self):
        """Test HebbianConnection.apply_decay method."""
        past = datetime.utcnow() - timedelta(days=10)
        conn = HebbianConnection(
            source_id="a",
            target_id="b",
            weight=0.5,
            last_activated=past
        )

        conn.apply_decay(decay_rate=0.01)

        # Weight should have decayed
        assert conn.weight < 0.5
        assert conn.weight >= 0.01


# ---------------------------------------------------------------------------
# T041: Weight Boundary Enforcement Tests
# ---------------------------------------------------------------------------


class TestWeightBoundaryEnforcement:
    """Tests for weight boundary enforcement (T041)."""

    def test_weight_bounds_enforcer_in_range(self):
        """Test values in range are unchanged."""
        assert weight_bounds_enforcer(0.5) == 0.5
        assert weight_bounds_enforcer(0.01) == 0.01
        assert weight_bounds_enforcer(0.99) == 0.99

    def test_weight_bounds_enforcer_below_min(self):
        """Test values below minimum are bounded."""
        result = weight_bounds_enforcer(-0.5)
        assert 0.01 <= result <= 0.99

        result = weight_bounds_enforcer(0.0)
        assert 0.01 <= result <= 0.99

    def test_weight_bounds_enforcer_above_max(self):
        """Test values above maximum are bounded."""
        result = weight_bounds_enforcer(1.5)
        assert 0.01 <= result <= 0.99

        result = weight_bounds_enforcer(1.0)
        assert 0.01 <= result <= 0.99

    def test_weight_bounds_enforcer_extreme_values(self):
        """Test extreme values are handled gracefully."""
        result = weight_bounds_enforcer(-100)
        assert 0.01 <= result <= 0.99

        result = weight_bounds_enforcer(100)
        assert 0.01 <= result <= 0.99


# ---------------------------------------------------------------------------
# HebbianService Tests
# ---------------------------------------------------------------------------


class TestHebbianService:
    """Tests for HebbianService methods."""

    @pytest.mark.asyncio
    async def test_record_coactivation_updates_weight(self):
        """Test record_coactivation updates connection weight."""
        mock_driver = MagicMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"weight": 0.5})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock()

        service = HebbianService(driver=mock_driver)
        await service.record_coactivation("node-a", "node-b", v1=1.0, v2=1.0)

        # Should have called session.run twice (fetch + update)
        assert mock_session.run.call_count == 2
