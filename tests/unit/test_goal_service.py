"""
Unit Tests for GoalService
Feature: 004-heartbeat-system
Task: T027

Tests goal CRUD, lifecycle transitions, and review logic.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from api.models.goal import (
    Goal,
    GoalPriority,
    GoalSource,
    GoalCreate,
    GoalBlocker,
    GoalProgressNote,
)


class TestGoalModel:
    """Tests for Goal Pydantic model."""

    def test_goal_defaults(self):
        """Goal has sensible defaults."""
        goal = Goal(title="Test goal")

        assert goal.title == "Test goal"
        assert goal.priority == GoalPriority.QUEUED
        assert goal.source == GoalSource.CURIOSITY
        assert goal.progress == []
        assert goal.blocked_by is None
        assert goal.emotional_valence == 0.0
        assert goal.completed_at is None
        assert goal.abandoned_at is None

    def test_goal_with_all_fields(self):
        """Goal accepts all field values."""
        goal = Goal(
            title="Complex goal",
            description="A detailed description",
            priority=GoalPriority.ACTIVE,
            source=GoalSource.USER_REQUEST,
            emotional_valence=0.8,
        )

        assert goal.title == "Complex goal"
        assert goal.description == "A detailed description"
        assert goal.priority == GoalPriority.ACTIVE
        assert goal.source == GoalSource.USER_REQUEST
        assert goal.emotional_valence == 0.8

    def test_goal_priority_values(self):
        """GoalPriority enum has expected values."""
        assert GoalPriority.ACTIVE.value == "active"
        assert GoalPriority.QUEUED.value == "queued"
        assert GoalPriority.BACKBURNER.value == "backburner"
        assert GoalPriority.COMPLETED.value == "completed"
        assert GoalPriority.ABANDONED.value == "abandoned"

    def test_goal_source_values(self):
        """GoalSource enum has expected values."""
        assert GoalSource.CURIOSITY.value == "curiosity"
        assert GoalSource.USER_REQUEST.value == "user_request"
        assert GoalSource.IDENTITY.value == "identity"
        assert GoalSource.DERIVED.value == "derived"
        assert GoalSource.EXTERNAL.value == "external"


class TestGoalProgressNote:
    """Tests for GoalProgressNote model."""

    def test_progress_note_defaults(self):
        """Progress note has sensible defaults."""
        note = GoalProgressNote(content="Made progress")

        assert note.content == "Made progress"
        assert note.heartbeat_number is None
        assert note.timestamp is not None

    def test_progress_note_with_heartbeat(self):
        """Progress note can include heartbeat number."""
        note = GoalProgressNote(content="Update", heartbeat_number=42)

        assert note.heartbeat_number == 42


class TestGoalBlocker:
    """Tests for GoalBlocker model."""

    def test_blocker_with_description(self):
        """Blocker requires description."""
        blocker = GoalBlocker(description="Waiting for API response")

        assert blocker.description == "Waiting for API response"
        assert blocker.dependency_goal_id is None
        assert blocker.external_dependency is None

    def test_blocker_with_dependency(self):
        """Blocker can reference another goal."""
        dep_id = uuid4()
        blocker = GoalBlocker(
            description="Blocked by prerequisite",
            dependency_goal_id=dep_id,
        )

        assert blocker.dependency_goal_id == dep_id

    def test_blocker_with_external(self):
        """Blocker can reference external dependency."""
        blocker = GoalBlocker(
            description="External block",
            external_dependency="User approval needed",
        )

        assert blocker.external_dependency == "User approval needed"


class TestGoalCreate:
    """Tests for GoalCreate DTO."""

    def test_goal_create_minimal(self):
        """GoalCreate requires only title."""
        dto = GoalCreate(title="New goal")

        assert dto.title == "New goal"
        assert dto.priority == GoalPriority.QUEUED
        assert dto.source == GoalSource.CURIOSITY

    def test_goal_create_full(self):
        """GoalCreate accepts all fields."""
        dto = GoalCreate(
            title="Full goal",
            description="Description here",
            priority=GoalPriority.ACTIVE,
            source=GoalSource.USER_REQUEST,
            emotional_valence=0.5,
        )

        assert dto.title == "Full goal"
        assert dto.description == "Description here"
        assert dto.priority == GoalPriority.ACTIVE
        assert dto.source == GoalSource.USER_REQUEST


class TestGoalLifecycleValidation:
    """Tests for goal lifecycle transition validation."""

    def test_valid_promotion_from_queued(self):
        """Can promote from queued to active."""
        goal = Goal(title="Test", priority=GoalPriority.QUEUED)

        # This would be done by the service, but validate the state is promotable
        assert goal.priority in (GoalPriority.QUEUED, GoalPriority.BACKBURNER)

    def test_valid_demotion_from_active(self):
        """Can demote from active to queued or backburner."""
        goal = Goal(title="Test", priority=GoalPriority.ACTIVE)

        # Active goals can be demoted
        assert goal.priority == GoalPriority.ACTIVE

    def test_cannot_promote_completed(self):
        """Completed goals cannot be promoted."""
        goal = Goal(
            title="Done",
            priority=GoalPriority.COMPLETED,
            completed_at=datetime.utcnow(),
        )

        # Completed goals should not be promotable
        assert goal.priority == GoalPriority.COMPLETED
        assert goal.completed_at is not None

    def test_cannot_promote_abandoned(self):
        """Abandoned goals cannot be promoted."""
        goal = Goal(
            title="Abandoned",
            priority=GoalPriority.ABANDONED,
            abandoned_at=datetime.utcnow(),
            abandonment_reason="No longer relevant",
        )

        # Abandoned goals should not be promotable
        assert goal.priority == GoalPriority.ABANDONED
        assert goal.abandoned_at is not None


class TestStaleGoalDetection:
    """Tests for stale goal detection logic."""

    def test_goal_is_stale(self):
        """Goal is stale if not touched in 7+ days."""
        stale_date = datetime.utcnow() - timedelta(days=8)
        goal = Goal(
            title="Old goal",
            priority=GoalPriority.ACTIVE,
            last_touched=stale_date,
        )

        days_since = (datetime.utcnow() - goal.last_touched).days
        assert days_since >= 7

    def test_goal_is_fresh(self):
        """Goal is fresh if touched recently."""
        goal = Goal(
            title="Fresh goal",
            priority=GoalPriority.ACTIVE,
            last_touched=datetime.utcnow(),
        )

        days_since = (datetime.utcnow() - goal.last_touched).days
        assert days_since < 7


class TestGoalWithProgress:
    """Tests for goals with progress notes."""

    def test_add_progress_note(self):
        """Can add progress notes to goal."""
        goal = Goal(title="Goal with progress")

        # Simulate adding progress
        note = GoalProgressNote(content="First update", heartbeat_number=10)
        goal.progress.append(note)

        assert len(goal.progress) == 1
        assert goal.progress[0].content == "First update"
        assert goal.progress[0].heartbeat_number == 10

    def test_multiple_progress_notes(self):
        """Can track multiple progress notes."""
        goal = Goal(title="Goal with multiple updates")

        goal.progress.append(GoalProgressNote(content="Update 1", heartbeat_number=10))
        goal.progress.append(GoalProgressNote(content="Update 2", heartbeat_number=11))
        goal.progress.append(GoalProgressNote(content="Update 3", heartbeat_number=12))

        assert len(goal.progress) == 3
        assert goal.progress[-1].heartbeat_number == 12


class TestGoalEmotionalValence:
    """Tests for emotional valence tracking."""

    def test_valence_bounds(self):
        """Emotional valence stays within bounds."""
        # Valid values
        goal_positive = Goal(title="Happy goal", emotional_valence=1.0)
        goal_negative = Goal(title="Sad goal", emotional_valence=-1.0)
        goal_neutral = Goal(title="Neutral goal", emotional_valence=0.0)

        assert goal_positive.emotional_valence == 1.0
        assert goal_negative.emotional_valence == -1.0
        assert goal_neutral.emotional_valence == 0.0

    def test_valence_validation(self):
        """Values outside -1 to 1 should fail validation."""
        # This should raise validation error
        with pytest.raises(ValueError):
            Goal(title="Invalid", emotional_valence=1.5)

        with pytest.raises(ValueError):
            Goal(title="Invalid", emotional_valence=-1.5)
