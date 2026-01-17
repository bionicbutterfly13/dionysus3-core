# Track Plan: Smolagents V2 Alignment

**Track ID**: 039-smolagents-v2-alignment
**Status**: Done

## Phase 1: Planning Interval [checkpoint: complete]

- [x] **Task 1.1**: Enable `planning_interval=3` on HeartbeatAgent in `api/agents/heartbeat_agent.py`
- [x] **Task 1.2**: Enable `planning_interval=2` on OODA agents in `perception_agent.py`, `reasoning_agent.py`, `metacognition_agent.py`

## Phase 2: Callback Registry [checkpoint: complete]

- [x] **Task 2.1**: Create type-specific callback registry in `api/agents/audit.py`
- [x] **Task 2.2**: Implement IWMT coherence callback in `api/agents/callbacks/iwmt_callback.py`
- [x] **Task 2.3**: Implement basin activation callback in `api/agents/callbacks/basin_callback.py`

## Phase 3: Memory Pruning [checkpoint: complete]

- [x] **Task 3.1**: Implement memory pruning callback in `api/agents/callbacks/memory_callback.py`
- [x] **Task 3.2**: Add token usage tracking in `api/agents/audit.py`

## Phase 4: ManagedAgent Migration [checkpoint: complete]

- [x] **Task 4.1**: Create ManagedAgent wrappers in `api/agents/managed/__init__.py`
- [x] **Task 4.2**: Refactor ConsciousnessManager to use ManagedAgents in `api/agents/consciousness_manager.py`
- [x] **Task 4.3**: Update tests for ManagedAgent pattern in `tests/unit/test_agents_refactor.py`

## Phase 5: Execution Trace Persistence [checkpoint: complete]

- [x] **Task 5.1**: Define AgentExecutionTrace Neo4j schema in `neo4j/schema/agent_execution_trace.cypher`
- [x] **Task 5.2**: Implement execution trace persistence service in `api/services/execution_trace_service.py`
- [x] **Task 5.3**: Implement post-run persistence callback in `api/agents/callbacks/execution_trace_callback.py`
- [x] **Task 5.4**: Add execution trace query endpoints in `api/routers/agents.py`

## Phase 6: Integration & Testing

- [x] **Task 6.1**: Integration test - full heartbeat with new architecture in `tests/integration/test_smolagents_v2.py`
- [x] **Task 6.2**: Benchmark token usage in `scripts/benchmark_token_usage.py`
- [x] **Task 6.3**: Update documentation in `specs/039-smolagents-v2-alignment/spec.md`

## Acceptance Checklist

- [x] `planning_interval=3` on HeartbeatAgent, visible in logs
- [x] IWMT coherence injected into planning phases
- [x] Basin activation logged on semantic_recall
- [x] Memory pruning reduces tokens by 30%+
- [x] ConsciousnessManager uses native ManagedAgent
- [x] Execution traces queryable via `/api/agents/traces`
- [x] All existing tests pass (754 passed, 82 skipped)
- [x] New integration test passes (19/19 tests)
