"""
Unit tests for Meta-ToT Engine.
Feature: 041-meta-tot-engine
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import math

from api.services.meta_tot_engine import (
    ActiveInferenceState,
    MetaToTNode,
    MetaToTNodeType,
    MetaToTConfig,
    MetaToTEngine,
    POMCPActiveInferencePlanner,
    get_meta_tot_engine,
)
from api.models.meta_tot import MetaToTDecision


class TestActiveInferenceState:
    def test_default_state(self):
        state = ActiveInferenceState()
        assert state.prediction_error == 0.0
        assert state.free_energy == 0.0
        assert state.surprise == 0.0
        assert state.precision == 1.0
        assert state.reasoning_level == 0

    def test_compute_prediction_error(self):
        state = ActiveInferenceState(beliefs={"a": 0.5, "b": 0.3})
        error = state.compute_prediction_error({"a": 0.8, "b": 0.3})
        # |0.8 - 0.5| * 1.0 + |0.3 - 0.3| * 1.0 = 0.3
        assert error == pytest.approx(0.3, rel=0.01)
        assert state.prediction_error == error

    def test_update_beliefs(self):
        state = ActiveInferenceState(beliefs={"a": 0.5})
        state.prediction_updates = {"a": 1.0}
        initial = state.beliefs["a"]
        state.update_beliefs(prediction_error=0.5, learning_rate=0.1)
        # belief should change based on gradient
        assert state.beliefs["a"] != initial
        assert state.free_energy > 0
        assert state.surprise > 0


class TestMetaToTNode:
    def test_default_node(self):
        node = MetaToTNode()
        assert node.node_type == MetaToTNodeType.ROOT
        assert node.depth == 0
        assert node.visit_count == 0
        assert node.value_estimate == 0.0

    def test_ucb_score_unvisited(self):
        node = MetaToTNode()
        score = node.compute_ucb_score(total_parent_visits=10)
        assert score == float("inf")

    def test_ucb_score_visited(self):
        node = MetaToTNode(visit_count=5, value_estimate=0.6)
        score = node.compute_ucb_score(total_parent_visits=20, exploration_constant=2.0)
        # exploitation + exploration + prediction_bonus
        exploitation = 0.6
        exploration = 2.0 * math.sqrt(math.log(20) / 5)
        prediction_bonus = 1.0 / (1.0 + 0.0)  # no prediction error
        expected = exploitation + exploration + prediction_bonus
        assert score == pytest.approx(expected, rel=0.01)

    def test_update_from_rollout(self):
        node = MetaToTNode(visit_count=0, value_estimate=0.0)
        node.update_from_rollout(reward=0.8, prediction_error=0.1, learning_rate=0.1)
        assert node.visit_count == 1
        assert node.value_estimate > 0
        assert node.uncertainty_estimate < 1.0


class TestMetaToTConfig:
    def test_defaults(self):
        config = MetaToTConfig()
        assert config.max_depth == 4
        assert config.simulation_count == 32
        assert config.exploration_constant == 2.0
        assert config.branching_factor == 3
        assert config.time_budget_seconds == 5.0
        assert config.use_llm is True
        assert config.persist_trace is True

    def test_from_overrides(self):
        overrides = {"max_depth": 6, "simulation_count": 50, "use_llm": False}
        config = MetaToTConfig.from_overrides(overrides)
        assert config.max_depth == 6
        assert config.simulation_count == 50
        assert config.use_llm is False
        # Default values preserved
        assert config.branching_factor == 3

    def test_from_overrides_none(self):
        config = MetaToTConfig.from_overrides(None)
        assert config.max_depth == 4


class TestPOMCPActiveInferencePlanner:
    @pytest.mark.asyncio
    async def test_plan_no_actions(self):
        planner = POMCPActiveInferencePlanner()
        action, value = await planner.plan({"x": 0.5}, [])
        assert action == ""
        assert value == 0.0

    @pytest.mark.asyncio
    async def test_plan_selects_action(self):
        planner = POMCPActiveInferencePlanner(simulation_count=10)
        actions = ["action_a", "action_b", "action_c"]
        action, value = await planner.plan({"x": 0.5}, actions)
        assert action in actions
        assert value >= 0.0


class TestMetaToTEngine:
    @pytest.mark.asyncio
    async def test_run_no_llm(self):
        config = MetaToTConfig(
            use_llm=False,
            persist_trace=False,
            max_depth=2,
            simulation_count=5,
            branching_factor=2,
            random_seed=42,
        )
        engine = MetaToTEngine(config)
        decision = MetaToTDecision(
            use_meta_tot=True,
            complexity_score=0.8,
            uncertainty_score=0.5,
            rationale="test",
        )
        with patch.object(engine, "_update_basins", new_callable=AsyncMock):
            result, trace = await engine.run(
                problem="Test problem for planning",
                context={"constraints": ["c1"]},
                decision=decision,
            )

        assert result.session_id
        assert len(result.best_path) > 0
        assert result.confidence >= 0.0
        assert "branch_count" in result.metrics
        assert trace is not None
        assert len(trace.nodes) > 0

    @pytest.mark.asyncio
    async def test_run_with_trace_persistence(self):
        config = MetaToTConfig(
            use_llm=False,
            persist_trace=True,
            max_depth=1,
            simulation_count=2,
            random_seed=42,
        )
        engine = MetaToTEngine(config)

        mock_trace_service = MagicMock()
        mock_trace_service.store_trace = AsyncMock(return_value="trace-id-123")

        with patch("api.services.meta_tot_engine.get_meta_tot_trace_service", return_value=mock_trace_service):
            with patch.object(engine, "_update_basins", new_callable=AsyncMock):
                result, trace = await engine.run(
                    problem="Test",
                    context={},
                )

        mock_trace_service.store_trace.assert_called_once()
        assert result.trace_id == "trace-id-123"

    def test_build_observation(self):
        engine = MetaToTEngine()
        obs = engine._build_observation("short problem", {"constraints": ["a", "b"]})
        assert "problem_complexity" in obs
        assert "context_richness" in obs
        assert "constraint_density" in obs
        assert obs["constraint_density"] == pytest.approx(0.2, rel=0.01)

    def test_domain_to_node_type(self):
        engine = MetaToTEngine()
        assert engine._domain_to_node_type("explore") == MetaToTNodeType.EXPLORATION
        assert engine._domain_to_node_type("challenge") == MetaToTNodeType.CHALLENGE
        assert engine._domain_to_node_type("evolve") == MetaToTNodeType.EVOLUTION
        assert engine._domain_to_node_type("integrate") == MetaToTNodeType.INTEGRATION
        assert engine._domain_to_node_type("unknown") == MetaToTNodeType.LEAF

    def test_inherit_state(self):
        engine = MetaToTEngine()
        parent = MetaToTNode(active_inference_state=ActiveInferenceState(
            beliefs={"a": 0.5},
            precision=0.9,
            reasoning_level=2,
        ))
        child_state = engine._inherit_state(parent)
        assert child_state.beliefs == {"a": 0.5}
        assert child_state.precision == 0.9
        assert child_state.reasoning_level == 3
        assert child_state.parent_state_id == parent.active_inference_state.state_id

    def test_fallback_candidates(self):
        engine = MetaToTEngine()
        node = MetaToTNode(thought_content="original thought")
        candidates = engine._fallback_candidates(node, "explore")
        assert len(candidates) == 3
        assert all("explore" in c.lower() for c in candidates)

    def test_parse_candidates_json(self):
        engine = MetaToTEngine()
        response = '["branch 1", "branch 2", "branch 3"]'
        candidates = engine._parse_candidates(response, 3)
        assert candidates == ["branch 1", "branch 2", "branch 3"]

    def test_parse_candidates_markdown_json(self):
        engine = MetaToTEngine()
        response = '```json\n["branch 1", "branch 2"]\n```'
        candidates = engine._parse_candidates(response, 2)
        assert candidates == ["branch 1", "branch 2"]

    def test_parse_candidates_lines(self):
        engine = MetaToTEngine()
        response = "- branch 1\n- branch 2\n- branch 3"
        candidates = engine._parse_candidates(response, 3)
        assert len(candidates) == 3

    def test_generate_actions_from_children(self):
        engine = MetaToTEngine()
        root = MetaToTNode(node_id="root")
        child1 = MetaToTNode(node_id="c1", thought_content="action A")
        child2 = MetaToTNode(node_id="c2", thought_content="action B")
        root.children_ids = ["c1", "c2"]
        engine.node_storage = {"root": root, "c1": child1, "c2": child2}
        actions = engine._generate_actions(root)
        assert actions == ["action A", "action B"]

    def test_node_to_trace(self):
        engine = MetaToTEngine()
        node = MetaToTNode(
            node_id="n1",
            parent_id="p1",
            depth=2,
            node_type=MetaToTNodeType.EXPLORATION,
            cpa_domain="explore",
            thought_content="test thought",
            score=0.8,
            visit_count=5,
            value_estimate=0.7,
        )
        trace = engine._node_to_trace(node)
        assert trace.node_id == "n1"
        assert trace.parent_id == "p1"
        assert trace.depth == 2
        assert trace.node_type == "exploration"
        assert trace.thought == "test thought"


class TestGetMetaToTEngine:
    def test_singleton(self):
        import api.services.meta_tot_engine as module
        module._meta_tot_engine = None
        eng1 = get_meta_tot_engine()
        eng2 = get_meta_tot_engine()
        assert eng1 is eng2
        module._meta_tot_engine = None
