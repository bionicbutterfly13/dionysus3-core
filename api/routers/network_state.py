"""
Network State Router - API endpoints for network state observation.

Part of 034-network-self-modeling feature.
Implements T018-T022: Network state API endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.models.network_state import (
    NetworkState,
    NetworkStateDiff,
    SnapshotTrigger,
    get_network_state_config,
)
from api.models.prediction import PredictionRecord, PredictionAccuracy
from api.services.network_state_service import NetworkStateService, get_network_state_service
from api.services.self_modeling_service import SelfModelingService, get_self_modeling_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/network-state", tags=["Network State"])

# Rate limiter for manual snapshots
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class HistoryResponse(BaseModel):
    """Response model for network state history."""
    snapshots: list[NetworkState]
    total_count: int


class ManualSnapshotRequest(BaseModel):
    """Request model for manual snapshot creation."""
    connection_weights: dict[str, float] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(default_factory=dict)
    speed_factors: dict[str, float] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[dict] = None


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_service() -> NetworkStateService:
    """Dependency for network state service."""
    return get_network_state_service()


def check_feature_enabled() -> None:
    """Dependency to check if network state feature is enabled (T022)."""
    config = get_network_state_config()
    if not config.network_state_enabled:
        raise HTTPException(
            status_code=503,
            detail="Network state feature is not enabled. Set NETWORK_STATE_ENABLED=true"
        )


# ---------------------------------------------------------------------------
# Endpoints (T018-T022)
# ---------------------------------------------------------------------------


@router.get(
    "/{agent_id}",
    response_model=NetworkState,
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found or no network state exists"},
        503: {"model": ErrorResponse, "description": "Feature not enabled"},
    },
    summary="Get current network state",
    description="Returns the most recent network state snapshot for an agent (T018)",
)
async def get_current_network_state(
    agent_id: str,
    service: NetworkStateService = Depends(get_service),
    _: None = Depends(check_feature_enabled),
) -> NetworkState:
    """Get current network state for an agent."""
    state = await service.get_current(agent_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"No network state found for agent {agent_id}"
        )
    return state


@router.get(
    "/{agent_id}/history",
    response_model=HistoryResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Feature not enabled"},
    },
    summary="Get network state history",
    description="Returns historical network state snapshots for an agent (T019)",
)
async def get_network_state_history(
    agent_id: str,
    start_time: Optional[datetime] = Query(
        None,
        description="Start of time range (default: 24 hours ago)"
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="End of time range (default: now)"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of snapshots to return"
    ),
    service: NetworkStateService = Depends(get_service),
    _: None = Depends(check_feature_enabled),
) -> HistoryResponse:
    """Get network state history for an agent."""
    snapshots = await service.get_history(
        agent_id=agent_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return HistoryResponse(
        snapshots=snapshots,
        total_count=len(snapshots),
    )


@router.post(
    "/{agent_id}/snapshot",
    response_model=NetworkState,
    status_code=201,
    responses={
        429: {"description": "Rate limited (max 1 manual snapshot per minute)"},
        503: {"model": ErrorResponse, "description": "Feature not enabled"},
    },
    summary="Create manual snapshot",
    description="Triggers a manual network state snapshot with rate limiting (T020)",
)
async def create_manual_snapshot(
    agent_id: str,
    request: ManualSnapshotRequest,
    service: NetworkStateService = Depends(get_service),
    _: None = Depends(check_feature_enabled),
) -> NetworkState:
    """Create a manual network state snapshot.

    Rate limited to 1 per minute per agent.
    """
    # Check for recent manual snapshot (rate limiting)
    history = await service.get_history(
        agent_id=agent_id,
        start_time=datetime.utcnow() - timedelta(minutes=1),
        limit=10,
    )

    recent_manual = [s for s in history if s.trigger == SnapshotTrigger.MANUAL]
    if recent_manual:
        raise HTTPException(
            status_code=429,
            detail="Rate limited: only 1 manual snapshot per minute allowed"
        )

    state = await service.create_snapshot(
        agent_id=agent_id,
        trigger=SnapshotTrigger.MANUAL,
        connection_weights=request.connection_weights,
        thresholds=request.thresholds,
        speed_factors=request.speed_factors,
    )

    if not state:
        raise HTTPException(
            status_code=500,
            detail="Failed to create snapshot"
        )

    return state


@router.get(
    "/{agent_id}/diff",
    response_model=NetworkStateDiff,
    responses={
        404: {"model": ErrorResponse, "description": "Snapshots not found"},
        503: {"model": ErrorResponse, "description": "Feature not enabled"},
    },
    summary="Get state diff between snapshots",
    description="Returns the difference between two network state snapshots (T021)",
)
async def get_network_state_diff(
    agent_id: str,
    from_snapshot_id: str = Query(..., description="Source snapshot UUID"),
    to_snapshot_id: str = Query(..., description="Target snapshot UUID"),
    service: NetworkStateService = Depends(get_service),
    _: None = Depends(check_feature_enabled),
) -> NetworkStateDiff:
    """Get diff between two network state snapshots."""
    diff = await service.get_diff(
        agent_id=agent_id,
        from_snapshot_id=from_snapshot_id,
        to_snapshot_id=to_snapshot_id,
    )

    if not diff:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find snapshots {from_snapshot_id} and/or {to_snapshot_id}"
        )

    return diff


# ---------------------------------------------------------------------------
# Self-Modeling Endpoints (T035-T036)
# ---------------------------------------------------------------------------


class PredictionsResponse(BaseModel):
    """Response model for predictions list."""
    predictions: list[PredictionRecord]
    total_count: int


def get_self_modeling() -> SelfModelingService:
    """Dependency for self-modeling service."""
    return get_self_modeling_service()


def check_self_modeling_enabled() -> None:
    """Check if self-modeling feature is enabled."""
    config = get_network_state_config()
    if not config.self_modeling_enabled:
        raise HTTPException(
            status_code=503,
            detail="Self-modeling feature is not enabled. Set SELF_MODELING_ENABLED=true"
        )


@router.get(
    "/self-modeling/{agent_id}/predictions",
    response_model=PredictionsResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Feature not enabled"},
    },
    summary="Get agent predictions",
    description="Returns recent self-predictions for an agent (T035)",
)
async def get_predictions(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum predictions to return"),
    include_resolved: bool = Query(True, description="Include resolved predictions"),
    service: SelfModelingService = Depends(get_self_modeling),
    _: None = Depends(check_self_modeling_enabled),
) -> PredictionsResponse:
    """Get recent predictions for an agent."""
    predictions = await service.get_predictions(
        agent_id=agent_id,
        limit=limit,
        include_resolved=include_resolved,
    )
    return PredictionsResponse(
        predictions=predictions,
        total_count=len(predictions),
    )


@router.get(
    "/self-modeling/{agent_id}/accuracy",
    response_model=PredictionAccuracy,
    responses={
        503: {"model": ErrorResponse, "description": "Feature not enabled"},
    },
    summary="Get prediction accuracy metrics",
    description="Returns time-windowed accuracy metrics for an agent (T036)",
)
async def get_accuracy_metrics(
    agent_id: str,
    window_hours: int = Query(24, ge=1, le=168, description="Window size in hours (max 7 days)"),
    service: SelfModelingService = Depends(get_self_modeling),
    _: None = Depends(check_self_modeling_enabled),
) -> PredictionAccuracy:
    """Get prediction accuracy metrics for an agent."""
    return await service.get_accuracy_metrics(
        agent_id=agent_id,
        window_hours=window_hours,
    )
