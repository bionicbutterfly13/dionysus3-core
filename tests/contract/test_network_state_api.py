"""
Contract tests for Network State API.

Part of 034-network-self-modeling feature.
Tests T010-T012: API contract validation.

Uses minimal FastAPI app + dependency overrides (no main app conditional router).
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.models.network_state import (
    NetworkState,
    NetworkStateDiff,
    SnapshotTrigger,
    NetworkStateConfig,
)
from api.services.network_state_service import NetworkStateService


# ---------------------------------------------------------------------------
# Minimal app (router always mounted; no main-app config)
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    import api.routers.network_state as ns

    test_app = FastAPI()
    test_app.include_router(ns.router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


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


def _override_deps(client: TestClient, *, get_service=None, check_feature_enabled=None):
    import api.routers.network_state as ns

    overrides = {}
    if get_service is not None:
        overrides[ns.get_service] = lambda: get_service
    if check_feature_enabled is not None:
        overrides[ns.check_feature_enabled] = check_feature_enabled
    for k, v in overrides.items():
        client.app.dependency_overrides[k] = v


def _clear_overrides(client: TestClient):
    client.app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# T010: Contract test for GET /network-state/{agent_id}
# ---------------------------------------------------------------------------


class TestGetCurrentNetworkState:
    """Contract tests for GET /network-state/{agent_id} (T010)."""

    def test_get_current_returns_200(self, client, mock_service, sample_network_state):
        """Test GET returns 200 with valid network state."""
        mock_service.get_current = AsyncMock(return_value=sample_network_state)
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get("/api/v1/network-state/perception-agent-001")
        finally:
            _clear_overrides(client)
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "perception-agent-001"
        assert data["trigger"] == "CHANGE_EVENT"
        assert "connection_weights" in data
        assert "thresholds" in data
        assert "speed_factors" in data

    def test_get_current_returns_404_for_unknown_agent(self, client, mock_service):
        """Test GET returns 404 when agent has no network state."""
        mock_service.get_current = AsyncMock(return_value=None)
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get("/api/v1/network-state/unknown-agent")
        finally:
            _clear_overrides(client)
        assert response.status_code == 404
        assert "No network state found" in response.json()["detail"]

    def test_response_matches_schema(self, client, mock_service, sample_network_state):
        """Test response matches OpenAPI schema."""
        mock_service.get_current = AsyncMock(return_value=sample_network_state)
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get("/api/v1/network-state/perception-agent-001")
        finally:
            _clear_overrides(client)
        data = response.json()
        assert "id" in data
        assert "agent_id" in data
        assert "timestamp" in data
        assert "trigger" in data
        assert "connection_weights" in data
        assert "thresholds" in data
        assert "speed_factors" in data


# ---------------------------------------------------------------------------
# Contract test for GET /network-state/{agent_id}/history
# ---------------------------------------------------------------------------


class TestGetNetworkStateHistory:
    """Contract tests for GET /network-state/{agent_id}/history."""

    def test_get_history_returns_200(self, client, mock_service, sample_network_state):
        """Test GET history returns 200 with snapshots array."""
        mock_service.get_history = AsyncMock(return_value=[sample_network_state])
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get("/api/v1/network-state/agent-001/history")
        finally:
            _clear_overrides(client)
        assert response.status_code == 200
        data = response.json()
        assert "snapshots" in data
        assert "total_count" in data
        assert data["total_count"] == 1
        assert len(data["snapshots"]) == 1

    def test_get_history_with_time_range(self, client, mock_service):
        """Test GET history accepts start_time and end_time params."""
        mock_service.get_history = AsyncMock(return_value=[])
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get(
                "/api/v1/network-state/agent-001/history",
                params={
                    "start_time": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                },
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 200
        mock_service.get_history.assert_called_once()

    def test_get_history_limit_validation(self, client, mock_service):
        """Test GET history validates limit param (1–1000)."""
        mock_service.get_history = AsyncMock(return_value=[])
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get(
                "/api/v1/network-state/agent-001/history",
                params={"limit": 0},
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Contract test for POST /network-state/{agent_id}/snapshot
# ---------------------------------------------------------------------------


class TestCreateManualSnapshot:
    """Contract tests for POST /network-state/{agent_id}/snapshot."""

    def test_create_snapshot_returns_201(self, client, mock_service, sample_network_state):
        """Test POST snapshot returns 201 with created state."""
        mock_service.get_history = AsyncMock(return_value=[])
        mock_service.create_snapshot = AsyncMock(return_value=sample_network_state)
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.post(
                "/api/v1/network-state/agent-001/snapshot",
                json={"connection_weights": {}},
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == "perception-agent-001"

    def test_create_snapshot_rate_limited(self, client, mock_service):
        """Test POST snapshot returns 429 when rate limited."""
        recent_snapshot = NetworkState(
            agent_id="agent-001",
            trigger=SnapshotTrigger.MANUAL,
            timestamp=datetime.utcnow() - timedelta(seconds=30),
        )
        mock_service.get_history = AsyncMock(return_value=[recent_snapshot])
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.post(
                "/api/v1/network-state/agent-001/snapshot",
                json={"connection_weights": {}},
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 429
        assert "Rate limited" in response.json()["detail"]

    def test_create_snapshot_empty_request(self, client, mock_service, sample_network_state):
        """Test POST snapshot works with empty state values."""
        sample_network_state.connection_weights = {}
        sample_network_state.thresholds = {}
        sample_network_state.speed_factors = {}
        mock_service.get_history = AsyncMock(return_value=[])
        mock_service.create_snapshot = AsyncMock(return_value=sample_network_state)
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.post(
                "/api/v1/network-state/agent-001/snapshot",
                json={},
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Contract test for GET /network-state/{agent_id}/diff
# ---------------------------------------------------------------------------


class TestGetNetworkStateDiff:
    """Contract tests for GET /network-state/{agent_id}/diff."""

    def test_get_diff_returns_200(self, client, mock_service):
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
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get(
                "/api/v1/network-state/agent-001/diff",
                params={"from_snapshot_id": "snap-1", "to_snapshot_id": "snap-2"},
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 200
        data = response.json()
        assert data["from_snapshot_id"] == "snap-1"
        assert data["to_snapshot_id"] == "snap-2"
        assert "total_delta" in data

    def test_get_diff_returns_404_not_found(self, client, mock_service):
        """Test GET diff returns 404 when snapshots not found."""
        mock_service.get_diff = AsyncMock(return_value=None)
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get(
                "/api/v1/network-state/agent-001/diff",
                params={"from_snapshot_id": "invalid-1", "to_snapshot_id": "invalid-2"},
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 404

    def test_get_diff_requires_params(self, client, mock_service):
        """Test GET diff requires from_snapshot_id and to_snapshot_id."""
        _override_deps(client, get_service=mock_service, check_feature_enabled=lambda: None)
        try:
            response = client.get("/api/v1/network-state/agent-001/diff")
        finally:
            _clear_overrides(client)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Feature Flag Tests (SC-009, SC-010)
# ---------------------------------------------------------------------------


class TestFeatureFlags:
    """Tests for feature flag behavior (SC-009, SC-010)."""

    def test_disabled_feature_returns_503(self, client):
        """Test that disabled feature returns 503."""
        from fastapi import HTTPException

        def raise_503():
            raise HTTPException(
                status_code=503,
                detail="Network state feature is not enabled. Set NETWORK_STATE_ENABLED=true",
            )

        import api.routers.network_state as ns

        client.app.dependency_overrides[ns.check_feature_enabled] = raise_503
        try:
            response = client.get("/api/v1/network-state/agent-001")
        finally:
            _clear_overrides(client)
        assert response.status_code == 503
        assert "not enabled" in response.json()["detail"]


# ---------------------------------------------------------------------------
# T026: Contract test for GET /self-modeling/{agent_id}/predictions
# ---------------------------------------------------------------------------


class TestGetPredictions:
    """Contract tests for GET /self-modeling/{agent_id}/predictions (T026)."""

    def test_get_predictions_returns_200(self, client):
        """Test GET predictions returns 200 with predictions array."""
        from api.models.prediction import PredictionRecord
        from api.services.self_modeling_service import SelfModelingService

        import api.routers.network_state as ns

        mock_prediction = PredictionRecord(
            agent_id="agent-001",
            predicted_state={"w_a->b": 0.5},
            actual_state={"w_a->b": 0.55},
            prediction_error=0.10,
        )
        mock_svc = MagicMock(spec=SelfModelingService)
        mock_svc.get_predictions = AsyncMock(return_value=[mock_prediction])

        client.app.dependency_overrides[ns.get_self_modeling] = lambda: mock_svc
        client.app.dependency_overrides[ns.check_self_modeling_enabled] = lambda: None
        try:
            response = client.get(
                "/api/v1/network-state/self-modeling/agent-001/predictions",
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total_count" in data
        assert data["total_count"] == 1

    def test_get_predictions_disabled_returns_503(self, client):
        """Test GET predictions returns 503 when feature disabled."""
        from fastapi import HTTPException

        def raise_503():
            raise HTTPException(
                status_code=503,
                detail="Self-modeling feature is not enabled. Set SELF_MODELING_ENABLED=true",
            )

        import api.routers.network_state as ns

        client.app.dependency_overrides[ns.check_self_modeling_enabled] = raise_503
        try:
            response = client.get(
                "/api/v1/network-state/self-modeling/agent-001/predictions",
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 503
        assert "not enabled" in response.json()["detail"]


# ---------------------------------------------------------------------------
# T027: Contract test for GET /self-modeling/{agent_id}/accuracy
# ---------------------------------------------------------------------------


class TestGetAccuracyMetrics:
    """Contract tests for GET /self-modeling/{agent_id}/accuracy (T027)."""

    def test_get_accuracy_returns_200(self, client):
        """Test GET accuracy returns 200 with metrics."""
        from api.models.prediction import PredictionAccuracy
        from api.services.self_modeling_service import SelfModelingService

        import api.routers.network_state as ns

        mock_metrics = PredictionAccuracy(
            agent_id="agent-001",
            average_error=0.08,
            sample_count=42,
            window_start=datetime.utcnow() - timedelta(hours=24),
            window_end=datetime.utcnow(),
        )
        mock_svc = MagicMock(spec=SelfModelingService)
        mock_svc.get_accuracy_metrics = AsyncMock(return_value=mock_metrics)

        client.app.dependency_overrides[ns.get_self_modeling] = lambda: mock_svc
        client.app.dependency_overrides[ns.check_self_modeling_enabled] = lambda: None
        try:
            response = client.get(
                "/api/v1/network-state/self-modeling/agent-001/accuracy",
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "agent-001"
        assert data["average_error"] == 0.08
        assert data["sample_count"] == 42
        assert "window_start" in data
        assert "window_end" in data

    def test_get_accuracy_with_window_param(self, client):
        """Test GET accuracy accepts window_hours parameter."""
        from api.models.prediction import PredictionAccuracy
        from api.services.self_modeling_service import SelfModelingService

        import api.routers.network_state as ns

        mock_metrics = PredictionAccuracy(
            agent_id="agent-001",
            average_error=0.05,
            sample_count=10,
            window_start=datetime.utcnow() - timedelta(hours=48),
            window_end=datetime.utcnow(),
        )
        mock_svc = MagicMock(spec=SelfModelingService)
        mock_svc.get_accuracy_metrics = AsyncMock(return_value=mock_metrics)

        client.app.dependency_overrides[ns.get_self_modeling] = lambda: mock_svc
        client.app.dependency_overrides[ns.check_self_modeling_enabled] = lambda: None
        try:
            response = client.get(
                "/api/v1/network-state/self-modeling/agent-001/accuracy",
                params={"window_hours": 48},
            )
        finally:
            _clear_overrides(client)
        assert response.status_code == 200
        mock_svc.get_accuracy_metrics.assert_called_once()
        call_kwargs = mock_svc.get_accuracy_metrics.call_args.kwargs
        assert call_kwargs.get("window_hours") == 48
