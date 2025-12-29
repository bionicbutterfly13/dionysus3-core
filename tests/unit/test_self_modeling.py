"""
Unit tests for Self-Modeling service.

Part of 034-network-self-modeling feature.
Tests T024-T025: PredictionRecord model and error calculation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.prediction import PredictionRecord, PredictionAccuracy
from api.models.network_state import PredictionStatus
from api.services.self_modeling_service import SelfModelingService


# ---------------------------------------------------------------------------
# T024: PredictionRecord Model Tests
# ---------------------------------------------------------------------------


class TestPredictionRecordModel:
    """Tests for PredictionRecord Pydantic model (T024)."""

    def test_create_prediction_record_basic(self):
        """Test basic PredictionRecord creation."""
        record = PredictionRecord(
            agent_id="test-agent-001",
            predicted_state={"w_input->hidden": 0.5, "t_hidden": 0.3}
        )

        assert record.agent_id == "test-agent-001"
        assert record.id is not None
        assert record.timestamp is not None
        assert record.predicted_state["w_input->hidden"] == 0.5
        assert record.actual_state is None
        assert record.prediction_error is None
        assert record.resolved_at is None

    def test_create_prediction_record_resolved(self):
        """Test PredictionRecord with resolution data."""
        record = PredictionRecord(
            agent_id="test-agent-001",
            predicted_state={"w_a->b": 0.5},
            actual_state={"w_a->b": 0.55},
            prediction_error=0.10,
            resolved_at=datetime.utcnow()
        )

        assert record.actual_state["w_a->b"] == 0.55
        assert record.prediction_error == 0.10
        assert record.resolved_at is not None

    def test_prediction_record_serialization(self):
        """Test PredictionRecord JSON serialization."""
        record = PredictionRecord(
            agent_id="test-agent",
            predicted_state={"w_x->y": 0.7}
        )

        data = record.model_dump()
        assert data["agent_id"] == "test-agent"
        assert "predicted_state" in data

        # Deserialize
        restored = PredictionRecord.model_validate(data)
        assert restored.agent_id == record.agent_id


class TestPredictionAccuracyModel:
    """Tests for PredictionAccuracy model."""

    def test_create_accuracy_metrics(self):
        """Test PredictionAccuracy creation."""
        now = datetime.utcnow()
        metrics = PredictionAccuracy(
            agent_id="test-agent",
            average_error=0.08,
            sample_count=42,
            window_start=now - timedelta(hours=24),
            window_end=now
        )

        assert metrics.agent_id == "test-agent"
        assert metrics.average_error == 0.08
        assert metrics.sample_count == 42


# ---------------------------------------------------------------------------
# T025: Prediction Error Calculation Tests
# ---------------------------------------------------------------------------


class TestPredictionErrorCalculation:
    """Tests for L2 norm prediction error calculation (T025)."""

    def test_l2_error_identical_states(self):
        """Test L2 error is 0 for identical states."""
        service = SelfModelingService(driver=MagicMock())

        predicted = {"w_a": 0.5, "w_b": 0.7}
        actual = {"w_a": 0.5, "w_b": 0.7}

        error = service._calculate_l2_error(predicted, actual)
        assert error == 0.0

    def test_l2_error_different_states(self):
        """Test L2 error calculation for different states."""
        service = SelfModelingService(driver=MagicMock())

        predicted = {"w_a": 0.5}
        actual = {"w_a": 0.6}

        error = service._calculate_l2_error(predicted, actual)
        # |0.5 - 0.6| / |0.6| = 0.1 / 0.6 ≈ 0.167
        assert 0.16 < error < 0.17

    def test_l2_error_multiple_dimensions(self):
        """Test L2 error with multiple state dimensions."""
        service = SelfModelingService(driver=MagicMock())

        predicted = {"w_a": 0.5, "w_b": 0.5}
        actual = {"w_a": 0.6, "w_b": 0.6}

        error = service._calculate_l2_error(predicted, actual)
        # Should be normalized relative error
        assert 0 < error < 1

    def test_l2_error_missing_keys(self):
        """Test L2 error handles missing keys in one dict."""
        service = SelfModelingService(driver=MagicMock())

        predicted = {"w_a": 0.5}
        actual = {"w_a": 0.5, "w_b": 0.3}  # Extra key

        error = service._calculate_l2_error(predicted, actual)
        # Missing key treated as 0.0
        assert error > 0

    def test_l2_error_zero_actual(self):
        """Test L2 error with zero actual state returns 0."""
        service = SelfModelingService(driver=MagicMock())

        predicted = {"w_a": 0.5}
        actual = {"w_a": 0.0}

        error = service._calculate_l2_error(predicted, actual)
        # Norm of actual is 0, so returns 0
        assert error == 0.0

    def test_l2_error_empty_states(self):
        """Test L2 error with empty states."""
        service = SelfModelingService(driver=MagicMock())

        error = service._calculate_l2_error({}, {})
        assert error == 0.0


# ---------------------------------------------------------------------------
# Service Method Tests
# ---------------------------------------------------------------------------


class TestSelfModelingService:
    """Tests for SelfModelingService methods."""

    @pytest.mark.asyncio
    async def test_predict_next_state_creates_record(self):
        """Test predict_next_state creates and persists prediction."""
        mock_driver = MagicMock()
        mock_session = AsyncMock()
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock()

        service = SelfModelingService(driver=mock_driver)

        current_state = {"w_a->b": 0.5, "t_a": 0.3}
        record = await service.predict_next_state("agent-001", current_state)

        assert record.agent_id == "agent-001"
        assert record.predicted_state == current_state
        mock_session.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_accuracy_metrics_empty(self):
        """Test get_accuracy_metrics with no data."""
        mock_driver = MagicMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"avg_error": None, "sample_count": 0})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock()

        service = SelfModelingService(driver=mock_driver)
        metrics = await service.get_accuracy_metrics("agent-001", window_hours=24)

        assert metrics.agent_id == "agent-001"
        assert metrics.average_error == 0.0
        assert metrics.sample_count == 0
