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

    def test_epistemic_value_computation(self):
        """Test that epistemic value is computed from belief uncertainty."""
        # High certainty beliefs (near 0 or 1) = low epistemic value
        certain_state = ActiveInferenceState(beliefs={"a": 0.99, "b": 0.01})
        certain_epistemic = certain_state._compute_epistemic_value()
        
        # Uncertain beliefs (near 0.5) = high epistemic value
        uncertain_state = ActiveInferenceState(beliefs={"a": 0.5, "b": 0.5})
        uncertain_epistemic = uncertain_state._compute_epistemic_value()
        
        # Uncertain beliefs should have higher epistemic value
        assert uncertain_epistemic > certain_epistemic
        # Both should be non-negative
        assert certain_epistemic >= 0
        assert uncertain_epistemic >= 0

    def test_epistemic_value_reduces_free_energy(self):
        """Test that high epistemic value reduces free energy (encourages exploration)."""
        # Two states with same prediction error but different belief uncertainty
        certain_state = ActiveInferenceState(beliefs={"a": 0.99})
        uncertain_state = ActiveInferenceState(beliefs={"a": 0.5})
        
        # Same prediction error
        certain_state.update_beliefs(prediction_error=0.3)
        uncertain_state.update_beliefs(prediction_error=0.3)
        
        # Uncertain state should have LOWER free energy (epistemic bonus)
        # This encourages exploration of uncertain states
        assert uncertain_state.free_energy < certain_state.free_energy


class TestMetaToTNode:
    def test_default_node(self):
        node = MetaToTNode()
        assert node.node_type == MetaToTNodeType.ROOT
        assert node.depth == 0
        assert node.score == 0.0
        assert node.thought_content == ""
        assert node.cpa_domain == "explore"


    def test_node_with_active_inference_state(self):
        state = ActiveInferenceState(beliefs={"x": 0.7}, precision=0.9)
        node = MetaToTNode(
            node_type=MetaToTNodeType.EXPLORATION,
            depth=2,
            thought_content="test thought",
            cpa_domain="challenge",
            active_inference_state=state,
            score=0.8,
        )
        assert node.node_type == MetaToTNodeType.EXPLORATION
        assert node.depth == 2
        assert node.score == 0.8
        assert node.active_inference_state.beliefs == {"x": 0.7}






class TestMetaToTConfig:
    def test_defaults(self):
        config = MetaToTConfig()
        assert config.max_depth == 4
        assert config.branching_factor == 3
        assert config.time_budget_seconds == 5.0
        assert config.use_llm is True
        assert config.persist_trace is True

    def test_from_overrides(self):
        overrides = {"max_depth": 6, "branching_factor": 5, "use_llm": False}
        config = MetaToTConfig.from_overrides(overrides)
        assert config.max_depth == 6
        assert config.branching_factor == 5
        assert config.use_llm is False
        # Default values preserved
        assert config.time_budget_seconds == 5.0

    def test_from_overrides_none(self):
        config = MetaToTConfig.from_overrides(None)
        assert config.max_depth == 4





class TestMetaToTEngine:
    @pytest.mark.asyncio
    async def test_run_no_llm(self):
        config = MetaToTConfig(
            use_llm=False,
            persist_trace=False,
            max_depth=2,
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

    def test_select_best_path_prefers_score(self):
        engine = MetaToTEngine()
        root = MetaToTNode(node_id="root")
        # Higher score is better (lower Free Energy)
        child_low_score = MetaToTNode(node_id="low", score=0.1)
        child_high_score = MetaToTNode(node_id="high", score=0.9)
        root.children_ids = ["low", "high"]
        engine.node_storage = {
            "root": root,
            "low": child_low_score,
            "high": child_high_score,
        }

        path = engine._select_best_path(root)
        assert path[1] == "high"

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
