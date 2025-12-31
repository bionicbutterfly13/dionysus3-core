# Dionysus Terminology Guide

This document disambiguates terms that have multiple meanings across different contexts in the codebase.

---

## Trajectory (Ambiguous Term)

**CAUTION**: "Trajectory" appears in two distinct contexts with different meanings.

### 1. Execution Trace (Operational)

**Location**: `api/models/memevolve.py`, `api/services/*`, `api/routers/memevolve.py`

**Meaning**: The sequence of steps an agent takes during a single run.

| Term | Definition |
|------|------------|
| `TrajectoryData` | Pydantic model containing agent execution steps |
| `TrajectoryStep` | Single action/observation pair from agent run |
| `TrajectoryMetadata` | Run metadata (agent_name, timestamps, energy) |
| `ExecutionTraceData` | Full trace with steps and basin links (spec-039) |
| `AgentExecutionTrace` | Neo4j node storing persisted execution trace |
| `AgentExecutionStep` | Neo4j node for individual step in trace |

**Example**:
```python
# This is an EXECUTION TRACE, not a state-space path
trajectory = TrajectoryData(
    steps=[
        TrajectoryStep(action="semantic_recall", observation="Found 3 memories"),
        TrajectoryStep(action="reflect_on_topic", observation="Pattern identified"),
    ],
    metadata=TrajectoryMetadata(agent_name="perception")
)
```

**Used for**: Debugging, replay, audit trails, operational observability.

---

### 2. State Trajectory (Theoretical)

**Location**: `specs/038-thoughtseeds-framework/`, IWMT/Active Inference literature

**Meaning**: A path through state space showing how the system's internal state evolves over time.

| Term | Definition |
|------|------------|
| State Trajectory | Sequence of state vectors in phase space |
| Basin Trajectory | Path of attractor basin activations over time |
| Belief Trajectory | Evolution of probabilistic beliefs (Active Inference) |
| ThoughtSeed Competition | State transitions between competing mental patterns |

**Example**:
```
# This is a STATE-SPACE TRAJECTORY, not an execution log
t=0: Basin[identity] = 0.8, Basin[security] = 0.2
t=1: Basin[identity] = 0.6, Basin[security] = 0.4  # Transition event
t=2: Basin[identity] = 0.3, Basin[security] = 0.7  # New attractor
```

**Used for**: Consciousness modeling, IWMT coherence, predictive processing, free energy minimization.

---

## Recommendation

When writing new code:

| If you mean... | Use this term |
|----------------|---------------|
| Agent step log | `ExecutionTrace`, `RunTrace`, `StepLog` |
| State evolution | `StateTrajectory`, `BasinPath`, `BeliefEvolution` |

When reading existing code:
- Check the file location to determine context
- `api/models/memevolve.py` → Execution trace
- `specs/038-*` or IWMT references → State trajectory

---

## Other Potentially Ambiguous Terms

### Memory

| Context | Meaning |
|---------|---------|
| `agent.memory` (smolagents) | In-context step history during run |
| `:Memory` (Neo4j) | Persisted episodic/semantic memory node |
| `MemoryCluster` | Attractor basin / thematic grouping |

### Basin

| Context | Meaning |
|---------|---------|
| Attractor Basin | Stable state in dynamical system (theoretical) |
| `MemoryCluster` | Neo4j implementation of semantic grouping |
| Basin Activation | Strengthening cluster relevance during cognition |

### Step

| Context | Meaning |
|---------|---------|
| `ActionStep` (smolagents) | Single tool call + observation |
| `PlanningStep` (smolagents) | Periodic replanning phase |
| `TrajectoryStep` | Persisted record of ActionStep |

---

## References

- [Smolagents Documentation](https://huggingface.co/docs/smolagents)
- Spec 038: ThoughtSeeds Framework (state-space dynamics)
- Spec 039: Smolagents V2 Alignment (execution traces)
- IWMT: Integrated World Modeling Theory
- Active Inference: Free Energy Principle applications
