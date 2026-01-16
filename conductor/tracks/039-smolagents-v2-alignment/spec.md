# Feature Specification: Smolagents V2 Alignment

**Track ID**: 039-smolagents-v2-alignment
**Status**: In Progress (95%)
**Depends On**: 033-smolagents-standardization (complete)
**Input**: [Smolagents v1.23+ Docs](https://huggingface.co/docs/smolagents), Context7 analysis
**Terminology**: See [docs/TERMINOLOGY.md](../../../docs/TERMINOLOGY.md) for disambiguation of "trajectory" and other overloaded terms

## Overview

Upgrade dionysus3-core's smolagents integration to leverage native multi-agent orchestration, planning intervals, and memory persistence. This aligns with smolagents v1.23+ production patterns and deeply integrates agent cognition with the Dionysus consciousness framework (IWMT, attractor basins, Active Inference).

## Problem Statement

Current implementation gaps:
1. **Manual OODA orchestration** - `ConsciousnessManager` manually chains agents instead of using native `ManagedAgent`
2. **No planning intervals** - Agents run linearly without periodic fact-checking or replanning
3. **Ephemeral agent memory** - Execution traces lost after each run
4. **No consciousness integration** - Step callbacks don't trigger IWMT coherence or basin activation
5. **Token accumulation** - Full observation history kept, causing context bloat

## Requirements

### Core Architecture

- **FR-039-001**: Migrate `ConsciousnessManager` to native `ManagedAgent` hierarchy pattern
- **FR-039-002**: Enable `planning_interval=3` on all orchestrator agents
- **FR-039-003**: Implement `PlanningStep` callback for IWMT coherence injection

### Memory & Persistence

- **FR-039-004**: Persist agent trajectories to Neo4j procedural memory
- **FR-039-005**: Implement dynamic memory pruning callback

### Basin Integration

- **FR-039-006**: Implement `ActionStep` callback for basin activation
- **FR-039-007**: Route ThoughtSeed competition through agent decisions

### Observability

- **FR-039-008**: Type-specific step callbacks registry

## Success Criteria

- **SC-001**: ConsciousnessManager uses native `ManagedAgent` pattern - zero manual delegation code
- **SC-002**: HeartbeatAgent completes 10-step cycles with 3 planning phases visible in logs
- **SC-003**: Agent trajectories queryable in Neo4j
- **SC-004**: IWMT coherence injected into planning - visible in agent output
- **SC-005**: Basin activations logged during semantic recall operations
- **SC-006**: Token usage reduced 30%+ on 10-step heartbeat cycles (memory pruning)

## Technical Design

### ManagedAgent Hierarchy

```
ConsciousnessManager (CodeAgent, manager)
├── perception (ManagedAgent)
│   └── PerceptionAgent (ToolCallingAgent)
├── reasoning (ManagedAgent)
│   └── ReasoningAgent (ToolCallingAgent)
└── metacognition (ManagedAgent)
    └── MetacognitionAgent (ToolCallingAgent)
```

## Migration Path

1. **Phase 1**: Add planning_interval to existing agents (non-breaking)
2. **Phase 2**: Implement callback registry with type routing
3. **Phase 3**: Refactor ConsciousnessManager to ManagedAgent pattern
4. **Phase 4**: Add trajectory persistence
5. **Phase 5**: Wire basin activation callbacks
6. **Phase 6**: Integration & Testing

## Dependencies

- `smolagents>=1.23.0` (already satisfied)
- Neo4j schema update (additive, no migration)
- spec-033 complete (ToolCallingAgent migration done)
