"""
Contract tests for Network State API.

Part of 034-network-self-modeling feature.
Tests T010-T012: API contract validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
import os

# Set feature flag before importing app
os.environ["NETWORK_STATE_ENABLED"] = "true"

from api.main import app
from api.models.network_state import (
    NetworkState,
    NetworkStateDiff,
    SnapshotTrigger,
    NetworkStateConfig,
)
from api.services.network_state_service import NetworkStateService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    """Create a mock NetworkStateService."""
    service = MagicMock(spec=NetworkStateService)
    service.config = NetworkStateConfig(network_state_enabled=True)
    return service


@pytest.fixture
def sample_network_state():
    """Create a sample NetworkState for testing."""
    return NetworkState(
        id="550e8400-e29b-41d4-a716-446655440000",
        agent_id="perception-agent-001",
        trigger=SnapshotTrigger.CHANGE_EVENT,
        connection_weights={"input->hidden": 0.75, "hidden->output": 0.6},
        thresholds={"hidden": 0.5, "output": 0.3},
        speed_factors={"hidden": 0.1, "output": 0.05},
        delta_from_previous=0.08,
    )


# ---------------------------------------------------------------------------
# T010: Contract test for GET /network-state/{agent_id}
# ---------------------------------------------------------------------------


class TestGetCurrentNetworkState:
    """Contract tests for GET /network-state/{agent_id} (T010)."""

    @pytest.mark.asyncio
    async def test_get_current_returns_200(self, mock_service, sample_network_state):
        """Test GET returns 200 with valid network state."""
        mock_service.get_current = AsyncMock(return_value=sample_network_state)

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/network-state/perception-agent-001")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "perception-agent-001"
        assert data["trigger"] == "CHANGE_EVENT"
        assert "connection_weights" in data
        assert "thresholds" in data
        assert "speed_factors" in data

    @pytest.mark.asyncio
    async def test_get_current_returns_404_for_unknown_agent(self, mock_service):
        """Test GET returns 404 when agent has no network state."""
        mock_service.get_current = AsyncMock(return_value=None)

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/network-state/unknown-agent")

        assert response.status_code == 404
        assert "No network state found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_response_matches_schema(self, mock_service, sample_network_state):
        """Test response matches OpenAPI schema."""
        mock_service.get_current = AsyncMock(return_value=sample_network_state)

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/network-state/perception-agent-001")

        data = response.json()

        # Required fields per OpenAPI spec
        assert "id" in data
        assert "agent_id" in data
        assert "timestamp" in data
        assert "trigger" in data
        assert "connection_weights" in data
        assert "thresholds" in data
        assert "speed_factors" in data

        # Trigger must be valid enum value
        assert data["trigger"] in ["CHANGE_EVENT", "DAILY_CHECKPOINT", "MANUAL"]


# ---------------------------------------------------------------------------
# T011: Contract test for GET /network-state/{agent_id}/history
# ---------------------------------------------------------------------------


class TestGetNetworkStateHistory:
    """Contract tests for GET /network-state/{agent_id}/history (T011)."""

    @pytest.mark.asyncio
    async def test_get_history_returns_200(self, mock_service, sample_network_state):
        """Test GET history returns 200 with snapshots array."""
        mock_service.get_history = AsyncMock(return_value=[sample_network_state])

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/network-state/perception-agent-001/history")

        assert response.status_code == 200
        data = response.json()
        assert "snapshots" in data
        assert "total_count" in data
        assert isinstance(data["snapshots"], list)
        assert data["total_count"] == 1

    @pytest.mark.asyncio
    async def test_get_history_with_time_range(self, mock_service, sample_network_state):
        """Test GET history with time range parameters."""
        mock_service.get_history = AsyncMock(return_value=[sample_network_state])

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            start = (datetime.utcnow() - timedelta(hours=48)).isoformat()
            end = datetime.utcnow().isoformat()

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/perception-agent-001/history",
                    params={"start_time": start, "end_time": end, "limit": 50}
                )

        assert response.status_code == 200
        mock_service.get_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_limit_validation(self, mock_service):
        """Test GET history enforces limit constraints."""
        mock_service.get_history = AsyncMock(return_value=[])

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            # Test limit > 1000 should be rejected
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/agent-001/history",
                    params={"limit": 2000}
                )

        # FastAPI validates Query params - should return 422
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# T012: Contract test for POST /network-state/{agent_id}/snapshot
# ---------------------------------------------------------------------------


class TestCreateManualSnapshot:
    """Contract tests for POST /network-state/{agent_id}/snapshot (T012)."""

    @pytest.mark.asyncio
    async def test_create_snapshot_returns_201(self, mock_service, sample_network_state):
        """Test POST snapshot returns 201 with created state."""
        mock_service.get_history = AsyncMock(return_value=[])  # No recent snapshots
        mock_service.create_snapshot = AsyncMock(return_value=sample_network_state)

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/network-state/perception-agent-001/snapshot",
                    json={
                        "connection_weights": {"input->hidden": 0.75},
                        "thresholds": {"hidden": 0.5},
                        "speed_factors": {"hidden": 0.1},
                    }
                )

        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == "perception-agent-001"
        assert data["trigger"] == "CHANGE_EVENT"

    @pytest.mark.asyncio
    async def test_create_snapshot_rate_limited(self, mock_service, sample_network_state):
        """Test POST snapshot returns 429 when rate limited."""
        # Recent manual snapshot exists
        recent_snapshot = NetworkState(
            agent_id="agent-001",
            trigger=SnapshotTrigger.MANUAL,
            timestamp=datetime.utcnow() - timedelta(seconds=30),  # 30 seconds ago
        )
        mock_service.get_history = AsyncMock(return_value=[recent_snapshot])

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/network-state/agent-001/snapshot",
                    json={"connection_weights": {}}
                )

        assert response.status_code == 429
        assert "Rate limited" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_snapshot_empty_request(self, mock_service, sample_network_state):
        """Test POST snapshot works with empty state values."""
        mock_service.get_history = AsyncMock(return_value=[])
        sample_network_state.connection_weights = {}
        sample_network_state.thresholds = {}
        sample_network_state.speed_factors = {}
        mock_service.create_snapshot = AsyncMock(return_value=sample_network_state)

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/network-state/agent-001/snapshot",
                    json={}  # Empty body should use defaults
                )

        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Contract test for GET /network-state/{agent_id}/diff
# ---------------------------------------------------------------------------


class TestGetNetworkStateDiff:
    """Contract tests for GET /network-state/{agent_id}/diff."""

    @pytest.mark.asyncio
    async def test_get_diff_returns_200(self, mock_service):
        """Test GET diff returns 200 with diff data."""
        diff = NetworkStateDiff(
            from_snapshot_id="snap-1",
            to_snapshot_id="snap-2",
            weight_changes={},
            threshold_changes={},
            speed_factor_changes={},
            total_delta=0.05,
        )
        mock_service.get_diff = AsyncMock(return_value=diff)

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/agent-001/diff",
                    params={
                        "from_snapshot_id": "snap-1",
                        "to_snapshot_id": "snap-2",
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data["from_snapshot_id"] == "snap-1"
        assert data["to_snapshot_id"] == "snap-2"
        assert "total_delta" in data

    @pytest.mark.asyncio
    async def test_get_diff_returns_404_not_found(self, mock_service):
        """Test GET diff returns 404 when snapshots not found."""
        mock_service.get_diff = AsyncMock(return_value=None)

        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/agent-001/diff",
                    params={
                        "from_snapshot_id": "invalid-1",
                        "to_snapshot_id": "invalid-2",
                    }
                )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_diff_requires_params(self, mock_service):
        """Test GET diff requires from_snapshot_id and to_snapshot_id."""
        with patch(
            "api.routers.network_state.get_network_state_service",
            return_value=mock_service
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/network-state/agent-001/diff")

        assert response.status_code == 422  # Missing required params


# ---------------------------------------------------------------------------
# Feature Flag Tests (SC-009, SC-010)
# ---------------------------------------------------------------------------


class TestFeatureFlags:
    """Tests for feature flag behavior (SC-009, SC-010)."""

    @pytest.mark.asyncio
    async def test_disabled_feature_returns_503(self):
        """Test that disabled feature returns 503."""
        disabled_config = NetworkStateConfig(network_state_enabled=False)
        mock_service = MagicMock(spec=NetworkStateService)
        mock_service.config = disabled_config

        # Patch get_network_state_config to return disabled config
        with patch(
            "api.routers.network_state.get_network_state_config",
            return_value=disabled_config
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/network-state/agent-001")

        assert response.status_code == 503
        assert "not enabled" in response.json()["detail"]


# ---------------------------------------------------------------------------
# T026: Contract test for GET /self-modeling/{agent_id}/predictions
# ---------------------------------------------------------------------------


class TestGetPredictions:
    """Contract tests for GET /self-modeling/{agent_id}/predictions (T026)."""

    @pytest.mark.asyncio
    async def test_get_predictions_returns_200(self):
        """Test GET predictions returns 200 with predictions array."""
        from api.models.prediction import PredictionRecord
        from api.services.self_modeling_service import SelfModelingService

        mock_prediction = PredictionRecord(
            agent_id="agent-001",
            predicted_state={"w_a->b": 0.5},
            actual_state={"w_a->b": 0.55},
            prediction_error=0.10
        )

        mock_service = MagicMock(spec=SelfModelingService)
        mock_service.get_predictions = AsyncMock(return_value=[mock_prediction])

        enabled_config = NetworkStateConfig(
            network_state_enabled=True,
            self_modeling_enabled=True
        )

        with patch(
            "api.routers.network_state.get_self_modeling_service",
            return_value=mock_service
        ), patch(
            "api.routers.network_state.get_network_state_config",
            return_value=enabled_config
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/self-modeling/agent-001/predictions"
                )

        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total_count" in data
        assert data["total_count"] == 1

    @pytest.mark.asyncio
    async def test_get_predictions_disabled_returns_503(self):
        """Test GET predictions returns 503 when feature disabled."""
        disabled_config = NetworkStateConfig(
            network_state_enabled=True,
            self_modeling_enabled=False
        )

        with patch(
            "api.routers.network_state.get_network_state_config",
            return_value=disabled_config
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/self-modeling/agent-001/predictions"
                )

        assert response.status_code == 503
        assert "not enabled" in response.json()["detail"]


# ---------------------------------------------------------------------------
# T027: Contract test for GET /self-modeling/{agent_id}/accuracy
# ---------------------------------------------------------------------------


class TestGetAccuracyMetrics:
    """Contract tests for GET /self-modeling/{agent_id}/accuracy (T027)."""

    @pytest.mark.asyncio
    async def test_get_accuracy_returns_200(self):
        """Test GET accuracy returns 200 with metrics."""
        from api.models.prediction import PredictionAccuracy
        from api.services.self_modeling_service import SelfModelingService

        mock_metrics = PredictionAccuracy(
            agent_id="agent-001",
            average_error=0.08,
            sample_count=42,
            window_start=datetime.utcnow() - timedelta(hours=24),
            window_end=datetime.utcnow()
        )

        mock_service = MagicMock(spec=SelfModelingService)
        mock_service.get_accuracy_metrics = AsyncMock(return_value=mock_metrics)

        enabled_config = NetworkStateConfig(
            network_state_enabled=True,
            self_modeling_enabled=True
        )

        with patch(
            "api.routers.network_state.get_self_modeling_service",
            return_value=mock_service
        ), patch(
            "api.routers.network_state.get_network_state_config",
            return_value=enabled_config
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/self-modeling/agent-001/accuracy"
                )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "agent-001"
        assert data["average_error"] == 0.08
        assert data["sample_count"] == 42
        assert "window_start" in data
        assert "window_end" in data

    @pytest.mark.asyncio
    async def test_get_accuracy_with_window_param(self):
        """Test GET accuracy accepts window_hours parameter."""
        from api.models.prediction import PredictionAccuracy
        from api.services.self_modeling_service import SelfModelingService

        mock_metrics = PredictionAccuracy(
            agent_id="agent-001",
            average_error=0.05,
            sample_count=10,
            window_start=datetime.utcnow() - timedelta(hours=48),
            window_end=datetime.utcnow()
        )

        mock_service = MagicMock(spec=SelfModelingService)
        mock_service.get_accuracy_metrics = AsyncMock(return_value=mock_metrics)

        enabled_config = NetworkStateConfig(
            network_state_enabled=True,
            self_modeling_enabled=True
        )

        with patch(
            "api.routers.network_state.get_self_modeling_service",
            return_value=mock_service
        ), patch(
            "api.routers.network_state.get_network_state_config",
            return_value=enabled_config
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/network-state/self-modeling/agent-001/accuracy",
                    params={"window_hours": 48}
                )

        assert response.status_code == 200
        mock_service.get_accuracy_metrics.assert_called_once()
        # Verify window_hours was passed
        call_kwargs = mock_service.get_accuracy_metrics.call_args.kwargs
        assert call_kwargs.get("window_hours") == 48
