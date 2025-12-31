# Tasks: Smolagents V2 Alignment

**Feature**: 039-smolagents-v2-alignment
**Status**: Planning
**Estimated Effort**: 3-4 days

---

## Phase 1: Planning Interval (Day 1 Morning)

### T001: Enable planning_interval on HeartbeatAgent
**File**: `api/agents/heartbeat_agent.py`
**Effort**: 30 min
**Status**: [X] Complete

- [ ] Add `planning_interval=3` to ToolCallingAgent initialization
- [ ] Verify PlanningStep appears in agent.memory.steps
- [ ] Add test case for planning phase count

```python
self.agent = ToolCallingAgent(
    tools=tools,
    model=self.model,
    max_steps=10,
    planning_interval=3,  # NEW
    step_callbacks=audit.get_registry("heartbeat_agent")
)
```

### T002: Enable planning_interval on OODA agents
**Files**: `api/agents/perception_agent.py`, `reasoning_agent.py`, `metacognition_agent.py`
**Effort**: 30 min
**Status**: [X] Complete

- [ ] Add `planning_interval=2` to each agent
- [ ] Standardize max_steps across agents (5 for leaf, 10 for orchestrator)

---

## Phase 2: Callback Registry (Day 1 Afternoon)

### T003: Create type-specific callback registry
**File**: `api/agents/audit.py` (extend)
**Effort**: 1 hour
**Status**: [X] Complete

- [ ] Define callback type enum: `PlanningStep`, `ActionStep`, `ToolCall`
- [ ] Implement `CallbackRegistry.register(step_type, callback)`
- [ ] Implement `CallbackRegistry.get_callbacks(step_type)` -> list
- [ ] Update existing audit callback to use registry

```python
from smolagents.types import PlanningStep, ActionStep

class CallbackRegistry:
    def __init__(self):
        self._callbacks: dict[type, list[Callable]] = {
            PlanningStep: [],
            ActionStep: [],
        }
    
    def register(self, step_type: type, callback: Callable):
        self._callbacks[step_type].append(callback)
    
    def get_registry(self, agent_name: str) -> dict[type, Callable]:
        """Return step_callbacks dict for agent initialization."""
        return {
            step_type: self._create_dispatcher(agent_name, callbacks)
            for step_type, callbacks in self._callbacks.items()
            if callbacks
        }
```

### T004: Implement IWMT coherence callback
**File**: `api/agents/callbacks/iwmt_callback.py` (new)
**Effort**: 1 hour
**Status**: [X] Complete

- [ ] Create callback that triggers on PlanningStep
- [ ] Call `assess_coherence()` from dionysus_mcp
- [ ] Inject coherence summary into `memory_step.plan`
- [ ] Log coherence level for observability

```python
async def iwmt_coherence_callback(memory_step: PlanningStep, agent) -> None:
    from dionysus_mcp.server import assess_coherence
    
    coherence = await assess_coherence()
    level = coherence.get("consciousness_level", 0)
    
    injection = f"\n\n[IWMT] Coherence: {level:.1%}"
    if level < 0.5:
        injection += " ⚠️ LOW - consider consolidating focus"
    
    memory_step.plan = (memory_step.plan or "") + injection
```

### T005: Implement basin activation callback
**File**: `api/agents/callbacks/basin_callback.py` (new)
**Effort**: 1 hour
**Status**: [X] Complete

- [ ] Create callback that triggers on ActionStep
- [ ] Detect `semantic_recall` tool calls
- [ ] Extract query, find related basins
- [ ] Call `activate_basin()` with strength based on relevance

---

## Phase 3: Memory Pruning (Day 2 Morning)

### T006: Implement memory pruning callback
**File**: `api/agents/callbacks/memory_callback.py` (new)
**Effort**: 45 min
**Status**: [X] Complete

- [ ] Create callback that triggers on ActionStep
- [ ] Check step_number against AGENT_MEMORY_WINDOW (default 3)
- [ ] Summarize observations older than window
- [ ] Preserve tool_calls metadata, prune verbose output

```python
MEMORY_WINDOW = int(os.getenv("AGENT_MEMORY_WINDOW", 3))

def memory_pruning_callback(memory_step: ActionStep, agent) -> None:
    latest = memory_step.step_number
    for prev in agent.memory.steps:
        if isinstance(prev, ActionStep) and prev.step_number <= latest - MEMORY_WINDOW:
            if prev.observations and len(prev.observations) > 200:
                prev.observations = f"[PRUNED] {prev.observations[:100]}..."
```

### T007: Add token usage tracking
**File**: `api/agents/audit.py`
**Effort**: 30 min
**Status**: [X] Complete

- [ ] Track token count before/after pruning
- [ ] Log reduction percentage
- [ ] Add metric to heartbeat summary

---

## Phase 4: ManagedAgent Migration (Day 2 Afternoon - Day 3)

### T008: Create ManagedAgent wrappers
**File**: `api/agents/managed/__init__.py` (new directory)
**Effort**: 1 hour
**Status**: [X] Complete

- [ ] Create `ManagedPerceptionAgent` wrapper
- [ ] Create `ManagedReasoningAgent` wrapper
- [ ] Create `ManagedMetacognitionAgent` wrapper
- [ ] Each wraps underlying ToolCallingAgent in ManagedAgent

```python
from smolagents import ManagedAgent

class ManagedPerceptionAgent:
    def __init__(self, model_id: str = "dionysus-agents"):
        self._inner = PerceptionAgent(model_id)
    
    def get_managed(self) -> ManagedAgent:
        with self._inner as agent:
            return ManagedAgent(
                agent=agent.agent,
                name="perception",
                description="""OBSERVE phase specialist.
                Gathers environment state via observe_environment.
                Recalls relevant memories via semantic_recall.
                Captures experiential state via mosaeic_capture.
                ALWAYS query wisdom graph for strategic principles."""
            )
```

### T009: Refactor ConsciousnessManager to use ManagedAgents
**File**: `api/agents/consciousness_manager.py`
**Effort**: 2 hours
**Status**: [X] Complete

- [ ] Replace manual OODA orchestration with CodeAgent + managed_agents
- [ ] Configure manager with planning_interval=3
- [ ] Remove manual phase chaining code
- [ ] Preserve River Metaphor flow adjustment (move to callback)

```python
from smolagents import CodeAgent

class ConsciousnessManager:
    def __init__(self, model_id: str = "dionysus-agents"):
        self.model = get_router_model(model_id)
        
        # Create managed sub-agents
        self.perception = ManagedPerceptionAgent(model_id).get_managed()
        self.reasoning = ManagedReasoningAgent(model_id).get_managed()
        self.metacognition = ManagedMetacognitionAgent(model_id).get_managed()
        
        # Manager orchestrates via natural language
        self.manager = CodeAgent(
            tools=[],
            model=self.model,
            managed_agents=[self.perception, self.reasoning, self.metacognition],
            planning_interval=3,
            max_steps=15,
            step_callbacks=get_audit_callback().get_registry("consciousness_manager")
        )
    
    async def run_ooda_cycle(self, context: dict) -> str:
        prompt = self._build_ooda_prompt(context)
        return self.manager.run(prompt)
```

### T010: Update tests for ManagedAgent pattern
**File**: `tests/unit/test_agents_refactor.py`
**Effort**: 1 hour
**Status**: [X] Complete

- [ ] Test manager delegates to correct sub-agent
- [ ] Test planning phases occur at expected intervals
- [ ] Test callbacks fire for each step type
- [ ] Verify backward compatibility with direct agent.run()

---

## Phase 5: Trajectory Persistence (Day 3-4)

### T011: Define AgentTrajectory Neo4j schema
**File**: `neo4j/schema/agent_trajectory.cypher` (new)
**Effort**: 30 min
**Status**: [ ] Todo

```cypher
// Constraint for trajectory uniqueness
CREATE CONSTRAINT agent_trajectory_id IF NOT EXISTS
FOR (t:AgentTrajectory) REQUIRE t.id IS UNIQUE;

// Index for querying by agent
CREATE INDEX agent_trajectory_agent IF NOT EXISTS
FOR (t:AgentTrajectory) ON (t.agent_name);

// Index for time-based queries
CREATE INDEX agent_trajectory_time IF NOT EXISTS
FOR (t:AgentTrajectory) ON (t.started_at);
```

### T012: Implement trajectory persistence service
**File**: `api/services/trajectory_service.py` (new)
**Effort**: 1.5 hours
**Status**: [ ] Todo

- [ ] `create_trajectory(agent_name, run_id)` -> trajectory_id
- [ ] `add_step(trajectory_id, step_data)` -> step_id
- [ ] `complete_trajectory(trajectory_id, success, summary)`
- [ ] `link_basin(trajectory_id, basin_id, strength)`
- [ ] `get_trajectory(trajectory_id)` -> full trajectory

### T013: Implement post-run persistence callback
**File**: `api/agents/callbacks/trajectory_callback.py` (new)
**Effort**: 1 hour
**Status**: [ ] Todo

- [ ] Register as final callback after agent.run() completes
- [ ] Extract all steps from agent.memory
- [ ] Call trajectory_service to persist
- [ ] Link activated basins from basin_activation_callback

### T014: Add trajectory query endpoints
**File**: `api/routers/agents.py` (new)
**Effort**: 1 hour
**Status**: [ ] Todo

- [ ] `GET /api/agents/trajectories` - list recent trajectories
- [ ] `GET /api/agents/trajectories/{id}` - get full trajectory
- [ ] `GET /api/agents/trajectories/{id}/replay` - formatted replay view

---

## Phase 6: Integration & Testing (Day 4)

### T015: Integration test - full heartbeat with new architecture
**File**: `tests/integration/test_smolagents_v2.py` (new)
**Effort**: 1.5 hours
**Status**: [ ] Todo

- [ ] Test HeartbeatAgent with planning_interval
- [ ] Verify IWMT callback fires on PlanningStep
- [ ] Verify basin activation on semantic_recall
- [ ] Verify trajectory persisted to Neo4j
- [ ] Measure token reduction from memory pruning

### T016: Benchmark token usage
**File**: `scripts/benchmark_token_usage.py` (new)
**Effort**: 45 min
**Status**: [ ] Todo

- [ ] Run 10-step heartbeat with and without pruning
- [ ] Compare token counts
- [ ] Document reduction percentage
- [ ] Add to CI as regression check

### T017: Update documentation
**Files**: `README.md`, `architecture.md`
**Effort**: 30 min
**Status**: [ ] Todo

- [ ] Document ManagedAgent hierarchy
- [ ] Document callback flow
- [ ] Document trajectory query endpoints
- [ ] Add mermaid diagram for OODA + callbacks

---

## Task Summary

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| 1. Planning Interval | T001-T002 | 1 hour | [ ] |
| 2. Callback Registry | T003-T005 | 3 hours | [ ] |
| 3. Memory Pruning | T006-T007 | 1.25 hours | [ ] |
| 4. ManagedAgent | T008-T010 | 4 hours | [ ] |
| 5. Trajectory Persistence | T011-T014 | 4 hours | [ ] |
| 6. Integration | T015-T017 | 2.75 hours | [ ] |
| **Total** | **17 tasks** | **~16 hours** | |

---

## Acceptance Checklist

- [ ] `planning_interval=3` on HeartbeatAgent, visible in logs
- [ ] IWMT coherence injected into planning phases
- [ ] Basin activation logged on semantic_recall
- [ ] Memory pruning reduces tokens by 30%+
- [ ] ConsciousnessManager uses native ManagedAgent
- [ ] Trajectories queryable via `/api/agents/trajectories`
- [ ] All existing tests pass
- [ ] New integration test passes
