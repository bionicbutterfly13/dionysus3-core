import json
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from api.models.action import (
    ActionPlan,
    ActionRequest,
    ActionResult,
    ActionStatus,
    ActionType,
    EnvironmentSnapshot,
    GoalsSnapshot,
    HeartbeatDecision,
    HeartbeatSummary,
)
from api.services.heartbeat_service import HeartbeatService


class FakeSession:
    def __init__(self):
        self.closed = False
        self.run_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.closed = True

    async def run(self, query, **kwargs):
        if self.closed:
            raise RuntimeError("session closed")
        self.run_calls.append((query, kwargs))
        return MagicMock()


class FakeDriver:
    def __init__(self, session):
        self._session = session

    def session(self):
        return self._session


def _build_summary(focus_goal_id=None):
    decision = HeartbeatDecision(
        action_plan=ActionPlan(
            actions=[ActionRequest(action_type=ActionType.REST, reason="noop")]
        ),
        reasoning="fallback reasoning",
        focus_goal_id=focus_goal_id,
        confidence=0.5,
    )
    summary = HeartbeatSummary(
        heartbeat_number=1,
        environment=EnvironmentSnapshot(user_present=False),
        goals=GoalsSnapshot(),
        decision=decision,
        results=[
            ActionResult(
                action_type=ActionType.REST,
                status=ActionStatus.COMPLETED,
                energy_cost=0.0,
            )
        ],
        energy_start=10.0,
        energy_end=10.0,
    )
    return summary


@pytest.mark.asyncio
async def test_make_decision_handles_missing_normalized_reasoning(monkeypatch):
    sys.modules["litellm"] = SimpleNamespace(
        acompletion=AsyncMock(),
        completion=AsyncMock(),
    )

    class DummyManager:
        async def run_ooda_cycle(self, _context):
            return {"final_plan": "fallback plan", "actions": []}

    class DummySchemaContext:
        def __init__(self, *_args, **_kwargs):
            pass

        async def query(self, _prompt):
            return {}

    monkeypatch.setattr(
        "api.agents.consciousness_manager.ConsciousnessManager",
        DummyManager,
    )
    monkeypatch.setattr(
        "api.utils.schema_context.SchemaContext",
        DummySchemaContext,
    )

    from api.models.goal import GoalAssessment
    from api.services.heartbeat_service import HeartbeatContext

    service = HeartbeatService(driver=FakeDriver(FakeSession()))
    context = HeartbeatContext(
        environment=EnvironmentSnapshot(),
        goals=GoalsSnapshot(),
        goal_assessment=GoalAssessment(),
    )

    decision = await service._make_decision(context)

    assert decision.reasoning == "fallback plan"


@pytest.mark.asyncio
async def test_record_heartbeat_focus_goal_runs_inside_session():
    session = FakeSession()
    service = HeartbeatService(driver=FakeDriver(session))
    summary = _build_summary(focus_goal_id=uuid4())

    await service._record_heartbeat(summary)

    assert any("TOUCHED_GOAL" in call[0] for call in session.run_calls)


@pytest.mark.asyncio
async def test_generate_narrative_handles_missing_time_since_user():
    async def fake_completion(*args, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
        )

    sys.modules["litellm"] = SimpleNamespace(completion=fake_completion)

    service = HeartbeatService(driver=FakeDriver(FakeSession()))
    summary = _build_summary()
    summary.environment.time_since_user_hours = None

    narrative = await service._generate_narrative_llm(summary)

    assert narrative == "ok"


@pytest.mark.asyncio
async def test_generate_narrative_fallback_uses_decision_reasoning():
    async def failing_completion(*args, **kwargs):
        raise RuntimeError("boom")

    sys.modules["litellm"] = SimpleNamespace(completion=failing_completion)

    service = HeartbeatService(driver=FakeDriver(FakeSession()))
    summary = _build_summary()

    narrative = await service._generate_narrative_llm(summary)

    assert "fallback reasoning" in narrative


@pytest.mark.asyncio
async def test_generate_strategic_memory_coerces_tags_to_list():
    async def fake_completion(*args, **kwargs):
        content = json.dumps(
            {"lesson": "keep going", "importance": 0.9, "tags": "strategy"}
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )

    sys.modules["litellm"] = SimpleNamespace(completion=fake_completion)

    session = FakeSession()
    service = HeartbeatService(driver=FakeDriver(session))

    await service._generate_strategic_memory(["insight"])

    tags = [call[1].get("tags") for call in session.run_calls if "tags" in call[1]]
    assert tags and isinstance(tags[0], list)


@pytest.mark.asyncio
async def test_metacognition_run_initializes_agent_when_missing(monkeypatch):
    sys.modules["litellm"] = SimpleNamespace(
        acompletion=AsyncMock(),
        completion=AsyncMock(),
    )

    from api.agents.metacognition_agent import MetacognitionAgent
    from api.models.cognitive import FlowState

    class DummyAgent:
        def __init__(self):
            self.max_steps = 5

        def run(self, task):
            return f"ran:{task}"

    dummy_agent = DummyAgent()
    enter_called = {"value": False}

    def fake_enter(self):
        enter_called["value"] = True
        self.agent = dummy_agent
        return self

    async def fake_analyze_current_flow(*args, **kwargs):
        return SimpleNamespace(state=FlowState.FLOWING, summary="steady")

    monkeypatch.setattr(MetacognitionAgent, "__enter__", fake_enter)
    monkeypatch.setattr(MetacognitionAgent, "__exit__", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "api.services.context_stream.get_context_stream_service",
        lambda: SimpleNamespace(analyze_current_flow=fake_analyze_current_flow),
    )
    monkeypatch.setattr(
        "api.services.llm_service.get_router_model",
        lambda model_id=None: SimpleNamespace(model_id=model_id),
    )

    agent = MetacognitionAgent()
    result = await agent.run("task")

    assert enter_called["value"] is True
    assert result.startswith("ran:")


def test_consciousness_manager_attaches_self_modeling_callback(monkeypatch):
    from smolagents.memory import ActionStep
    sys.modules["litellm"] = SimpleNamespace(
        acompletion=AsyncMock(),
        completion=AsyncMock(),
    )
    import api.agents.consciousness_manager as cm

    class DummyAgent:
        def __init__(self):
            self.step_callbacks = {}
            self.tools = {}

    class DummyWrapper:
        def __init__(self, agent):
            self._agent = agent

        def get_managed(self):
            return self._agent

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    class DummyMarketingWrapper:
        def __init__(self, _model_id):
            self._agent = dummy_agent

        def get_managed(self):
            return self._agent

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    class DummyAudit:
        def get_registry(self, *_args, **_kwargs):
            return {}

    class DummyCodeAgent:
        def __init__(self, *args, **kwargs):
            pass

    dummy_agent = DummyAgent()
    dummy_cb = MagicMock()

    monkeypatch.setattr(cm, "CodeAgent", DummyCodeAgent)
    monkeypatch.setattr("api.agents.audit.get_audit_callback", lambda: DummyAudit())
    monkeypatch.setattr(cm, "create_self_modeling_callback", lambda *args, **kwargs: dummy_cb)
    monkeypatch.setattr(cm, "ManagedMarketingStrategist", DummyMarketingWrapper)
    monkeypatch.setattr(
        "api.services.llm_service.get_router_model",
        lambda model_id=None: SimpleNamespace(model_id=model_id),
    )

    manager = cm.ConsciousnessManager()
    manager.perception_wrapper = DummyWrapper(dummy_agent)
    manager.reasoning_wrapper = DummyWrapper(dummy_agent)
    manager.metacognition_wrapper = DummyWrapper(dummy_agent)
    manager.marketing_wrapper = DummyWrapper(dummy_agent)

    manager.__enter__()

    callback = dummy_agent.step_callbacks.get(ActionStep)
    assert callback is not None

    step = ActionStep(step_number=1, timing=MagicMock())
    callback(step, agent=None)

    assert dummy_cb.log_step.call_count >= 1
