"""
Action Models for Heartbeat System
Feature: 004-heartbeat-system
Tasks: T011

Dataclasses for action requests, results, and execution tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


# =============================================================================
# Action Type (re-export from energy_service for convenience)
# =============================================================================

# Import ActionType from energy_service where costs are defined
from api.services.energy_service import ActionType


# =============================================================================
# Action Status
# =============================================================================


class ActionStatus(str, Enum):
    """Status of an action execution."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Due to insufficient energy


# =============================================================================
# Action Request
# =============================================================================


@dataclass
class ActionRequest:
    """
    Request to execute an action during a heartbeat.

    Contains the action type and any parameters needed for execution.
    """

    action_type: ActionType
    params: dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more important (for trimming)
    reason: str | None = None  # Why this action was chosen

    def __post_init__(self):
        """Validate the request."""
        if not isinstance(self.action_type, ActionType):
            raise ValueError(f"Invalid action type: {self.action_type}")


# =============================================================================
# Action Result
# =============================================================================


@dataclass
class ActionResult:
    """
    Result of executing an action.

    Contains the outcome, any data produced, and execution metadata.
    """

    action_type: ActionType
    status: ActionStatus
    energy_cost: float
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    duration_ms: float | None = None

    def __post_init__(self):
        """Calculate duration if both times are set."""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_ms = delta.total_seconds() * 1000

    @property
    def success(self) -> bool:
        """Check if action completed successfully."""
        return self.status == ActionStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "action": self.action_type.value,
            "status": self.status.value,
            "cost": self.energy_cost,
            "data": self.data,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
        }


# =============================================================================
# Action Plan
# =============================================================================


@dataclass
class ActionPlan:
    """
    A planned sequence of actions for a heartbeat.

    The LLM produces this during the Decide phase.
    """

    actions: list[ActionRequest] = field(default_factory=list)
    total_cost: float = 0.0
    reasoning: str | None = None  # Why this plan was chosen
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Calculate total cost."""
        from api.services.energy_service import DEFAULT_ACTION_COSTS

        self.total_cost = sum(
            DEFAULT_ACTION_COSTS.get(a.action_type, 0.0) for a in self.actions
        )

    def trim_to_budget(self, available_energy: float) -> "ActionPlan":
        """
        Return a new plan trimmed to fit budget.

        Args:
            available_energy: Available energy budget

        Returns:
            New ActionPlan with actions that fit
        """
        from api.services.energy_service import DEFAULT_ACTION_COSTS

        trimmed_actions = []
        remaining = available_energy

        for action in self.actions:
            cost = DEFAULT_ACTION_COSTS.get(action.action_type, 0.0)
            if cost <= remaining:
                trimmed_actions.append(action)
                remaining -= cost
            else:
                break

        return ActionPlan(
            actions=trimmed_actions,
            reasoning=self.reasoning,
        )


# =============================================================================
# Action Execution Record
# =============================================================================


@dataclass
class ActionExecutionRecord:
    """
    Complete record of action execution for a heartbeat.

    Stored in HeartbeatLog.actions_taken.
    """

    id: UUID = field(default_factory=uuid4)
    request: ActionRequest | None = None
    result: ActionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "action": self.request.action_type.value if self.request else None,
            "params": self.request.params if self.request else {},
            "reason": self.request.reason if self.request else None,
            "status": self.result.status.value if self.result else None,
            "cost": self.result.energy_cost if self.result else 0,
            "data": self.result.data if self.result else {},
            "error": self.result.error if self.result else None,
            "duration_ms": self.result.duration_ms if self.result else None,
        }


# =============================================================================
# Environment Snapshot
# =============================================================================


@dataclass
class EnvironmentSnapshot:
    """
    Snapshot of the environment at heartbeat start.

    Captured during the Observe phase.
    """

    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_present: bool = False
    time_since_user_hours: float | None = None
    pending_events: list[dict[str, Any]] = field(default_factory=list)
    recent_memories_count: int = 0
    active_goals_count: int = 0
    queued_goals_count: int = 0
    blocked_goals_count: int = 0
    current_energy: float = 0.0
    heartbeat_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_present": self.user_present,
            "time_since_user_hours": self.time_since_user_hours,
            "pending_events": self.pending_events,
            "recent_memories_count": self.recent_memories_count,
            "active_goals_count": self.active_goals_count,
            "queued_goals_count": self.queued_goals_count,
            "blocked_goals_count": self.blocked_goals_count,
            "current_energy": self.current_energy,
            "heartbeat_number": self.heartbeat_number,
        }


# =============================================================================
# Goals Snapshot
# =============================================================================


@dataclass
class GoalsSnapshot:
    """
    Snapshot of goal state at heartbeat start.

    Part of the Observe phase output.
    """

    active: list[UUID] = field(default_factory=list)
    queued: list[UUID] = field(default_factory=list)
    blocked: list[UUID] = field(default_factory=list)
    stale: list[UUID] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "active": [str(g) for g in self.active],
            "queued": [str(g) for g in self.queued],
            "blocked": [str(g) for g in self.blocked],
            "stale": [str(g) for g in self.stale],
        }


# =============================================================================
# Heartbeat Decision
# =============================================================================


@dataclass
class HeartbeatDecision:
    """
    The AGI's decision for what to do during this heartbeat.

    Produced during the Orient/Decide phases.
    """

    action_plan: ActionPlan
    reasoning: str  # Why these actions were chosen
    focus_goal_id: UUID | None = None  # Primary goal being worked on
    emotional_state: float = 0.0  # -1 to 1
    confidence: float = 0.5  # 0 to 1, how confident in this plan

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "actions": [
                {"action": a.action_type.value, "params": a.params, "reason": a.reason}
                for a in self.action_plan.actions
            ],
            "total_cost": self.action_plan.total_cost,
            "reasoning": self.reasoning,
            "focus_goal_id": str(self.focus_goal_id) if self.focus_goal_id else None,
            "emotional_state": self.emotional_state,
            "confidence": self.confidence,
        }


# =============================================================================
# Heartbeat Summary
# =============================================================================


@dataclass
class HeartbeatSummary:
    """
    Summary of a completed heartbeat.

    Used for creating the episodic memory.
    """

    heartbeat_number: int
    environment: EnvironmentSnapshot
    goals: GoalsSnapshot
    decision: HeartbeatDecision
    results: list[ActionResult] = field(default_factory=list)
    energy_start: float = 0.0
    energy_end: float = 0.0
    narrative: str = ""  # Self-generated description
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None

    @property
    def energy_spent(self) -> float:
        """Total energy spent this heartbeat."""
        return self.energy_start - self.energy_end

    @property
    def actions_completed(self) -> int:
        """Number of successfully completed actions."""
        return sum(1 for r in self.results if r.success)

    @property
    def actions_failed(self) -> int:
        """Number of failed actions."""
        return sum(1 for r in self.results if r.status == ActionStatus.FAILED)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/logging."""
        return {
            "heartbeat_number": self.heartbeat_number,
            "environment": self.environment.to_dict(),
            "goals": self.goals.to_dict(),
            "decision": self.decision.to_dict(),
            "results": [r.to_dict() for r in self.results],
            "energy_start": self.energy_start,
            "energy_end": self.energy_end,
            "energy_spent": self.energy_spent,
            "narrative": self.narrative,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "actions_completed": self.actions_completed,
            "actions_failed": self.actions_failed,
        }
