"""
Execution Trace Persistence Callback (Feature 039, T013)

TERMINOLOGY: "ExecutionTrace" = agent step logs (operational audit trail)
NOT state-space trajectories. See docs/TERMINOLOGY.md for disambiguation.

This callback persists the full execution trace to Neo4j after agent.run() completes.
It extracts steps from agent.memory, links activated basins, and saves token metrics.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import uuid

from smolagents.memory import ActionStep, PlanningStep

if TYPE_CHECKING:
    from smolagents.agents import Agent

logger = logging.getLogger(__name__)


# =============================================================================
# In-Flight Trace Collector
# =============================================================================


class ExecutionTraceCollector:
    """
    Collects execution steps during an agent run.

    This collector is registered as a step callback and accumulates
    step data in memory. On completion, it persists the full trace
    to Neo4j via ExecutionTraceService.

    Usage:
        collector = ExecutionTraceCollector("heartbeat_agent", "run-123")
        agent = ToolCallingAgent(
            ...,
            step_callbacks={
                ActionStep: collector.on_action_step,
                PlanningStep: collector.on_planning_step,
            }
        )
        result = agent.run(task)
        await collector.finalize(success=True, token_usage={...})
    """

    def __init__(self, agent_name: str, run_id: Optional[str] = None):
        self.agent_name = agent_name
        self.run_id = run_id or str(uuid.uuid4())
        self.trace_id: Optional[str] = None
        self._service_initialized = False
        self._steps_collected: List[Dict[str, Any]] = []
        self._basin_links: List[Dict[str, Any]] = []
        self._finalized = False

    async def _ensure_trace(self) -> str:
        """Lazily create the trace on first step."""
        if self.trace_id is None:
            from api.services.execution_trace_service import get_execution_trace_service
            service = get_execution_trace_service()
            self.trace_id = await service.create_trace(self.agent_name, self.run_id)
            self._service_initialized = True
        return self.trace_id

    def on_action_step(self, step: ActionStep, agent: Optional[Any] = None) -> None:
        """
        Callback for ActionStep - collects tool execution data.

        This is a sync callback (smolagents requirement) that queues
        step data for async persistence later.
        """
        try:
            step_data = {
                "step_number": getattr(step, "step_number", len(self._steps_collected)),
                "step_type": "ActionStep",
                "tool_name": None,
                "tool_arguments": None,
                "observation": None,
                "error": str(step.error) if getattr(step, "error", None) else None,
            }

            # Extract tool call info
            if hasattr(step, "tool_calls") and step.tool_calls:
                # Take the first tool call (most common case)
                tc = step.tool_calls[0]
                step_data["tool_name"] = tc.name
                step_data["tool_arguments"] = tc.arguments

            # Extract observation (truncate for storage)
            obs = getattr(step, "observations", None) or getattr(step, "observation", "")
            if obs:
                step_data["observation"] = str(obs)[:500]

            self._steps_collected.append(step_data)
            logger.debug(f"Collected ActionStep {step_data['step_number']} for {self.agent_name}")

        except Exception as e:
            logger.warning(f"Failed to collect ActionStep: {e}")

    def on_planning_step(self, step: PlanningStep, agent: Optional[Any] = None) -> None:
        """
        Callback for PlanningStep - collects planning phase data.
        """
        try:
            step_data = {
                "step_number": getattr(step, "step_number", len(self._steps_collected)),
                "step_type": "PlanningStep",
                "plan": str(getattr(step, "plan", ""))[:1000],
                "tool_name": None,
                "tool_arguments": None,
                "observation": None,
                "error": None,
            }

            self._steps_collected.append(step_data)
            logger.debug(f"Collected PlanningStep {step_data['step_number']} for {self.agent_name}")

        except Exception as e:
            logger.warning(f"Failed to collect PlanningStep: {e}")

    def record_basin_activation(
        self,
        basin_id: str,
        strength: float,
        at_step: Optional[int] = None,
    ) -> None:
        """
        Record a basin activation for later persistence.

        Called from basin_callback when semantic_recall activates basins.
        """
        self._basin_links.append({
            "basin_id": basin_id,
            "strength": strength,
            "at_step": at_step or len(self._steps_collected),
        })

    async def finalize(
        self,
        success: bool,
        error_message: Optional[str] = None,
        token_usage: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Persist the collected trace to Neo4j.

        Args:
            success: Whether the agent run succeeded
            error_message: Error details if failed
            token_usage: Token statistics from TokenUsageTracker

        Returns:
            trace_id if persisted successfully, None otherwise
        """
        if self._finalized:
            logger.warning(f"Trace {self.trace_id} already finalized")
            return self.trace_id

        self._finalized = True

        # Skip if no steps were collected
        if not self._steps_collected:
            logger.debug(f"No steps collected for {self.agent_name}, skipping persistence")
            return None

        try:
            from api.services.execution_trace_service import get_execution_trace_service
            service = get_execution_trace_service()

            # Create trace
            trace_id = await self._ensure_trace()

            # Add all collected steps
            for step_data in self._steps_collected:
                await service.add_step(trace_id, step_data)

            # Link activated basins
            for link in self._basin_links:
                await service.link_basin(
                    trace_id,
                    link["basin_id"],
                    link["strength"],
                    link["at_step"],
                )

            # Complete and persist
            persisted = await service.complete_trace(
                trace_id,
                success=success,
                error_message=error_message,
                token_usage=token_usage,
            )

            if persisted:
                logger.info(
                    f"Finalized execution trace {trace_id}: "
                    f"{len(self._steps_collected)} steps, {len(self._basin_links)} basins"
                )
                return trace_id
            else:
                logger.warning(f"Failed to persist trace {trace_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to finalize execution trace: {e}")
            return None

    def get_step_callbacks(self) -> Dict[type, Callable]:
        """
        Return step_callbacks dict for agent initialization.

        Returns:
            Dict mapping step types to callback functions
        """
        return {
            ActionStep: self.on_action_step,
            PlanningStep: self.on_planning_step,
        }


# =============================================================================
# Convenience Factory
# =============================================================================


def create_trace_collector(
    agent_name: str,
    run_id: Optional[str] = None,
) -> ExecutionTraceCollector:
    """
    Create a new trace collector for an agent run.

    Usage:
        collector = create_trace_collector("heartbeat_agent")

        agent = ToolCallingAgent(
            ...,
            step_callbacks=collector.get_step_callbacks()
        )

        result = agent.run(task)

        # After run completes
        await collector.finalize(success=True)
    """
    return ExecutionTraceCollector(agent_name, run_id)


# =============================================================================
# Global Active Collectors (for basin callback integration)
# =============================================================================

_active_collectors: Dict[str, ExecutionTraceCollector] = {}


def register_collector(agent_name: str, collector: ExecutionTraceCollector) -> None:
    """Register a collector for basin callback integration."""
    _active_collectors[agent_name] = collector


def get_active_collector(agent_name: str) -> Optional[ExecutionTraceCollector]:
    """Get the active collector for an agent."""
    return _active_collectors.get(agent_name)


def unregister_collector(agent_name: str) -> None:
    """Unregister a collector after run completion."""
    _active_collectors.pop(agent_name, None)


__all__ = [
    "ExecutionTraceCollector",
    "create_trace_collector",
    "register_collector",
    "get_active_collector",
    "unregister_collector",
]
