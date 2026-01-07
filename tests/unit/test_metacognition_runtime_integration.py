"""
Unit tests for Metacognition Runtime Integration

Tests agent runtime integration with metacognition patterns.
"""

import pytest
import asyncio

from api.services.metacognition_runtime_integration import (
    MetacognitionRuntimeMonitor,
    MetacognitionRuntimeController,
    ThoughtseedCompetitionRuntime,
    LoopPreventionRuntime,
    MetacognitionRuntimeIntegration,
    get_metacognition_runtime_integration,
)


class TestMetacognitionRuntimeMonitor:
    """Tests for MetacognitionRuntimeMonitor."""

    def test_initialization(self):
        """Test monitor initialization."""
        monitor = MetacognitionRuntimeMonitor()

        assert monitor is not None
        assert len(monitor._monitoring_state) == 0

    @pytest.mark.asyncio
    async def test_assess_cognitive_state(self):
        """Test cognitive state assessment."""
        monitor = MetacognitionRuntimeMonitor()

        metrics = {
            "progress": 0.5,
            "confidence": 0.6,
            "surprise": 0.2,
            "basin_stability": 0.7,
        }

        # First assessment (step 1)
        result1 = await monitor.assess_cognitive_state("agent1", metrics)
        assert result1 is None  # Not yet at interval

        # Second assessment (step 2)
        result2 = await monitor.assess_cognitive_state("agent1", metrics)
        assert result2 is None  # Not yet at interval

        # Third assessment (step 3) should trigger (3-step interval)
        result3 = await monitor.assess_cognitive_state("agent1", metrics)
        assert result3 is not None

    def test_reset_monitoring_state(self):
        """Test resetting monitoring state."""
        monitor = MetacognitionRuntimeMonitor()

        # Create monitoring state
        monitor._monitoring_state["agent1"] = {
            "step_count": 5,
            "last_assessment": None,
        }

        monitor.reset_monitoring_state("agent1")

        assert "agent1" not in monitor._monitoring_state


class TestMetacognitionRuntimeController:
    """Tests for MetacognitionRuntimeController."""

    def test_initialization(self):
        """Test controller initialization."""
        controller = MetacognitionRuntimeController()

        assert controller is not None

    @pytest.mark.asyncio
    async def test_generate_control_actions_high_surprise(self):
        """Test control action generation for high surprise."""
        controller = MetacognitionRuntimeController()

        actions = await controller.generate_control_actions(
            agent_id="agent1",
            surprise=0.8,  # Above threshold
            confidence=0.5,
            free_energy=1.0,
        )

        assert len(actions) == 1
        assert actions[0]["action"] == "generate_thoughtseeds"
        assert "surprise" in actions[0]["metrics"]

    @pytest.mark.asyncio
    async def test_generate_control_actions_low_confidence(self):
        """Test control action generation for low confidence."""
        controller = MetacognitionRuntimeController()

        actions = await controller.generate_control_actions(
            agent_id="agent1",
            surprise=0.5,
            confidence=0.2,  # Below threshold
            free_energy=1.0,
        )

        assert len(actions) == 1
        assert actions[0]["action"] == "replan"

    @pytest.mark.asyncio
    async def test_generate_control_actions_high_free_energy(self):
        """Test control action generation for high free energy."""
        controller = MetacognitionRuntimeController()

        actions = await controller.generate_control_actions(
            agent_id="agent1",
            surprise=0.5,
            confidence=0.5,
            free_energy=4.0,  # Above threshold
        )

        assert len(actions) == 1
        assert actions[0]["action"] == "reduce_model_complexity"

    @pytest.mark.asyncio
    async def test_generate_control_actions_no_action(self):
        """Test when no control action is needed."""
        controller = MetacognitionRuntimeController()

        actions = await controller.generate_control_actions(
            agent_id="agent1",
            surprise=0.3,
            confidence=0.7,
            free_energy=1.0,
        )

        assert len(actions) == 0


class TestThoughtseedCompetitionRuntime:
    """Tests for ThoughtseedCompetitionRuntime."""

    def test_initialization(self):
        """Test competition runtime initialization."""
        runtime = ThoughtseedCompetitionRuntime()

        assert runtime is not None

    def test_rank_thoughtseeds_by_free_energy(self):
        """Test ranking thoughtseeds by free energy."""
        runtime = ThoughtseedCompetitionRuntime()

        thoughtseeds = [
            {"id": "ts1", "free_energy": 3.0, "content": "thought1"},
            {"id": "ts2", "free_energy": 1.5, "content": "thought2"},
            {"id": "ts3", "free_energy": 2.0, "content": "thought3"},
        ]

        winner, ranked = runtime.rank_thoughtseeds(thoughtseeds)

        assert winner is not None
        assert winner["id"] == "ts2"  # Lowest free energy
        assert winner["free_energy"] == 1.5

        assert ranked[0]["id"] == "ts2"
        assert ranked[1]["id"] == "ts3"
        assert ranked[2]["id"] == "ts1"

    def test_rank_thoughtseeds_empty(self):
        """Test ranking with empty thoughtseeds."""
        runtime = ThoughtseedCompetitionRuntime()

        winner, ranked = runtime.rank_thoughtseeds([])

        assert winner is None
        assert ranked == []

    def test_get_competition_config(self):
        """Test getting competition configuration."""
        runtime = ThoughtseedCompetitionRuntime()

        config = runtime.get_competition_config()

        assert "algorithm" in config
        assert "max_iterations" in config
        assert config["algorithm"] == "meta_tot_mcts"


class TestLoopPreventionRuntime:
    """Tests for LoopPreventionRuntime."""

    def test_initialization(self):
        """Test loop prevention runtime initialization."""
        runtime = LoopPreventionRuntime()

        assert runtime is not None
        assert len(runtime._recursion_stacks) == 0

    def test_create_recursion_context(self):
        """Test creating recursion context."""
        runtime = LoopPreventionRuntime()

        pattern = runtime.create_recursion_context("ctx1")

        assert pattern is not None
        assert "ctx1" in runtime._recursion_stacks

    def test_enter_recursion_depth_limit(self):
        """Test entering recursion with depth limit."""
        runtime = LoopPreventionRuntime()

        # Create context with max_depth=2
        assert runtime.enter_recursion("ctx1")  # depth 0->1
        assert runtime.enter_recursion("ctx1")  # depth 1->2
        assert not runtime.enter_recursion("ctx1")  # depth 2->3 (exceeds limit)

    def test_exit_recursion(self):
        """Test exiting recursion."""
        runtime = LoopPreventionRuntime()

        runtime.enter_recursion("ctx1")
        runtime.enter_recursion("ctx1")

        pattern = runtime._recursion_stacks["ctx1"]
        assert pattern.recursion_depth == 2

        runtime.exit_recursion("ctx1", improvement=0.1)

        assert pattern.recursion_depth == 1
        assert len(pattern.last_improvements) == 1

    def test_reset_recursion_context(self):
        """Test resetting recursion context."""
        runtime = LoopPreventionRuntime()

        runtime.create_recursion_context("ctx1")
        pattern = runtime._recursion_stacks["ctx1"]

        pattern.step_counter = 5
        pattern.recursion_depth = 2

        runtime.reset_recursion_context("ctx1")

        assert pattern.step_counter == 0
        assert pattern.recursion_depth == 0

    def test_cleanup_context(self):
        """Test cleaning up context."""
        runtime = LoopPreventionRuntime()

        runtime.create_recursion_context("ctx1")
        assert "ctx1" in runtime._recursion_stacks

        runtime.cleanup_context("ctx1")

        assert "ctx1" not in runtime._recursion_stacks

    def test_get_context_status(self):
        """Test getting context status."""
        runtime = LoopPreventionRuntime()

        runtime.create_recursion_context("ctx1")
        runtime.enter_recursion("ctx1")

        status = runtime.get_context_status("ctx1")

        assert status is not None
        assert status["recursion_depth"] == 1
        assert "step_counter" in status
        assert "max_recursion_depth" in status

    def test_get_nonexistent_context_status(self):
        """Test getting status for nonexistent context."""
        runtime = LoopPreventionRuntime()

        status = runtime.get_context_status("nonexistent")

        assert status is None


class TestMetacognitionRuntimeIntegration:
    """Tests for main integration service."""

    def test_initialization(self):
        """Test integration initialization."""
        integration = MetacognitionRuntimeIntegration()

        assert integration is not None

    @pytest.mark.asyncio
    async def test_execute_metacognition_cycle(self):
        """Test full metacognition cycle."""
        integration = MetacognitionRuntimeIntegration()

        metrics = {
            "progress": 0.5,
            "confidence": 0.6,
            "surprise": 0.2,
            "basin_stability": 0.7,
            "free_energy": 1.0,
        }

        result = await integration.execute_metacognition_cycle("agent1", metrics)

        assert result["agent_id"] == "agent1"
        assert "assessment" in result
        assert "control_actions" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_execute_metacognition_with_control(self):
        """Test metacognition cycle with control actions."""
        integration = MetacognitionRuntimeIntegration()

        # High surprise should trigger control
        metrics = {
            "progress": 0.5,
            "confidence": 0.6,
            "surprise": 0.8,  # High
            "basin_stability": 0.7,
            "free_energy": 1.0,
        }

        # Run multiple times to trigger assessment
        for _ in range(3):
            result = await integration.execute_metacognition_cycle("agent1", metrics)

        # Should eventually generate control actions
        assert isinstance(result, dict)

    def test_get_patterns_summary(self):
        """Test getting patterns summary."""
        integration = MetacognitionRuntimeIntegration()

        summary = integration.get_patterns_summary()

        assert "patterns" in summary
        assert "stats" in summary
        assert "timestamp" in summary

    def test_cleanup_storage(self):
        """Test storage cleanup."""
        integration = MetacognitionRuntimeIntegration()

        result = integration.cleanup_storage()

        assert "expired_patterns" in result
        assert "remaining_stats" in result


class TestSingleton:
    """Tests for singleton integration instance."""

    def test_singleton_instance(self):
        """Test that singleton returns same instance."""
        integration1 = get_metacognition_runtime_integration()
        integration2 = get_metacognition_runtime_integration()

        assert integration1 is integration2

    def test_singleton_access_components(self):
        """Test accessing components through singleton."""
        integration = get_metacognition_runtime_integration()

        assert integration._monitor is not None
        assert integration._controller is not None
        assert integration._thoughtseed_comp is not None
        assert integration._loop_prevention is not None


@pytest.mark.asyncio
async def test_full_integration_flow():
    """Test full integration flow with all components."""
    integration = get_metacognition_runtime_integration()

    # Simulate agent execution with metrics
    agent_id = "test_agent"
    metrics = {
        "progress": 0.5,
        "confidence": 0.6,
        "surprise": 0.3,
        "basin_stability": 0.7,
        "free_energy": 2.0,
    }

    # Execute metacognition cycle multiple times
    for i in range(10):
        result = await integration.execute_metacognition_cycle(agent_id, metrics)
        assert "agent_id" in result

    # Get summary
    summary = integration.get_patterns_summary()
    assert summary is not None

    # Cleanup
    cleanup_result = integration.cleanup_storage()
    assert cleanup_result is not None
