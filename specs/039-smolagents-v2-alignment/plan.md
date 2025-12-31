# Implementation Plan: Smolagents V2 Alignment

## Overview

This plan implements native smolagents patterns for multi-agent orchestration, planning intervals, and consciousness integration. The goal is seamless alignment between agent cognition and the Dionysus consciousness substrate.

## Architecture Before/After

### Before (Current)
```
ConsciousnessManager
  ├── Manual OODA loop
  │     ├── perception.run() → wait
  │     ├── reasoning.run() → wait
  │     └── metacognition.run() → wait
  └── No planning phases
  └── Ephemeral memory
  └── No basin integration
```

### After (Target)
```
ConsciousnessManager (CodeAgent, manager)
  ├── managed_agents=[perception, reasoning, metacognition]
  ├── planning_interval=3
  ├── step_callbacks={
  │     PlanningStep: iwmt_coherence_callback,
  │     ActionStep: [basin_callback, memory_callback, audit_callback]
  │   }
  └── post_run: trajectory_persistence_callback
```

## Implementation Phases

### Phase 1: Quick Wins (Day 1 Morning)
**Goal**: Enable planning without breaking existing code

1. Add `planning_interval=3` to HeartbeatAgent
2. Add `planning_interval=2` to leaf agents
3. Verify PlanningStep appears in logs
4. No API changes, no new files

**Validation**: Run heartbeat, confirm 3 planning phases in 10 steps

### Phase 2: Callback Infrastructure (Day 1 Afternoon)
**Goal**: Type-specific callback routing

1. Extend `api/agents/audit.py` with CallbackRegistry
2. Create `api/agents/callbacks/` directory
3. Implement IWMT coherence callback
4. Implement basin activation callback
5. Wire callbacks into existing agents

**Validation**: Planning phases show IWMT coherence injection

### Phase 3: Memory Optimization (Day 2 Morning)
**Goal**: Reduce token usage

1. Implement memory pruning callback
2. Add token tracking metrics
3. Configure AGENT_MEMORY_WINDOW env var

**Validation**: 10-step heartbeat uses 30% fewer tokens

### Phase 4: ManagedAgent Migration (Day 2 Afternoon - Day 3)
**Goal**: Native multi-agent orchestration

1. Create ManagedAgent wrappers in `api/agents/managed/`
2. Refactor ConsciousnessManager to use CodeAgent + managed_agents
3. Update tests

**Validation**: Manager delegates to sub-agents via natural language

### Phase 5: Trajectory Persistence (Day 3-4)
**Goal**: Durable agent memory in Neo4j

1. Define AgentTrajectory schema
2. Implement trajectory_service
3. Implement post-run persistence callback
4. Add query endpoints

**Validation**: `GET /api/agents/trajectories` returns recent runs

### Phase 6: Polish (Day 4)
**Goal**: Integration testing and documentation

1. Full integration test
2. Token usage benchmark
3. Documentation update

## File Changes Summary

### New Files
```
api/agents/callbacks/__init__.py
api/agents/callbacks/iwmt_callback.py
api/agents/callbacks/basin_callback.py
api/agents/callbacks/memory_callback.py
api/agents/callbacks/trajectory_callback.py
api/agents/managed/__init__.py
api/agents/managed/perception.py
api/agents/managed/reasoning.py
api/agents/managed/metacognition.py
api/services/trajectory_service.py
api/routers/agents.py
neo4j/schema/agent_trajectory.cypher
tests/integration/test_smolagents_v2.py
scripts/benchmark_token_usage.py
```

### Modified Files
```
api/agents/audit.py              # Extend with CallbackRegistry
api/agents/heartbeat_agent.py    # Add planning_interval
api/agents/perception_agent.py   # Add planning_interval
api/agents/reasoning_agent.py    # Add planning_interval
api/agents/metacognition_agent.py # Add planning_interval
api/agents/consciousness_manager.py # Refactor to ManagedAgent
api/agents/__init__.py           # Export new components
api/main.py                      # Include agents router
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ManagedAgent latency | Phase 4 includes benchmarking; can revert to manual |
| Callback complexity | Single registry, clear ownership, comprehensive tests |
| Neo4j write volume | Async persistence, batch writes |
| Breaking existing behavior | Each phase is independently deployable |

## Rollback Plan

Each phase can be reverted independently:
- Phase 1: Remove planning_interval (1 line per file)
- Phase 2: Remove callbacks from step_callbacks dict
- Phase 3: Set AGENT_MEMORY_WINDOW=999 to disable
- Phase 4: Swap ConsciousnessManager import to legacy version
- Phase 5: Remove trajectory endpoints from router

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Planning phases per heartbeat | 3 | Log count |
| Token reduction | 30%+ | Benchmark script |
| IWMT injection rate | 100% | Log grep |
| Trajectory persistence | 100% | Neo4j query |
| Test pass rate | 100% | CI pipeline |
