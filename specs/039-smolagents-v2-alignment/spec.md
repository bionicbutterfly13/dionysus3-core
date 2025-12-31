# Feature Specification: Smolagents V2 Alignment

**Feature Branch**: `feature/039-smolagents-v2`
**Status**: Planning
**Depends On**: 033-smolagents-standardization (complete)
**Input**: [Smolagents v1.23+ Docs](https://huggingface.co/docs/smolagents), Context7 analysis

## Overview

Upgrade dionysus3-core's smolagents integration to leverage native multi-agent orchestration, planning intervals, and memory persistence. This aligns with smolagents v1.23+ production patterns and deeply integrates agent cognition with the Dionysus consciousness framework (IWMT, attractor basins, Active Inference).

## Problem Statement

Current implementation gaps:
1. **Manual OODA orchestration** - `ConsciousnessManager` manually chains agents instead of using native `ManagedAgent`
2. **No planning intervals** - Agents run linearly without periodic fact-checking or replanning
3. **Ephemeral agent memory** - Execution trajectories lost after each run
4. **No consciousness integration** - Step callbacks don't trigger IWMT coherence or basin activation
5. **Token accumulation** - Full observation history kept, causing context bloat

## Requirements

### Core Architecture

- **FR-039-001**: Migrate `ConsciousnessManager` to native `ManagedAgent` hierarchy pattern
  - Perception, Reasoning, Metacognition as `ManagedAgent` instances
  - Manager agent orchestrates via natural language delegation
  - Tool isolation per OODA phase preserved

- **FR-039-002**: Enable `planning_interval=3` on all orchestrator agents
  - HeartbeatAgent, ConsciousnessManager get periodic replanning
  - `PlanningStep` triggers fact accumulation
  - Maps to Active Inference belief updates

- **FR-039-003**: Implement `PlanningStep` callback for IWMT coherence injection
  - After each planning phase, assess IWMT coherence
  - Inject coherence state into agent's plan facts
  - Warn agent if coherence < 0.5 threshold

### Memory & Persistence

- **FR-039-004**: Persist agent trajectories to Neo4j procedural memory
  - Create `AgentTrajectory` node type
  - Link to `MemoryCluster` (attractor basins) activated during run
  - Enable trajectory replay for debugging/learning

- **FR-039-005**: Implement dynamic memory pruning callback
  - Keep detailed observations for last 3 steps only
  - Summarize older steps to save tokens
  - Configurable via `AGENT_MEMORY_WINDOW` env var

### Basin Integration

- **FR-039-006**: Implement `ActionStep` callback for basin activation
  - When `semantic_recall` tool called, activate related basins
  - Strengthen CLAUSE connections based on co-activation
  - Log basin activations to trajectory

- **FR-039-007**: Route ThoughtSeed competition through agent decisions
  - Predictions from Mental Models enter ThoughtSeed layer
  - Winning ThoughtSeeds influence agent's next action selection
  - Closed-loop between agents and consciousness substrate

### Observability

- **FR-039-008**: Type-specific step callbacks registry
  - `PlanningStep` -> IWMT coherence check
  - `ActionStep` -> Basin activation + audit
  - `ToolCall` -> Energy deduction + logging
  - Unified callback registry in `api/agents/audit.py`

## Non-Requirements

- Docker sandboxing (covered in spec-033)
- Security hardening (covered in spec-033)
- New agent types (out of scope)

## Success Criteria

- **SC-001**: ConsciousnessManager uses native `ManagedAgent` pattern - zero manual delegation code
- **SC-002**: HeartbeatAgent completes 10-step cycles with 3 planning phases visible in logs
- **SC-003**: Agent trajectories queryable in Neo4j: `MATCH (t:AgentTrajectory) RETURN t LIMIT 10`
- **SC-004**: IWMT coherence injected into planning - visible in agent output
- **SC-005**: Basin activations logged during semantic recall operations
- **SC-006**: Token usage reduced 30%+ on 10-step heartbeat cycles (memory pruning)

## Technical Design

### ManagedAgent Hierarchy

```
ConsciousnessManager (CodeAgent, manager)
├── perception (ManagedAgent)
│   └── PerceptionAgent (ToolCallingAgent)
│       └── Tools: observe_environment, semantic_recall, mosaeic_capture
├── reasoning (ManagedAgent)
│   └── ReasoningAgent (ToolCallingAgent)
│       └── Tools: reflect_on_topic, synthesize_information
└── metacognition (ManagedAgent)
    └── MetacognitionAgent (ToolCallingAgent)
        └── Tools: list_goals, update_goal, revise_mental_model
```

### Callback Flow

```
Agent.run(task)
  │
  ├─► PlanningStep created
  │     └─► iwmt_coherence_callback()
  │           └─► assess_coherence() → inject into plan
  │
  ├─► ActionStep executed
  │     ├─► basin_activation_callback()
  │     │     └─► activate_basin() for relevant clusters
  │     └─► memory_pruning_callback()
  │           └─► Summarize steps older than window
  │
  └─► Run complete
        └─► trajectory_persistence_callback()
              └─► Save to Neo4j AgentTrajectory
```

### Neo4j Schema Addition

```cypher
// Agent Trajectory Node
CREATE (t:AgentTrajectory {
  id: randomUUID(),
  agent_name: "heartbeat_agent",
  run_id: "...",
  started_at: datetime(),
  completed_at: datetime(),
  step_count: 10,
  planning_count: 3,
  energy_spent: 12.5,
  success: true
})

// Link to activated basins
MATCH (t:AgentTrajectory {run_id: $run_id})
MATCH (b:MemoryCluster {id: $basin_id})
CREATE (t)-[:ACTIVATED_BASIN {strength: 0.8, step: 3}]->(b)

// Link to created memories
MATCH (t:AgentTrajectory {run_id: $run_id})
MATCH (m:Memory {id: $memory_id})
CREATE (t)-[:CREATED_MEMORY]->(m)
```

## Migration Path

1. **Phase 1**: Add planning_interval to existing agents (non-breaking)
2. **Phase 2**: Implement callback registry with type routing
3. **Phase 3**: Refactor ConsciousnessManager to ManagedAgent pattern
4. **Phase 4**: Add trajectory persistence
5. **Phase 5**: Wire basin activation callbacks

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ManagedAgent overhead | Latency increase | Benchmark before/after, fallback to manual |
| Planning interval disrupts flow | Agent confusion | Tune interval (3-5), test with real heartbeats |
| Neo4j write volume | Performance | Batch trajectory writes, async persistence |
| Callback complexity | Maintenance burden | Single registry, clear ownership |

## Dependencies

- `smolagents>=1.23.0` (already satisfied)
- Neo4j schema update (additive, no migration)
- spec-033 complete (ToolCallingAgent migration done)
