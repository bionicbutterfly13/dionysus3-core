# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Track 099 (Memory Amnesia Fix): bootstrap task, ingest after heartbeat, pre-prune flush."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.goal import Goal, GoalAssessment, GoalPriority, GoalSource
from api.models.action import EnvironmentSnapshot, GoalsSnapshot
from api.services.heartbeat_service import HeartbeatService, HeartbeatContext


@pytest.mark.asyncio
async def test_make_decision_sets_task_for_bootstrap(monkeypatch):
    """initial_context['task'] is set so bootstrap recall has a non-empty query."""
    from types import SimpleNamespace

    stored_context: list[dict] = []

    class DummyManager:
        async def run_ooda_cycle(self, ctx: dict):
            stored_context.append(ctx)
            return {"final_plan": "Rest.", "actions": [{"action": "rest", "params": {}, "reason": "Low energy"}], "confidence": 0.9}

    class DummySchemaContext:
        def __init__(self, *_args, **_kwargs):
            pass

        async def query(self, _prompt):
            return {
                "reasoning": "Agreed.",
                "emotional_state": 0.0,
                "confidence": 1.0,
                "focus_goal_id": None,
                "actions": [{"action": "rest", "params": {}, "reason": "Ok"}],
            }

    monkeypatch.setattr("api.agents.consciousness_manager.ConsciousnessManager", DummyManager)
    monkeypatch.setattr("api.utils.schema_context.SchemaContext", DummySchemaContext)
    import sys
    sys.modules["litellm"] = SimpleNamespace(acompletion=AsyncMock(), completion=MagicMock())

    env = EnvironmentSnapshot(heartbeat_number=7, current_energy=10.0)
    goal = Goal(title="Ship feature X", priority=GoalPriority.ACTIVE, source=GoalSource.USER_REQUEST)
    goal_eval = GoalAssessment(
        active_goals=[goal],
        queued_goals=[],
        blocked_goals=[],
        stale_goals=[],
        issues=[],
    )
    goals = GoalsSnapshot(active=[goal.id], queued=[], blocked=[], stale=[])
    context = HeartbeatContext(
        environment=env,
        goal_assessment=goal_eval,
        goals=goals,
    )

    service = HeartbeatService(driver=MagicMock())
    await service._make_decision(context)

    assert len(stored_context) == 1
    initial_context = stored_context[0]
    task = initial_context.get("task", "")
    assert "Heartbeat 7" in task
    assert "Ship feature X" in task or "goal" in task.lower()


@pytest.mark.asyncio
async def test_route_heartbeat_memory_called_and_does_not_raise():
    """_route_heartbeat_memory runs and catches router exceptions."""
    from api.models.action import HeartbeatSummary, HeartbeatDecision, ActionPlan
    from api.services.heartbeat_service import HeartbeatService

    summary = MagicMock(spec=HeartbeatSummary)
    summary.heartbeat_number = 1
    summary.narrative = "I rested."
    summary.decision = MagicMock(reasoning="Low energy.")

    service = HeartbeatService(driver=MagicMock())
    with patch("api.services.memory_basin_router.get_memory_basin_router") as m:
        router = MagicMock()
        router.route_memory = AsyncMock()
        m.return_value = router

        await service._route_heartbeat_memory(summary)

    router.route_memory.assert_called_once()
    assert "Heartbeat #1" in router.route_memory.call_args[1]["content"]
    assert "I rested." in router.route_memory.call_args[1]["content"]
    assert "heartbeat:1" in router.route_memory.call_args[1]["source_id"]


@pytest.mark.asyncio
async def test_route_heartbeat_memory_swallows_errors():
    """_route_heartbeat_memory never raises; logs and returns on failure."""
    from api.models.action import HeartbeatSummary
    from api.services.heartbeat_service import HeartbeatService

    summary = MagicMock(spec=HeartbeatSummary)
    summary.heartbeat_number = 2
    summary.narrative = "Done."
    summary.decision = MagicMock(reasoning="Ok.")

    service = HeartbeatService(driver=MagicMock())
    with patch("api.services.memory_basin_router.get_memory_basin_router") as m:
        m.side_effect = RuntimeError("router unavailable")

        await service._route_heartbeat_memory(summary)

    # No raise
    m.assert_called_once()
