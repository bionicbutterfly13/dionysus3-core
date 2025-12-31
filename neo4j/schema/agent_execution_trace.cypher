// Agent Execution Trace Schema (Feature 039, T011)
//
// TERMINOLOGY: "ExecutionTrace" = agent step logs (operational audit trail)
// NOT state-space trajectories. See docs/TERMINOLOGY.md for disambiguation.
//
// This schema persists smolagents execution history for:
// - Debugging and replay
// - Performance analysis
// - Learning from past runs
// - Linking to activated attractor basins

// =============================================================================
// Constraints
// =============================================================================

// Unique constraint on execution trace ID
CREATE CONSTRAINT agent_execution_trace_id IF NOT EXISTS
FOR (t:AgentExecutionTrace) REQUIRE t.id IS UNIQUE;

// Unique constraint on execution step ID
CREATE CONSTRAINT agent_execution_step_id IF NOT EXISTS
FOR (s:AgentExecutionStep) REQUIRE s.id IS UNIQUE;

// =============================================================================
// Indexes
// =============================================================================

// Index for querying traces by agent name
CREATE INDEX agent_execution_trace_agent IF NOT EXISTS
FOR (t:AgentExecutionTrace) ON (t.agent_name);

// Index for time-based queries (recent traces)
CREATE INDEX agent_execution_trace_started IF NOT EXISTS
FOR (t:AgentExecutionTrace) ON (t.started_at);

// Index for filtering by success/failure
CREATE INDEX agent_execution_trace_success IF NOT EXISTS
FOR (t:AgentExecutionTrace) ON (t.success);

// Index for querying steps by type (ActionStep, PlanningStep)
CREATE INDEX agent_execution_step_type IF NOT EXISTS
FOR (s:AgentExecutionStep) ON (s.step_type);

// =============================================================================
// Example Node Structures
// =============================================================================

// AgentExecutionTrace node structure:
// {
//   id: "trace-uuid",
//   agent_name: "perception",
//   run_id: "run-uuid",
//   started_at: datetime(),
//   completed_at: datetime(),
//   step_count: 5,
//   planning_count: 2,
//   success: true,
//   error_message: null,
//   token_usage: {pre_prune: 1500, post_prune: 800, reduction_pct: 46.7}
// }

// AgentExecutionStep node structure:
// {
//   id: "step-uuid",
//   trace_id: "trace-uuid",
//   step_number: 1,
//   step_type: "ActionStep",  // or "PlanningStep"
//   timestamp: datetime(),
//   tool_name: "semantic_recall",
//   tool_arguments: {query: "recent memories"},
//   observation_summary: "[100 chars of observation]",
//   error: null
// }

// =============================================================================
// Relationships
// =============================================================================

// Trace contains steps (ordered)
// (t:AgentExecutionTrace)-[:HAS_STEP {order: 1}]->(s:AgentExecutionStep)

// Trace activated basins during execution
// (t:AgentExecutionTrace)-[:ACTIVATED_BASIN {strength: 0.8, at_step: 3}]->(b:MemoryCluster)

// Trace created memories
// (t:AgentExecutionTrace)-[:CREATED_MEMORY]->(m:Memory)

// Trace was orchestrated by manager trace
// (child:AgentExecutionTrace)-[:DELEGATED_FROM {at_step: 2}]->(parent:AgentExecutionTrace)
