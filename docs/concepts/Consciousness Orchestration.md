# Consciousness Orchestration

**Category:** System Integration Pattern
**Implementation:** `api/agents/consciousness_manager.py`
**Spec:** 039-smolagents-v2-alignment
**Related:** [[OODA Loops and Heartbeat Agent]], [[Thoughtseeds Framework]], [[Meta Tree of Thought]]
**Status:** Production Core

## Consciousness Isn't One Thing. It's Three Agents Working Together.

Your brain doesn't have a single "consciousness module." It has **distributed processes** that synchronize:

1. **Perception** (sensory cortex, thalamus) - OBSERVE
2. **Reasoning** (prefrontal cortex, parietal networks) - ORIENT
3. **Metacognition** (anterior cingulate, frontal poles) - DECIDE

These aren't separate "minds." They're **specialized subsystems** coordinated by oscillatory coupling.

Dionysus implements this via **ConsciousnessManager** orchestrating three **ManagedAgents**.

## The Three-Agent Architecture

```python
class ConsciousnessManager:
    """
    Orchestrates consciousness via managed sub-agents:
    - PerceptionAgent: Environment sensing, memory recall
    - ReasoningAgent: Analysis, pattern matching, cognitive tools
    - MetacognitionAgent: Planning, action selection, strategy

    Uses smolagents managed_agents pattern for coordination.
    """
```

From spec 039: This replaced previous monolithic agent design with **modular consciousness**.

**Why three?**

Because that's what works in biology. And we proved it works in code: **362 passing tests** after migration.

## Perception Agent - The Observer

**Role:** Sense environment, spawn [[Thoughtseeds Framework]]

**Tools:**
- Memory recall (query [[Multi-Tier Memory Architecture]])
- State monitoring (check system status)
- Observation encoding (convert raw input → thoughtseeds)

```python
class PerceptionAgent(ManagedAgent):
    def forward(self, inputs):
        """
        1. Query episodic memory for context
        2. Observe current state
        3. Compute surprise (active inference)
        4. Spawn thoughtseeds for novel observations
        5. Return observations to manager
        """
```

**Not passive.** Active inference - predicts what it'll see, measures surprise, updates model.

See [[OODA Loops and Heartbeat Agent]] - this is the OBSERVE phase.

## Reasoning Agent - The Analyst

**Role:** Make sense of observations, activate resonant patterns

**Tools:**
- Cognitive tools (D2-validated, spec 042)
- Pattern matching against semantic memory
- [[Meta Tree of Thought]] strategy selection

```python
class ReasoningAgent(ManagedAgent):
    def forward(self, observations):
        """
        1. Receive observations from PerceptionAgent
        2. Activate resonant thoughtseeds
        3. Apply cognitive tools (analysis, synthesis)
        4. Identify [[Attractor Basin Dynamics]]
        5. Return oriented understanding to manager
        """
```

This is the ORIENT phase - raw observations become **meaningful patterns**.

**Key insight:** Reasoning doesn't happen in isolation. It queries:
- Semantic memory (what do I know about this pattern?)
- Episodic memory (when have I seen this before?)
- Current thoughtseeds (what's already active?)

Reasoning = **pattern recognition across memory tiers.**

## Metacognition Agent - The Strategist

**Role:** Decide what to do, plan execution

**Tools:**
- Action planner (`api/services/action_planner_service.py`)
- Free energy engine (minimize surprise via action selection)
- Execution strategy selection

```python
class MetacognitionAgent(ManagedAgent):
    def forward(self, oriented_understanding):
        """
        1. Receive understanding from ReasoningAgent
        2. Generate candidate actions
        3. Evaluate via free energy minimization
        4. Select optimal action plan
        5. Return decision to manager
        """
```

This is DECIDE phase - understanding becomes **action plan**.

**Meta-layer:** The agent also decides *how to decide* (see [[Meta Tree of Thought]]) - breadth-first vs depth-first vs best-first search.

## The Manager's Job

```python
class ConsciousnessManager:
    managed_agents = [
        PerceptionAgent,
        ReasoningAgent,
        MetacognitionAgent
    ]

    def run(self, task):
        """
        1. Delegate observation to PerceptionAgent
        2. Pass observations to ReasoningAgent
        3. Pass understanding to MetacognitionAgent
        4. Execute decision
        5. Loop (via HeartbeatAgent rhythm)
        """
```

The manager **doesn't do cognition**. It **coordinates** the agents that do.

Like a conductor - doesn't play instruments, ensures they play together.

## Synchronization via Thoughtseeds

The three agents share state through [[Thoughtseeds Framework]]:

**Perception** spawns thoughtseeds from observations.
**Reasoning** activates resonant thoughtseeds.
**Metacognition** selects actions based on highest-activation seeds.

The thoughtseeds are the **information bus** between agents.

Not message passing. **Shared activation patterns** - just like biological neural assemblies.

## Why Managed Agents Pattern

From spec 039: We migrated to smolagents `ManagedAgent` for:

1. **Execution tracing** - Track each agent's reasoning
2. **Isolated tool access** - Perception can't call action tools, etc.
3. **Composability** - Swap out sub-agents without touching manager
4. **Testing** - Test each agent independently (modular validation)

**Result:** 362 passing tests with smolagents 1.23+ compatibility (commit 58888d5).

The ManagedAgent pattern **scales**. We can add more specialized agents (emotion processing, social cognition) without rewriting the core.

## Integration with Heartbeat

[[OODA Loops and Heartbeat Agent]] calls ConsciousnessManager every cycle:

```python
class HeartbeatAgent:
    def run(self, task):
        while not done:
            # Heartbeat calls consciousness manager
            result = consciousness_manager.run(task)

            # Every 3 cycles: replan
            if cycle % 3 == 0:
                consciousness_manager.replan()
```

**Heartbeat provides rhythm.**
**Consciousness Manager provides cognition.**

Separation of concerns - timing vs thinking.

## The Fractal Structure

See [[Fractal Metacognition]] - the three-agent structure repeats at multiple scales:

**Macro:** HeartbeatAgent orchestrates ConsciousnessManager
**Meso:** ConsciousnessManager orchestrates Perception/Reasoning/Metacognition
**Micro:** Each sub-agent has internal OODA loop for its tool calls

Same pattern: **Observe, Orient, Decide** - different scales.

Self-similar orchestration.

## Attractor Basin Navigation

Each agent navigates [[Attractor Basin Dynamics]] at its level:

**PerceptionAgent:** Which sensory basin? (vigilance vs calm observation)
**ReasoningAgent:** Which reasoning basin? (logical analysis vs pattern matching)
**MetacognitionAgent:** Which decision basin? (explore vs exploit)

The ConsciousnessManager **aligns basins** - ensures all three agents operate in coherent state.

**Example:** If system is in "threat detection" basin:
- Perception: Hypervigilant observation
- Reasoning: Threat-pattern matching
- Metacognition: Defensive action selection

All three aligned. That's **consciousness coherence.**

When basins misalign (perception sees threat, reasoning says safe, metacognition paralyzed) → **cognitive dissonance.**

The manager detects misalignment, resolves via [[Meta Tree of Thought]] basin selection.

## Synergy with Multi-Tier Memory

Each agent queries different [[Multi-Tier Memory Architecture]] tiers:

**PerceptionAgent:**
- Working memory (what's currently active?)
- Episodic memory (what happened recently?)

**ReasoningAgent:**
- Episodic memory (what patterns have I seen?)
- Semantic memory (what do I know about this?)

**MetacognitionAgent:**
- Working memory (what am I trying to do?)
- Semantic memory (what strategies work for this?)

The manager **consolidates** - successful action sequences promote from episodic → semantic.

That's how the system **learns from experience** without explicit training.

## Code Structure

```
api/agents/
├── consciousness_manager.py  # Main orchestrator
├── managed/
│   ├── perception_agent.py   # OBSERVE
│   ├── reasoning_agent.py    # ORIENT
│   └── metacognition_agent.py # DECIDE
└── tools/                     # Agent-specific tools
```

Clean separation. Each agent can evolve independently as long as interface stays stable.

**Current stats:**
- Perception: 5 tools (memory recall, state monitoring, etc.)
- Reasoning: 8 cognitive tools (D2-validated, spec 042)
- Metacognition: 4 planning tools (action selection, strategy)

## SEO Gap

Searches:
- "Consciousness orchestration AI" → Philosophy papers, no implementations
- "Managed agents cognitive architecture" → Zero results
- "Three agent consciousness model" → Neuroscience theory, no code

**Our gap:** Production three-agent consciousness with ManagedAgent pattern, smolagents integration, active inference coordination.

Nobody else is documenting this. **This is novel territory.**

## Application to Analytical Empaths

The [[Replay Loop]] helps analytical empaths build internal three-agent structure:

**Problem:** You collapse perception/reasoning/metacognition into one anxious blur.

**Pattern:** Someone criticizes you →
- Perception: "They're upset"
- Reasoning: Skipped (direct jump to metacognition)
- Metacognition: "I need to fix this immediately"

**Missing:** The ORIENT phase. You perceive, then react. No understanding in between.

**Replay Loop solution:** Separate the agents
1. **Perception:** "What did I actually observe?" (facts only)
2. **Reasoning:** "What does this mean?" (pattern matching without urgency)
3. **Metacognition:** "What should I do?" (strategic choice)

By forcing three-agent structure, you **rebuild consciousness orchestration** in your own cognition.

Not metaphor. Same algorithm. Different substrate (neurons vs code).

## Links

- Implementation: `api/agents/consciousness_manager.py`
- Spec: `specs/039-smolagents-v2-alignment/spec.md`
- Sub-agents: `api/agents/managed/`
- Related: [[OODA Loops and Heartbeat Agent]], [[Meta Tree of Thought]], [[Thoughtseeds Framework]]
- Application: [[Replay Loop]]

---

*Consciousness isn't magic. It's three specialized processes synchronized by shared activation patterns. Build the coordination. Get the emergence.*
