"""
Goal Models for Heartbeat System
Feature: 004-heartbeat-system
Tasks: T005, T006

Pydantic models for AGI goal management with priority backlog.
Based on heartbeat_design.md specification.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Goal Enums
# =============================================================================


class GoalPriority(str, Enum):
    """
    Goal priority levels forming a backlog structure.

    Levels:
        ACTIVE: Currently being worked on (limit: 1-3)
        QUEUED: Next up when capacity opens (limit: 5-10)
        BACKBURNER: Someday, not now (unlimited)
        COMPLETED: Done, archived
        ABANDONED: Gave up, with reason
    """

    ACTIVE = "active"
    QUEUED = "queued"
    BACKBURNER = "backburner"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class GoalSource(str, Enum):
    """
    Origin of the goal.

    Sources:
        CURIOSITY: Self-generated interest
        USER_REQUEST: User explicitly asked
        IDENTITY: Aligned with self-concept
        DERIVED: Sub-goal of another goal
        EXTERNAL: Triggered by external event
    """

    CURIOSITY = "curiosity"
    USER_REQUEST = "user_request"
    IDENTITY = "identity"
    DERIVED = "derived"
    EXTERNAL = "external"


class GoalMemoryLinkType(str, Enum):
    """Types of links between goals and memories."""

    ORIGIN = "origin"  # Memory that inspired the goal
    PROGRESS = "progress"  # Memory documenting progress
    COMPLETION = "completion"  # Memory documenting completion
    BLOCKER = "blocker"  # Memory describing what's blocking


# =============================================================================
# Goal Progress Note
# =============================================================================


class GoalProgressNote(BaseModel):
    """A progress note added to a goal."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: str = Field(min_length=1, max_length=2000)
    heartbeat_number: int | None = Field(None, description="Heartbeat when note was added")


# =============================================================================
# Goal Blocker
# =============================================================================


class GoalBlocker(BaseModel):
    """Description of what's blocking a goal."""

    description: str = Field(min_length=1, max_length=1000)
    blocked_since: datetime = Field(default_factory=datetime.utcnow)
    dependency_goal_id: UUID | None = Field(None, description="Goal that must complete first")
    external_dependency: str | None = Field(None, description="External factor blocking progress")


# =============================================================================
# Goal Model
# =============================================================================


class Goal(BaseModel):
    """
    AGI goal with priority-based backlog management.

    Goals form the AGI's intention system, guiding what it works on
    during each heartbeat cycle.
    """

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1, max_length=200, description="Short goal title")
    description: str | None = Field(
        None, max_length=2000, description="What does 'done' look like?"
    )
    priority: GoalPriority = GoalPriority.QUEUED
    source: GoalSource = GoalSource.CURIOSITY
    parent_goal_id: UUID | None = Field(None, description="For hierarchical goals")
    progress: list[GoalProgressNote] = Field(default_factory=list)
    blocked_by: GoalBlocker | None = None
    emotional_valence: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Emotional association (-1 negative, +1 positive)",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_touched: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    abandoned_at: datetime | None = None
    abandonment_reason: str | None = Field(None, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Understand user's project architecture",
                "description": "Analyze codebase structure and document findings",
                "priority": "active",
                "source": "user_request",
                "parent_goal_id": None,
                "progress": [
                    {
                        "timestamp": "2025-12-15T10:00:00Z",
                        "content": "Started analyzing database schema",
                        "heartbeat_number": 45,
                    }
                ],
                "blocked_by": None,
                "emotional_valence": 0.3,
                "created_at": "2025-12-14T09:00:00Z",
                "last_touched": "2025-12-15T10:00:00Z",
                "completed_at": None,
                "abandoned_at": None,
                "abandonment_reason": None,
            }
        }
    }


# =============================================================================
# Goal Create/Update DTOs
# =============================================================================


class GoalCreate(BaseModel):
    """DTO for creating a new goal."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    priority: GoalPriority = GoalPriority.QUEUED
    source: GoalSource = GoalSource.CURIOSITY
    parent_goal_id: UUID | None = None
    emotional_valence: float = Field(default=0.0, ge=-1.0, le=1.0)


class GoalUpdate(BaseModel):
    """DTO for updating a goal."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    emotional_valence: float | None = Field(None, ge=-1.0, le=1.0)


class GoalPriorityChange(BaseModel):
    """DTO for changing goal priority."""

    goal_id: UUID
    new_priority: GoalPriority
    reason: str | None = Field(None, max_length=500)


# =============================================================================
# Goal Memory Link
# =============================================================================


class GoalMemoryLink(BaseModel):
    """Link between a goal and a memory."""

    goal_id: UUID
    memory_id: UUID
    link_type: GoalMemoryLinkType
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Goal Assessment (from goal review)
# =============================================================================


class GoalAssessment(BaseModel):
    """
    Assessment from reviewing goals during heartbeat.

    Produced by the free Review Goals action.
    """

    active_goals: list[Goal] = Field(default_factory=list)
    queued_goals: list[Goal] = Field(default_factory=list)
    backburner_goals: list[Goal] = Field(default_factory=list)
    blocked_goals: list[Goal] = Field(default_factory=list)
    stale_goals: list[Goal] = Field(default_factory=list, description="Not touched in 7+ days")
    promotion_candidates: list[Goal] = Field(
        default_factory=list, description="Queued goals that may warrant promotion"
    )
    needs_brainstorm: bool = Field(default=False, description="True if no goals exist")
    issues: list[str] = Field(default_factory=list, description="Problems detected")


# =============================================================================
# Goal Backlog Summary
# =============================================================================


class GoalBacklogSummary(BaseModel):
    """Summary of the goal backlog."""

    active_count: int = 0
    queued_count: int = 0
    backburner_count: int = 0
    completed_count: int = 0
    abandoned_count: int = 0
    total_count: int = 0
    blocked_count: int = 0
    stale_count: int = 0
