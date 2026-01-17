"""
Integration Tests for Smolagents V2 Alignment
Feature: 039-smolagents-v2-alignment
Task: T015

Tests for:
- Planning interval behavior
- IWMT coherence callback on PlanningStep
- Basin activation on semantic_recall
- Execution trace persistence
- Memory pruning token reduction

Note: smolagents 1.23+ removed ManagedAgent class. This project uses custom
ManagedAgent wrappers in api/agents/managed/ (ManagedPerceptionAgent, etc.)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from smolagents.memory import ActionStep, PlanningStep

# Check if custom ManagedAgent wrappers are available
try:
    from api.agents.managed import (
        ManagedPerceptionAgent,
        ManagedReasoningAgent,
        ManagedMetacognitionAgent,
    )
    HAS_MANAGED_AGENT = True
except ImportError:
    HAS_MANAGED_AGENT = False

# Marker for tests requiring ManagedAgent wrappers
requires_managed_agent = pytest.mark.skipif(
    not HAS_MANAGED_AGENT,
    reason="Custom ManagedAgent wrappers not available in api.agents.managed"
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_action_step():
    """Create a mock ActionStep for testing."""
    step = MagicMock(spec=ActionStep)
    step.step_number = 1
    step.tool_calls = [MagicMock(name="semantic_recall", arguments={"query": "test"})]
    step.observations = "Test observation " * 50  # ~850 chars
    step.observation = step.observations
    step.error = None
    return step


@pytest.fixture
def mock_planning_step():
    """Create a mock PlanningStep for testing."""
    step = MagicMock(spec=PlanningStep)
    step.step_number = 0
    step.plan = "1. Observe environment\n2. Recall memories\n3. Decide action"
    return step


@pytest.fixture
def mock_agent():
    """Create a mock agent with memory."""
    agent = MagicMock()
    agent.name = "test_agent"
    agent.memory = MagicMock()
    agent.memory.steps = []
    return agent


# =============================================================================
# Phase 1: Planning Interval Tests
# =============================================================================


@requires_managed_agent
class TestPlanningInterval:
    """Tests for planning_interval configuration."""

    def test_heartbeat_agent_has_planning_interval(self):
        """HeartbeatAgent should be configured with planning_interval=3."""
        from api.agents.heartbeat_agent import HeartbeatAgent

        with patch("api.services.llm_service.get_router_model") as mock_model, \
             patch("api.agents.heartbeat_agent.MCPClient") as mock_mcp:
            mock_model.return_value = MagicMock()
            # Mock MCP client to return fake tools
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.__enter__ = MagicMock(return_value=[])
            mock_mcp_instance.__exit__ = MagicMock(return_value=None)
            mock_mcp.return_value = mock_mcp_instance

            with HeartbeatAgent() as agent:
                # Check agent configuration
                inner_agent = agent.agent
                assert hasattr(inner_agent, "planning_interval")
                assert inner_agent.planning_interval == 3

    def test_ooda_agents_have_planning_interval(self):
        """OODA agents should have planning_interval=2."""
        from api.agents.perception_agent import PerceptionAgent
        from api.agents.reasoning_agent import ReasoningAgent
        from api.agents.metacognition_agent import MetacognitionAgent

        # Helper to create mock MCP client
        def create_mock_mcp():
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.__enter__ = MagicMock(return_value=[])
            mock_mcp_instance.__exit__ = MagicMock(return_value=None)
            return mock_mcp_instance

        with patch("api.services.llm_service.get_router_model") as mock_model, \
             patch("api.agents.perception_agent.MCPClient") as mock_mcp:
            mock_model.return_value = MagicMock()
            mock_mcp.return_value = create_mock_mcp()

            with PerceptionAgent() as agent:
                assert agent.agent.planning_interval == 2

        with patch("api.services.llm_service.get_router_model") as mock_model, \
             patch("api.agents.reasoning_agent.MCPClient") as mock_mcp:
            mock_model.return_value = MagicMock()
            mock_mcp.return_value = create_mock_mcp()

            with ReasoningAgent() as agent:
                assert agent.agent.planning_interval == 2

        with patch("api.services.llm_service.get_router_model") as mock_model, \
             patch("api.agents.metacognition_agent.MCPClient") as mock_mcp:
            mock_model.return_value = MagicMock()
            mock_mcp.return_value = create_mock_mcp()

            with MetacognitionAgent() as agent:
                assert agent.agent.planning_interval == 2


# =============================================================================
# Phase 2: Callback Registry Tests
# =============================================================================


@requires_managed_agent
class TestCallbackRegistry:
    """Tests for DionysusCognitiveCallbackRegistry."""

    def test_registry_initialization(self):
        """Registry should initialize with empty callback lists."""
        from api.agents.audit import DionysusCognitiveCallbackRegistry

        registry = DionysusCognitiveCallbackRegistry()
        assert ActionStep in registry._callbacks
        assert PlanningStep in registry._callbacks
        assert len(registry._callbacks[ActionStep]) == 0
        assert len(registry._callbacks[PlanningStep]) == 0

    def test_register_callback(self):
        """Callbacks can be registered for step types."""
        from api.agents.audit import DionysusCognitiveCallbackRegistry

        registry = DionysusCognitiveCallbackRegistry()

        def test_callback(step, agent):
            pass

        registry.register(ActionStep, test_callback)
        assert test_callback in registry._callbacks[ActionStep]

    def test_get_step_callbacks_returns_dispatchers(self):
        """get_step_callbacks returns dispatcher functions."""
        from api.agents.audit import DionysusCognitiveCallbackRegistry

        registry = DionysusCognitiveCallbackRegistry()

        call_count = {"value": 0}

        def test_callback(step, agent):
            call_count["value"] += 1

        registry.register(ActionStep, test_callback)
        callbacks = registry.get_step_callbacks("test_agent")

        # Should have ActionStep dispatcher
        assert ActionStep in callbacks

        # Call the dispatcher
        mock_step = MagicMock()
        callbacks[ActionStep](mock_step, None)

        assert call_count["value"] == 1

    def test_callback_error_isolation(self):
        """Callback errors should not propagate."""
        from api.agents.audit import DionysusCognitiveCallbackRegistry

        registry = DionysusCognitiveCallbackRegistry()

        def failing_callback(step, agent):
            raise ValueError("Test error")

        def succeeding_callback(step, agent):
            step.marked = True

        registry.register(ActionStep, failing_callback)
        registry.register(ActionStep, succeeding_callback)

        callbacks = registry.get_step_callbacks("test_agent")

        mock_step = MagicMock()
        # Should not raise
        callbacks[ActionStep](mock_step, None)

        # Second callback should still run
        assert mock_step.marked is True


# =============================================================================
# Phase 3: Memory Pruning Tests
# =============================================================================


@requires_managed_agent
class TestMemoryPruning:
    """Tests for memory pruning callback."""

    def test_memory_callback_prunes_old_observations(self, mock_action_step, mock_agent):
        """Memory callback should prune observations older than window."""
        from api.agents.callbacks.memory_callback import memory_pruning_callback

        # Create old step with long observation
        old_step = MagicMock(spec=ActionStep)
        old_step.step_number = 1
        old_step.observations = "Old observation content " * 100  # Long

        # Current step is step 5 (window is 3, so step 1 should be pruned)
        mock_action_step.step_number = 5
        mock_agent.memory.steps = [old_step]

        with patch.dict("os.environ", {"AGENT_MEMORY_WINDOW": "3"}):
            memory_pruning_callback(mock_action_step, mock_agent)

        # Old step should be pruned (format: "[STEP X PRUNED]")
        assert "PRUNED" in old_step.observations

    def test_token_tracker_records_reduction(self, mock_action_step):
        """TokenUsageTracker should record pre/post pruning tokens."""
        from api.agents.audit import TokenUsageTracker

        tracker = TokenUsageTracker("test_agent")

        # Record before pruning (850 chars ≈ 212 tokens)
        tracker.record_pre_prune(mock_action_step)

        # Simulate pruning
        mock_action_step.observations = "[PRUNED] Test observation..."

        # Record after pruning
        tracker.record_post_prune(mock_action_step)

        summary = tracker.get_summary()
        assert summary["tokens_saved"] > 0
        assert summary["reduction_percentage"] > 0


# =============================================================================
# Phase 4: ManagedAgent Tests
# =============================================================================


@requires_managed_agent
class TestManagedAgents:
    """Tests for ManagedAgent wrappers."""

    def test_managed_perception_agent_wrapper(self):
        """ManagedPerceptionAgent should wrap PerceptionAgent."""
        from api.agents.managed import ManagedPerceptionAgent

        # Helper to create mock MCP client
        def create_mock_mcp():
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.__enter__ = MagicMock(return_value=[])
            mock_mcp_instance.__exit__ = MagicMock(return_value=None)
            return mock_mcp_instance

        with patch("api.services.llm_service.get_router_model") as mock_model, \
             patch("api.agents.perception_agent.MCPClient") as mock_mcp:
            mock_model.return_value = MagicMock()
            mock_mcp.return_value = create_mock_mcp()

            wrapper = ManagedPerceptionAgent()
            with wrapper:
                managed = wrapper.get_managed()

                assert managed.name == "perception"
                # Description should mention observation/memory/environmental
                assert "observation" in managed.description.lower() or "environmental" in managed.description.lower()

    def test_managed_reasoning_agent_wrapper(self):
        """ManagedReasoningAgent should wrap ReasoningAgent."""
        from api.agents.managed import ManagedReasoningAgent

        def create_mock_mcp():
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.__enter__ = MagicMock(return_value=[])
            mock_mcp_instance.__exit__ = MagicMock(return_value=None)
            return mock_mcp_instance

        with patch("api.services.llm_service.get_router_model") as mock_model, \
             patch("api.agents.reasoning_agent.MCPClient") as mock_mcp:
            mock_model.return_value = MagicMock()
            mock_mcp.return_value = create_mock_mcp()

            wrapper = ManagedReasoningAgent()
            with wrapper:
                managed = wrapper.get_managed()

                assert managed.name == "reasoning"
                # Description should mention analysis/reflection/synthesis
                assert "analysis" in managed.description.lower() or "reflection" in managed.description.lower()

    def test_managed_metacognition_agent_wrapper(self):
        """ManagedMetacognitionAgent should wrap MetacognitionAgent."""
        from api.agents.managed import ManagedMetacognitionAgent

        def create_mock_mcp():
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.__enter__ = MagicMock(return_value=[])
            mock_mcp_instance.__exit__ = MagicMock(return_value=None)
            return mock_mcp_instance

        with patch("api.services.llm_service.get_router_model") as mock_model, \
             patch("api.agents.metacognition_agent.MCPClient") as mock_mcp:
            mock_model.return_value = MagicMock()
            mock_mcp.return_value = create_mock_mcp()

            wrapper = ManagedMetacognitionAgent()
            with wrapper:
                managed = wrapper.get_managed()

                assert managed.name == "metacognition"
                # Description should mention self-reflection/goal/mental model
                assert "self-reflection" in managed.description.lower() or "goal" in managed.description.lower()


# =============================================================================
# Phase 5: Execution Trace Persistence Tests
# =============================================================================


class TestExecutionTracePersistence:
    """Tests for execution trace persistence."""

    @pytest.mark.asyncio
    async def test_create_trace(self):
        """ExecutionTraceService should create trace with UUID."""
        from api.services.execution_trace_service import get_execution_trace_service

        service = get_execution_trace_service()
        trace_id = await service.create_trace("test_agent", "run-123")

        assert trace_id is not None
        assert len(trace_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_add_step_to_trace(self):
        """Steps can be added to a trace."""
        from api.services.execution_trace_service import get_execution_trace_service

        service = get_execution_trace_service()
        trace_id = await service.create_trace("test_agent", "run-456")

        step_id = await service.add_step(trace_id, {
            "step_number": 1,
            "step_type": "ActionStep",
            "tool_name": "semantic_recall",
            "observation": "Test result",
        })

        assert step_id is not None
        assert len(step_id) == 36

    @pytest.mark.asyncio
    async def test_link_basin_to_trace(self):
        """Basins can be linked to traces."""
        from api.services.execution_trace_service import get_execution_trace_service

        service = get_execution_trace_service()
        trace_id = await service.create_trace("test_agent", "run-789")

        # Should not raise
        await service.link_basin(trace_id, "basin-abc", 0.8, at_step=2)

        # Verify buffer has the link
        assert len(service._buffers[trace_id].basin_links) == 1

    @requires_managed_agent
    @pytest.mark.asyncio
    async def test_execution_trace_collector(self, mock_action_step, mock_planning_step):
        """ExecutionTraceCollector collects steps during run."""
        from api.agents.callbacks.execution_trace_callback import ExecutionTraceCollector

        collector = ExecutionTraceCollector("test_agent", "run-collect")

        # Simulate step callbacks
        collector.on_planning_step(mock_planning_step, None)
        collector.on_action_step(mock_action_step, None)

        assert len(collector._steps_collected) == 2
        assert collector._steps_collected[0]["step_type"] == "PlanningStep"
        assert collector._steps_collected[1]["step_type"] == "ActionStep"


# =============================================================================
# Integration: Full Flow Test
# =============================================================================


@requires_managed_agent
class TestFullFlow:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_callback_to_trace_flow(self, mock_action_step, mock_planning_step):
        """Full flow from callbacks to trace persistence."""
        from api.agents.callbacks.execution_trace_callback import (
            ExecutionTraceCollector,
            register_collector,
            get_active_collector,
            unregister_collector,
        )
        from api.services.execution_trace_service import get_execution_trace_service

        # Create and register collector
        collector = ExecutionTraceCollector("integration_test", "run-full")
        register_collector("integration_test", collector)

        # Verify registration
        assert get_active_collector("integration_test") is collector

        # Simulate agent run with steps
        collector.on_planning_step(mock_planning_step, None)
        collector.on_action_step(mock_action_step, None)
        collector.record_basin_activation("basin-123", 0.75, at_step=1)

        # Mock Neo4j to avoid actual persistence
        with patch("api.services.remote_sync.get_neo4j_driver"):
            with patch.object(
                get_execution_trace_service(),
                "_persist_trace",
                new_callable=AsyncMock,
                return_value=True
            ):
                trace_id = await collector.finalize(success=True, token_usage={"saved": 100})

        # Cleanup
        unregister_collector("integration_test")
        assert get_active_collector("integration_test") is None

    def test_token_usage_aggregate_stats(self):
        """Aggregate token stats across multiple agents."""
        from api.agents.audit import (
            get_token_tracker,
            get_aggregate_token_stats,
            TokenUsageTracker,
        )

        # Create trackers for multiple agents
        tracker1 = get_token_tracker("agent1")
        tracker2 = get_token_tracker("agent2")

        # Simulate usage
        tracker1.stats.pre_pruning_tokens = 1000
        tracker1.stats.post_pruning_tokens = 700
        tracker1.stats.steps_tracked = 5

        tracker2.stats.pre_pruning_tokens = 500
        tracker2.stats.post_pruning_tokens = 400
        tracker2.stats.steps_tracked = 3

        # Check aggregate
        aggregate = get_aggregate_token_stats()

        assert aggregate["total_agents"] >= 2
        assert aggregate["total_pre_pruning_tokens"] >= 1500
        assert aggregate["total_tokens_saved"] >= 400


# =============================================================================
# API Endpoint Tests
# =============================================================================


@requires_managed_agent
class TestAgentsRouter:
    """Tests for /api/agents endpoints."""

    @pytest.mark.asyncio
    async def test_list_traces_endpoint(self):
        """GET /api/agents/traces should return trace list."""
        from fastapi.testclient import TestClient
        from api.routers.agents import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch("api.routers.agents.get_execution_trace_service") as mock_service:
            mock_service.return_value.list_traces = AsyncMock(return_value=[
                {
                    "id": "trace-1",
                    "agent_name": "test",
                    "run_id": "run-1",
                    "started_at": "2025-01-01T00:00:00",
                    "step_count": 5,
                    "planning_count": 2,
                    "success": True,
                }
            ])

            response = client.get("/api/agents/traces")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert data["traces"][0]["agent_name"] == "test"

    @pytest.mark.asyncio
    async def test_token_usage_endpoint(self):
        """GET /api/agents/token-usage should return stats."""
        from fastapi.testclient import TestClient
        from api.routers.agents import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/api/agents/token-usage")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "aggregate" in data
