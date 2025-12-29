"""
Network State Models - Observable W/T/H values for network reification.

Part of 034-network-self-modeling feature.
All components are opt-in via configuration flags.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Configuration (T001)
# ---------------------------------------------------------------------------


class NetworkStateConfig:
    """Configuration for network state feature flags.

    All features default to disabled for zero-regression guarantee.
    """

    def __init__(
        self,
        network_state_enabled: Optional[bool] = None,
        self_modeling_enabled: Optional[bool] = None,
        hebbian_learning_enabled: Optional[bool] = None,
        role_matrix_enabled: Optional[bool] = None,
        delta_threshold: Optional[float] = None,
    ):
        self.network_state_enabled = network_state_enabled if network_state_enabled is not None else (
            os.getenv("NETWORK_STATE_ENABLED", "false").lower() == "true"
        )
        self.self_modeling_enabled = self_modeling_enabled if self_modeling_enabled is not None else (
            os.getenv("SELF_MODELING_ENABLED", "false").lower() == "true"
        )
        self.hebbian_learning_enabled = hebbian_learning_enabled if hebbian_learning_enabled is not None else (
            os.getenv("HEBBIAN_LEARNING_ENABLED", "false").lower() == "true"
        )
        self.role_matrix_enabled = role_matrix_enabled if role_matrix_enabled is not None else (
            os.getenv("ROLE_MATRIX_ENABLED", "false").lower() == "true"
        )
        self.delta_threshold = delta_threshold if delta_threshold is not None else float(
            os.getenv("NETWORK_STATE_DELTA_THRESHOLD", "0.05")
        )


# Singleton for easy access
_config: Optional[NetworkStateConfig] = None


def get_network_state_config() -> NetworkStateConfig:
    """Get or create the network state configuration singleton."""
    global _config
    if _config is None:
        _config = NetworkStateConfig()
    return _config


# ---------------------------------------------------------------------------
# Enums (T002, T003)
# ---------------------------------------------------------------------------


class SnapshotTrigger(str, Enum):
    """Trigger type for network state snapshots (T002)."""
    CHANGE_EVENT = "CHANGE_EVENT"  # >5% delta threshold exceeded
    DAILY_CHECKPOINT = "DAILY_CHECKPOINT"  # Scheduled daily snapshot
    MANUAL = "MANUAL"  # User/operator triggered


class AdaptationMode(str, Enum):
    """Adaptation behavior mode for multi-level learning (T003)."""
    ACCELERATING = "ACCELERATING"  # Learning speed increasing
    STABLE = "STABLE"  # Learning speed steady
    DECELERATING = "DECELERATING"  # Learning speed decreasing
    STRESSED = "STRESSED"  # Reduced adaptation due to stress


class PredictionStatus(str, Enum):
    """Status of a self-prediction record."""
    PENDING = "PENDING"  # Prediction made, awaiting actual state
    RESOLVED = "RESOLVED"  # Actual state observed, error calculated
    EXPIRED = "EXPIRED"  # Prediction timeout exceeded (1 hour)


# ---------------------------------------------------------------------------
# Network State Model (T013)
# ---------------------------------------------------------------------------


class NetworkState(BaseModel):
    """Complete snapshot of an agent's reified network state.

    Contains W (connection weights), T (thresholds), and H (speed factors)
    values that make the network's internal state observable.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = Field(..., description="Agent this state belongs to")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trigger: SnapshotTrigger = Field(..., description="Why snapshot was created")

    # W, T, H values - the core reified state
    connection_weights: dict[str, float] = Field(
        default_factory=dict,
        description="W values keyed by 'source_id->target_id'"
    )
    thresholds: dict[str, float] = Field(
        default_factory=dict,
        description="T values keyed by node_id"
    )
    speed_factors: dict[str, float] = Field(
        default_factory=dict,
        description="H values keyed by node_id"
    )

    # Delta tracking
    delta_from_previous: Optional[float] = Field(
        None,
        ge=0,
        description="L2 norm change from last snapshot"
    )
    checksum: Optional[str] = Field(
        None,
        description="SHA256 of serialized state for integrity"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_id": "perception-agent-001",
                "trigger": "CHANGE_EVENT",
                "connection_weights": {"input->hidden": 0.75, "hidden->output": 0.6},
                "thresholds": {"hidden": 0.5, "output": 0.3},
                "speed_factors": {"hidden": 0.1, "output": 0.05},
                "delta_from_previous": 0.08
            }
        }
    }

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum of the state for integrity verification."""
        data = (
            f"{self.agent_id}|{self.timestamp.isoformat()}|"
            f"{sorted(self.connection_weights.items())}|"
            f"{sorted(self.thresholds.items())}|"
            f"{sorted(self.speed_factors.items())}"
        )
        return hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Network State Diff Model
# ---------------------------------------------------------------------------


class ValueChange(BaseModel):
    """A single value change between snapshots."""
    old: float
    new: float
    delta: float


class NetworkStateDiff(BaseModel):
    """Difference between two network state snapshots."""

    from_snapshot_id: str
    to_snapshot_id: str
    weight_changes: dict[str, ValueChange] = Field(default_factory=dict)
    threshold_changes: dict[str, ValueChange] = Field(default_factory=dict)
    speed_factor_changes: dict[str, ValueChange] = Field(default_factory=dict)
    total_delta: float = Field(0.0, description="Overall L2 norm delta")


# ---------------------------------------------------------------------------
# Self-Model State (T066 - Phase 7)
# ---------------------------------------------------------------------------


class SelfModelState(BaseModel):
    """First-order self-model representing observable network characteristics.

    The agent's internal representation of its own W and T states,
    with confidence level for self-observation accuracy.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    network_state_id: str = Field(..., description="Associated NetworkState snapshot")

    # Self-model of W and T values
    w_states: dict[str, float] = Field(
        default_factory=dict,
        description="Self-model of connection weights"
    )
    t_states: dict[str, float] = Field(
        default_factory=dict,
        description="Self-model of thresholds"
    )

    observation_confidence: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in self-observation accuracy"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Timing State (T067 - Phase 7)
# ---------------------------------------------------------------------------


class TimingState(BaseModel):
    """Second-order self-model controlling adaptation speed.

    The H states that control how fast W and T states adapt,
    implementing the stress-reduces-adaptation principle.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    self_model_state_id: str = Field(..., description="Associated first-order state")

    # Speed factors for each W/T state
    h_states: dict[str, float] = Field(
        default_factory=dict,
        description="Speed factors for each W/T state"
    )

    adaptation_mode: AdaptationMode = Field(
        AdaptationMode.STABLE,
        description="Current adaptation behavior"
    )
    stress_level: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Current stress indicator (affects adaptation)"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)
