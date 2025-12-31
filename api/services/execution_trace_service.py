"""
Execution Trace Persistence Service (Feature 039, T012)

TERMINOLOGY: "ExecutionTrace" = agent step logs (operational audit trail)
NOT state-space trajectories. See docs/TERMINOLOGY.md for disambiguation.

This service persists smolagents execution history to Neo4j for:
- Debugging and replay
- Performance analysis
- Learning from past runs
- Linking to activated attractor basins
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


class ExecutionStepData(BaseModel):
    """Data for a single execution step."""

    step_number: int = Field(..., description="Step number in sequence")
    step_type: str = Field(..., description="ActionStep or PlanningStep")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tool_name: Optional[str] = Field(None, description="Tool called (if ActionStep)")
    tool_arguments: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool arguments"
    )
    observation_summary: Optional[str] = Field(
        None, description="Truncated observation (100 chars)"
    )
    plan: Optional[str] = Field(None, description="Plan content (if PlanningStep)")
    error: Optional[str] = Field(None, description="Error message if step failed")


class ExecutionTraceData(BaseModel):
    """Full execution trace with steps."""

    id: str = Field(..., description="Trace UUID")
    agent_name: str = Field(..., description="Agent that ran")
    run_id: str = Field(..., description="Run identifier for grouping")
    started_at: str = Field(...)
    completed_at: Optional[str] = Field(None)
    step_count: int = Field(default=0)
    planning_count: int = Field(default=0)
    success: Optional[bool] = Field(None)
    error_message: Optional[str] = Field(None)
    token_usage: Optional[Dict[str, Any]] = Field(None)
    steps: List[ExecutionStepData] = Field(default_factory=list)
    activated_basins: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# In-Memory Buffer (for batching before Neo4j write)
# =============================================================================


@dataclass
class TraceBuffer:
    """In-memory buffer for building trace before persistence."""

    trace_id: str
    agent_name: str
    run_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    basin_links: List[Dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    success: Optional[bool] = None
    error_message: Optional[str] = None


# =============================================================================
# Execution Trace Service
# =============================================================================


class ExecutionTraceService:
    """
    Service for persisting agent execution traces to Neo4j.

    Feature 039, T012: Implements execution trace CRUD operations.

    Usage:
        service = get_execution_trace_service()
        trace_id = await service.create_trace("heartbeat_agent", "run-123")
        step_id = await service.add_step(trace_id, step_data)
        await service.link_basin(trace_id, "basin-456", 0.8, at_step=2)
        await service.complete_trace(trace_id, success=True)
        trace = await service.get_trace(trace_id)
    """

    def __init__(self):
        self._buffers: Dict[str, TraceBuffer] = {}

    async def create_trace(self, agent_name: str, run_id: str) -> str:
        """
        Create a new execution trace and return its ID.

        Args:
            agent_name: Name of the agent (e.g., "heartbeat_agent", "perception")
            run_id: Unique identifier for this run

        Returns:
            trace_id: UUID for the new trace
        """
        trace_id = str(uuid.uuid4())

        # Store in memory buffer (persisted on complete_trace)
        self._buffers[trace_id] = TraceBuffer(
            trace_id=trace_id,
            agent_name=agent_name,
            run_id=run_id,
        )

        logger.debug(f"Created execution trace {trace_id} for {agent_name}")
        return trace_id

    async def add_step(self, trace_id: str, step_data: Dict[str, Any]) -> str:
        """
        Add a step to an execution trace.

        Args:
            trace_id: The trace to add to
            step_data: Step information (step_number, step_type, tool_name, etc.)

        Returns:
            step_id: UUID for the new step
        """
        buffer = self._buffers.get(trace_id)
        if not buffer:
            raise ValueError(f"Unknown trace_id: {trace_id}")

        step_id = str(uuid.uuid4())
        step_record = {
            "id": step_id,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            **step_data,
        }

        # Truncate observation if present
        if "observation" in step_record and step_record["observation"]:
            obs = str(step_record["observation"])
            step_record["observation_summary"] = obs[:100] + "..." if len(obs) > 100 else obs
            del step_record["observation"]

        buffer.steps.append(step_record)
        logger.debug(f"Added step {step_id} to trace {trace_id}")
        return step_id

    async def link_basin(
        self,
        trace_id: str,
        basin_id: str,
        strength: float,
        at_step: Optional[int] = None,
    ) -> None:
        """
        Link an activated basin to the trace.

        Args:
            trace_id: The trace that activated the basin
            basin_id: MemoryCluster ID
            strength: Activation strength (0-1)
            at_step: Step number when activation occurred
        """
        buffer = self._buffers.get(trace_id)
        if not buffer:
            raise ValueError(f"Unknown trace_id: {trace_id}")

        buffer.basin_links.append(
            {
                "basin_id": basin_id,
                "strength": strength,
                "at_step": at_step or len(buffer.steps),
            }
        )
        logger.debug(f"Linked basin {basin_id} to trace {trace_id}")

    async def complete_trace(
        self,
        trace_id: str,
        success: bool,
        error_message: Optional[str] = None,
        token_usage: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark trace as complete and persist to Neo4j.

        Args:
            trace_id: The trace to complete
            success: Whether the run succeeded
            error_message: Error details if failed
            token_usage: Token statistics (pre/post prune, reduction %)

        Returns:
            True if persistence succeeded
        """
        buffer = self._buffers.get(trace_id)
        if not buffer:
            raise ValueError(f"Unknown trace_id: {trace_id}")

        buffer.completed = True
        buffer.success = success
        buffer.error_message = error_message

        # Persist to Neo4j
        persisted = await self._persist_trace(buffer, token_usage)

        # Clean up buffer
        if persisted:
            del self._buffers[trace_id]

        return persisted

    async def _persist_trace(
        self, buffer: TraceBuffer, token_usage: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Persist trace and steps to Neo4j."""
        try:
            from api.services.remote_sync import get_neo4j_driver

            driver = get_neo4j_driver()

            # Count step types
            action_count = sum(
                1 for s in buffer.steps if s.get("step_type") == "ActionStep"
            )
            planning_count = sum(
                1 for s in buffer.steps if s.get("step_type") == "PlanningStep"
            )

            # Create trace node
            trace_cypher = """
            CREATE (t:AgentExecutionTrace {
                id: $id,
                agent_name: $agent_name,
                run_id: $run_id,
                started_at: datetime($started_at),
                completed_at: datetime($completed_at),
                step_count: $step_count,
                planning_count: $planning_count,
                success: $success,
                error_message: $error_message,
                token_usage: $token_usage
            })
            RETURN t.id as trace_id
            """

            await driver.execute_query(
                trace_cypher,
                {
                    "id": buffer.trace_id,
                    "agent_name": buffer.agent_name,
                    "run_id": buffer.run_id,
                    "started_at": buffer.started_at.isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "step_count": len(buffer.steps),
                    "planning_count": planning_count,
                    "success": buffer.success,
                    "error_message": buffer.error_message,
                    "token_usage": str(token_usage) if token_usage else None,
                },
            )

            # Create step nodes and link to trace
            for idx, step in enumerate(buffer.steps):
                step_cypher = """
                MATCH (t:AgentExecutionTrace {id: $trace_id})
                CREATE (s:AgentExecutionStep {
                    id: $step_id,
                    trace_id: $trace_id,
                    step_number: $step_number,
                    step_type: $step_type,
                    timestamp: datetime($timestamp),
                    tool_name: $tool_name,
                    tool_arguments: $tool_arguments,
                    observation_summary: $observation_summary,
                    plan: $plan,
                    error: $error
                })
                CREATE (t)-[:HAS_STEP {order: $order}]->(s)
                """

                await driver.execute_query(
                    step_cypher,
                    {
                        "trace_id": buffer.trace_id,
                        "step_id": step.get("id"),
                        "step_number": step.get("step_number", idx),
                        "step_type": step.get("step_type", "Unknown"),
                        "timestamp": step.get("timestamp", datetime.utcnow().isoformat()),
                        "tool_name": step.get("tool_name"),
                        "tool_arguments": str(step.get("tool_arguments"))
                        if step.get("tool_arguments")
                        else None,
                        "observation_summary": step.get("observation_summary"),
                        "plan": step.get("plan"),
                        "error": step.get("error"),
                        "order": idx + 1,
                    },
                )

            # Link activated basins
            for link in buffer.basin_links:
                basin_cypher = """
                MATCH (t:AgentExecutionTrace {id: $trace_id})
                MATCH (b:MemoryCluster {id: $basin_id})
                MERGE (t)-[r:ACTIVATED_BASIN]->(b)
                SET r.strength = $strength, r.at_step = $at_step
                """

                await driver.execute_query(
                    basin_cypher,
                    {
                        "trace_id": buffer.trace_id,
                        "basin_id": link["basin_id"],
                        "strength": link["strength"],
                        "at_step": link["at_step"],
                    },
                )

            logger.info(
                f"Persisted execution trace {buffer.trace_id}: "
                f"{len(buffer.steps)} steps, {len(buffer.basin_links)} basins"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to persist execution trace: {e}")
            return False

    async def get_trace(self, trace_id: str) -> Optional[ExecutionTraceData]:
        """
        Retrieve a full execution trace from Neo4j.

        Args:
            trace_id: The trace to retrieve

        Returns:
            ExecutionTraceData with steps and basin links, or None
        """
        try:
            from api.services.remote_sync import get_neo4j_driver

            driver = get_neo4j_driver()

            # Get trace with steps
            trace_cypher = """
            MATCH (t:AgentExecutionTrace {id: $trace_id})
            OPTIONAL MATCH (t)-[hs:HAS_STEP]->(s:AgentExecutionStep)
            OPTIONAL MATCH (t)-[ab:ACTIVATED_BASIN]->(b:MemoryCluster)
            WITH t,
                 collect(DISTINCT {
                     step_number: s.step_number,
                     step_type: s.step_type,
                     timestamp: toString(s.timestamp),
                     tool_name: s.tool_name,
                     tool_arguments: s.tool_arguments,
                     observation_summary: s.observation_summary,
                     plan: s.plan,
                     error: s.error,
                     order: hs.order
                 }) as steps,
                 collect(DISTINCT {
                     basin_id: b.id,
                     basin_name: b.name,
                     strength: ab.strength,
                     at_step: ab.at_step
                 }) as basins
            RETURN t {
                .id, .agent_name, .run_id,
                started_at: toString(t.started_at),
                completed_at: toString(t.completed_at),
                .step_count, .planning_count, .success, .error_message, .token_usage
            } as trace, steps, basins
            """

            result = await driver.execute_query(trace_cypher, {"trace_id": trace_id})

            if not result:
                return None

            row = result[0]
            trace_data = row.get("trace", {})

            # Filter out empty steps (from OPTIONAL MATCH)
            steps = [
                s for s in row.get("steps", []) if s.get("step_number") is not None
            ]
            # Sort by order
            steps.sort(key=lambda x: x.get("order", 0))

            # Filter out empty basins
            basins = [
                b for b in row.get("basins", []) if b.get("basin_id") is not None
            ]

            return ExecutionTraceData(
                id=trace_data.get("id", trace_id),
                agent_name=trace_data.get("agent_name", "unknown"),
                run_id=trace_data.get("run_id", "unknown"),
                started_at=trace_data.get("started_at", ""),
                completed_at=trace_data.get("completed_at"),
                step_count=trace_data.get("step_count", 0),
                planning_count=trace_data.get("planning_count", 0),
                success=trace_data.get("success"),
                error_message=trace_data.get("error_message"),
                token_usage=trace_data.get("token_usage"),
                steps=[
                    ExecutionStepData(
                        step_number=s.get("step_number", 0),
                        step_type=s.get("step_type", "Unknown"),
                        timestamp=s.get("timestamp", ""),
                        tool_name=s.get("tool_name"),
                        tool_arguments=s.get("tool_arguments"),
                        observation_summary=s.get("observation_summary"),
                        plan=s.get("plan"),
                        error=s.get("error"),
                    )
                    for s in steps
                ],
                activated_basins=basins,
            )

        except Exception as e:
            logger.error(f"Failed to retrieve execution trace {trace_id}: {e}")
            return None

    async def list_traces(
        self,
        agent_name: Optional[str] = None,
        limit: int = 20,
        success_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List recent execution traces.

        Args:
            agent_name: Filter by agent name
            limit: Maximum traces to return
            success_only: Only return successful traces

        Returns:
            List of trace summaries
        """
        try:
            from api.services.remote_sync import get_neo4j_driver

            driver = get_neo4j_driver()

            # Build query with optional filters
            where_clauses = []
            params = {"limit": limit}

            if agent_name:
                where_clauses.append("t.agent_name = $agent_name")
                params["agent_name"] = agent_name

            if success_only:
                where_clauses.append("t.success = true")

            where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            cypher = f"""
            MATCH (t:AgentExecutionTrace)
            {where_clause}
            RETURN t {{
                .id, .agent_name, .run_id,
                started_at: toString(t.started_at),
                completed_at: toString(t.completed_at),
                .step_count, .planning_count, .success
            }} as trace
            ORDER BY t.started_at DESC
            LIMIT $limit
            """

            result = await driver.execute_query(cypher, params)
            return [row.get("trace", {}) for row in result]

        except Exception as e:
            logger.error(f"Failed to list execution traces: {e}")
            return []


# =============================================================================
# Factory
# =============================================================================

_service: Optional[ExecutionTraceService] = None


def get_execution_trace_service() -> ExecutionTraceService:
    """Get or create the global execution trace service."""
    global _service
    if _service is None:
        _service = ExecutionTraceService()
    return _service


__all__ = [
    "ExecutionTraceService",
    "ExecutionStepData",
    "ExecutionTraceData",
    "get_execution_trace_service",
]
