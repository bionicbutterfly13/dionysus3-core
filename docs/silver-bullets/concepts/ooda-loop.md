# OODA Loop

**Category**: Core Concept
**Type**: Cognitive Process
**Implementation**: `api/agents/heartbeat_agent.py`, `api/agents/consciousness_manager.py`

---

## Definition

An **OODA loop** is a continuous decision cycle that iterates through four phases: **Observe-Orient-Decide-Act**. Originally developed for fighter pilot decision-making, it represents how autonomous systems gather information, analyze it, make decisions, and execute actions in dynamic environments.

Think of it as **your cognitive heartbeat**—a rhythmic cycle that keeps you oriented in changing circumstances, constantly updating your mental model of reality.

## Key Characteristics

- **Continuous**: Never stops—each cycle feeds into the next
- **Adaptive**: Updates beliefs and plans based on new observations
- **Hierarchical**: Can nest multiple OODA loops at different timescales
- **Competitive**: Faster loops outmaneuver slower opponents
- **Implicit**: Most cycling happens unconsciously until surprise interrupts
- **Energy-Bounded**: Each cycle consumes cognitive resources

## How It Works

### The Four Phases

```
OBSERVE → ORIENT → DECIDE → ACT
    ↑__________________________|

    Continuous feedback loop
```

### Step-by-Step Process

1. **OBSERVE**: Gather raw data from environment and internal state
   - What changed since last cycle?
   - What's the current context?
   - What memories are relevant?

2. **ORIENT**: Analyze observations to update mental models
   - What patterns exist in the data?
   - How does this relate to prior knowledge?
   - What are possible interpretations?

3. **DECIDE**: Select actions based on oriented understanding
   - What goals are active?
   - Which action best reduces free energy?
   - What's the confidence level?

4. **ACT**: Execute the selected action
   - Perform the action
   - Create new observations
   - Begin next cycle

### Visual Representation

```
┌─────────────────────────────────────────────┐
│         OODA LOOP CYCLE                     │
│                                             │
│  OBSERVE                                    │
│  ┌─────────────────────────┐               │
│  │ Environment Scan        │               │
│  │ Memory Recall           │               │
│  │ MOSAEIC Capture         │               │
│  └──────────┬──────────────┘               │
│             ↓                               │
│  ORIENT                                     │
│  ┌─────────────────────────┐               │
│  │ Pattern Recognition     │               │
│  │ Mental Model Update     │               │
│  │ Synthesis               │               │
│  └──────────┬──────────────┘               │
│             ↓                               │
│  DECIDE                                     │
│  ┌─────────────────────────┐               │
│  │ Goal Review             │               │
│  │ Action Selection        │               │
│  │ Plan Generation         │               │
│  └──────────┬──────────────┘               │
│             ↓                               │
│  ACT                                        │
│  ┌─────────────────────────┐               │
│  │ Execute Action          │               │
│  │ Create Effects          │               │
│  │ Generate Observations   │               │
│  └──────────┬──────────────┘               │
│             │                               │
│             └───────┐                       │
│                     ↓                       │
│              Next OBSERVE                   │
└─────────────────────────────────────────────┘
```

## Implementation

### HeartbeatAgent - Top-Level OODA

**Code**: `api/agents/heartbeat_agent.py:14-111`

The `HeartbeatAgent` implements the top-level OODA loop using smolagents `ToolCallingAgent` with periodic replanning:

```python
# From heartbeat_agent.py:38-47
self.agent = ToolCallingAgent(
    tools=tools,
    model=self.model,
    max_steps=10,
    planning_interval=3,  # Re-plan every 3 action steps (OODA cycle)
    name="heartbeat_agent",
    description="Autonomous cognitive decision cycle agent.",
    verbosity_level=1,
    step_callbacks=audit.get_registry("heartbeat_agent")
)
```

**Key Properties**:
- `planning_interval=3`: Triggers periodic ORIENT phase (replanning)
- `max_steps=10`: Energy budget constraint
- Step callbacks: Audit trail for each OODA phase
- Timeout gating: Prevents runaway loops

### ConsciousnessManager - Multi-Agent OODA

**Code**: `api/agents/consciousness_manager.py:157-395`

The `ConsciousnessManager` orchestrates specialized agents for each OODA phase:

```python
# From consciousness_manager.py:120-146
self.orchestrator = CodeAgent(
    managed_agents=[
        perception_managed,      # OBSERVE phase
        reasoning_managed,       # ORIENT phase
        metacognition_managed,   # DECIDE phase
        marketing_managed        # ACT phase (domain-specific)
    ],
    planning_interval=3,  # Re-plan every 3 steps
    max_steps=15
)
```

**Phase Mapping**:
- **OBSERVE** → `PerceptionAgent`: Environment scan, memory recall, MOSAEIC capture
- **ORIENT** → `ReasoningAgent`: Pattern analysis, synthesis, cognitive tools
- **DECIDE** → `MetacognitionAgent`: Goal review, action selection, planning
- **ACT** → Tool execution: Perform selected actions

### Planning Interval Mechanism

**Code**: `specs/039-smolagents-v2-alignment/spec.md:40-42`

```
planning_interval=3 means:
Step 1: Action
Step 2: Action
Step 3: Action
Step 4: PlanningStep (ORIENT phase - replanning)
Step 5: Action
Step 6: Action
Step 7: Action
Step 8: PlanningStep (another ORIENT cycle)
...
```

This creates a **nested OODA rhythm**:
- Micro-cycle: Each action step
- Meso-cycle: Every 3 steps (planning interval)
- Macro-cycle: Full run completion

### OODA Cycle Execution

**Code**: `api/agents/consciousness_manager.py:166-395`

```python
async def _run_ooda_cycle(self, initial_context: Dict[str, Any]):
    # OBSERVE: Bootstrap Recall (pre-cycle observation)
    bootstrap_result = await self.bootstrap_svc.recall_context(...)
    initial_context["bootstrap_past_context"] = bootstrap_result

    # ORIENT: Coordination Plan (meta-cognitive selection)
    coordination_plan = await coordinator.coordinate(task_query, ...)

    # Full OODA Delegation
    prompt = """
    1. Delegate to 'perception' to OBSERVE
    2. Delegate to 'reasoning' to ORIENT
    3. Delegate to 'metacognition' to DECIDE
    4. Synthesize into ACT plan
    """

    result = await run_agent_with_timeout(self.orchestrator, prompt)

    # POST-CYCLE: Calculate surprise for next cycle
    surprise_level = 1.0 - confidence
    adjusted_lr = metaplasticity_svc.calculate_learning_rate(surprise_level)
```

### Tests

- **Integration**: `scripts/test_heartbeat_agent.py`
- **Unit**: `tests/unit/test_heartbeat_agent.py`
- **OODA Cycle**: `scripts/test_memevolve_recall.py` (full consciousness cycle)

## Related Concepts

**Prerequisites** (understand these first):
- [[active-inference]] - OODA minimizes free energy via prediction updates
- [[prediction-error]] - Drives ORIENT phase adjustments

**Builds Upon** (this uses):
- [[thoughtseed-competition]] - DECIDE phase selects winning thoughtseed
- [[attractor-basin]] - OBSERVE/ORIENT activate and strengthen basins
- [[metacognitive-feelings]] - Generated during ORIENT→DECIDE transition

**Used By** (depends on this):
- [[planning-interval]] - Periodic ORIENT phases during ACT
- [[basin-transition]] - OODA cycles trigger basin shifts under high surprise
- [[metaplasticity]] - Surprise from OODA outcome adjusts learning rates

**Related** (similar or complementary):
- [[declarative-metacognition]] - Knowledge accessed during ORIENT
- [[procedural-metacognition]] - Regulates OODA resource allocation
- [[bootstrap-recall]] - Pre-cycle OBSERVE phase
- [[cognitive-coordination]] - Selects reasoning mode for ORIENT phase

## Examples

### Example 1: Clinical Debugging Session

**Context**: Patient reports "I feel stuck" but can't articulate why

**OODA Execution**:

```
OBSERVE:
- Patient verbal report: "stuck"
- Non-verbal cues: fidgeting, averted gaze
- Recall: Similar presentations in past cases
- Context: Third session, working on career transition

ORIENT:
- Pattern: "Stuck" = approach-avoidance conflict
- Mental model: Fear of success/identity loss
- Hypothesis: Analytical Empath measuring self by crisis metrics

DECIDE:
- Goal: Surface the conflict to awareness
- Action: "What would happen if you weren't stuck?"
- Confidence: 0.75

ACT:
- Execute question
- Observe patient response (tears, relief)
- Next OBSERVE: "That's the question I've been avoiding"

Result: OODA cycle broke through defensive basin
```

### Example 2: Agent Heartbeat Execution

**Code Example**: From `scripts/test_heartbeat_agent.py`

```python
# Heartbeat context
context = {
    "heartbeat_number": 42,
    "current_energy": 15,
    "max_energy": 20,
    "user_present": False,
    "active_goals": [
        {"goal": "Maintain session continuity", "priority": 0.9}
    ]
}

# OODA Cycle
with HeartbeatAgent(model_id="dionysus-agents") as agent:
    result = await agent.decide(context)

# Result structure:
# {
#   "reasoning": "User absent. Energy high. Focus: memory consolidation",
#   "actions": [
#     {"action": "consolidate_recent_memories", "params": {...}},
#     {"action": "prune_low_activation_basins", "params": {...}}
#   ],
#   "confidence": 0.85
# }
```

**OODA Breakdown**:
1. **OBSERVE**: Parse context (energy, user presence, goals)
2. **ORIENT**: "User absent + high energy = consolidation opportunity"
3. **DECIDE**: Select memory consolidation actions
4. **ACT**: Execute via MCP tools
5. **Next OBSERVE**: Check energy after actions, new context

### Example 3: Nested OODA Loops

**Scenario**: Writing marketing email (multi-timescale OODA)

```
MACRO OODA (Full Task):
└── OBSERVE: "Need to draft New Year email for Analytical Empaths"
    └── ORIENT: "Use identity transformation hook pattern"
        └── DECIDE: "Delegate to marketing agent with research context"
            └── ACT: Execute delegation
                └── MICRO OODA (Marketing Agent):
                    ├── OBSERVE: Load hook library, past performance data
                    ├── ORIENT: Select Identity Crisis hook, 6AM timing
                    ├── DECIDE: Draft structure with Before/After framing
                    └── ACT: Generate email copy
                        └── PLANNING INTERVAL (Step 4):
                            ├── OBSERVE: Email draft so far
                            ├── ORIENT: "Missing call-to-action clarity"
                            ├── DECIDE: Add explicit CTA paragraph
                            └── ACT: Insert CTA, finalize

Result: Nested loops at different abstraction levels
- Macro: Full task delegation
- Micro: Agent execution with replanning
- Planning interval: Self-correction within micro loop
```

### Example 4: OODA Speed Competition

**Clinical Application**: Hypervigilance vs Meta-Recognition

```
Threat-Detection OODA (Analytical Empath Default):
- OBSERVE: Ambiguous social cue (0.1s)
- ORIENT: Match to threat template (0.2s)
- DECIDE: Defensive posture (0.1s)
- ACT: Withdraw/attack (0.2s)
Total: 0.6s cycle time

Meta-Recognition OODA (Trained):
- OBSERVE: Ambiguous cue + internal state (0.1s)
- ORIENT: "This is Basin #2 activating" (0.3s)
- DECIDE: "I can choose not to follow this pattern" (0.2s)
- ACT: Pause, clarify instead of react (0.5s)
Total: 1.1s cycle time

Paradox: Slower cycle wins
- Faster loop = trapped in defensive basin
- Slower loop = meta-cognitive override
- Key: Recognizing you're IN an OODA loop
```

## Common Misconceptions

**Misconception 1**: "OODA is only for combat/competition"
**Reality**: OODA describes ANY decision cycle. You're running OODA loops constantly—reading this sentence is an OODA cycle (observe words → orient meaning → decide to continue → act by reading next sentence).

**Misconception 2**: "Faster OODA always wins"
**Reality**: Speed matters in competition, but **quality of orientation** matters more. A slow, accurate ORIENT beats a fast, wrong one. Meta-cognitive OODA (recognizing you're in a loop) can outmaneuver unconscious cycling.

**Misconception 3**: "OODA is linear: do one phase then move to next"
**Reality**: Phases overlap and can skip. You can jump from OBSERVE directly to ACT (reflex), or loop OBSERVE→ORIENT→OBSERVE (clarifying before deciding). The cycle is a rhythm, not a rigid sequence.

**Misconception 4**: "OODA replaces other decision frameworks"
**Reality**: OODA is a **descriptor**, not a prescription. It describes what you're already doing. Other frameworks (active inference, thoughtseed competition) explain *how* each phase works internally.

**Misconception 5**: "One OODA loop per person"
**Reality**: You run **multiple parallel OODA loops** at different timescales (micro: word-by-word reading, meso: paragraph comprehension, macro: learning from entire document). Loops nest and interact.

## When to Use

✅ **Use this concept when**:
- Designing autonomous agent architectures
- Explaining continuous decision-making under uncertainty
- Debugging reactive behavior patterns (clinical or technical)
- Implementing adaptive systems that learn from outcomes
- Teaching situational awareness and adaptive planning
- Structuring hierarchical agent orchestration

❌ **Don't use when**:
- One-shot decisions with no feedback loop
- Static analysis without action (use pure reasoning instead)
- Explaining unconscious reflexes (too fast for OODA)
- Planning without execution (ORIENT without ACT)

## OODA in Active Inference

### Free Energy Minimization

Each OODA phase minimizes free energy (prediction error):

```
OBSERVE: Gather sensory evidence
    ↓
ORIENT: Update beliefs to match observations
    Free Energy = Complexity - Accuracy
    ↓
DECIDE: Select action that minimizes expected free energy
    Expected F = Epistemic value + Pragmatic value
    ↓
ACT: Execute action, generate new observations
    ↓
Next OBSERVE: Measure prediction error (surprise)
```

### Precision Weighting

**Code**: From `api/services/metaplasticity_service.py`

```python
# OODA outcome adjusts precision for next cycle
surprise_level = 1.0 - confidence

# High surprise → lower precision → explore more
# Low surprise → higher precision → exploit current model
new_precision = metaplasticity_svc.update_precision_from_surprise(
    agent_name,
    surprise_level
)
```

**Mechanism**:
- **Low surprise** (prediction correct): Increase precision, trust current ORIENT
- **High surprise** (prediction wrong): Decrease precision, explore alternative ORIENTs
- This is **metaplasticity**: Learning how to learn from OODA outcomes

## OODA vs Other Frameworks

| Framework | Relationship to OODA | Key Difference |
|-----------|---------------------|----------------|
| **Active Inference** | OODA is the cycle; Active Inference is the physics | Active Inference explains *why* ORIENT updates (free energy) |
| **Thoughtseed Competition** | Happens during ORIENT→DECIDE | Multiple OODA loops (thoughtseeds) compete in parallel |
| **MOSAEIC** | OBSERVE phase captures MOSAEIC | MOSAEIC is snapshot; OODA is continuous |
| **Attractor Basin** | ORIENT activates basins; ACT strengthens them | Basin = stable state; OODA = transition dynamics |
| **Planning Interval** | Periodic ORIENT within ACT phase | Meta-OODA: loop within a loop |

## Historical Context

### Origin: John Boyd (Fighter Pilot)

- **1950s-60s**: Boyd analyzed Korean War dogfights
- **Key Insight**: Winner isn't fastest plane—it's pilot with fastest OODA cycle
- **"Getting inside opponent's loop"**: Your ACT happens before their DECIDE
- **Extension**: Applied to business strategy, therapy, military doctrine

### Dionysus Implementation

- **2024**: Spec 033 - Smolagents standardization
- **2024**: Spec 039 - OODA loop with planning_interval
- **2025**: Heartbeat agent implements autonomous OODA
- **2026**: Consciousness manager orchestrates multi-agent OODA

### Research Foundation

- Boyd, J. (1976). "Destruction and Creation"
- Boyd, J. (1995). "The Essence of Winning and Losing" (unpublished briefing)
- Friston, K. (2010). "Free-energy principle" - Active Inference connection
- Spec 039: Smolagents V2 Alignment (OODA implementation design)

## Advanced Topics

### OODA Hijacking (Clinical)

**Pattern**: External agent controls your OBSERVE phase

```
Abuser OODA:
- Manipulates what you OBSERVE (gaslighting)
- Your ORIENT based on false observations
- Your DECIDE follows their frame
- Your ACT serves their goals

Defense: Meta-OODA
- OBSERVE your OBSERVE process
- ORIENT to the manipulation pattern
- DECIDE to verify observations independently
- ACT to reclaim perceptual agency
```

### Computational Complexity

**OODA Scaling**:
```
Single loop: O(n) observations → O(n²) orientations → O(n) decisions
Nested loops: O(n^depth) where depth = nesting level
Parallel loops: O(n*agents) with synchronization overhead

Dionysus optimization:
- Planning interval: Amortize ORIENT cost across 3 ACT steps
- Basin activation: Cache frequent ORIENTations
- Memory pruning: Limit OBSERVE history to last 3 steps
```

### Self-Modifying OODA

**Code**: From `api/agents/consciousness_manager.py:305-312`

```python
# OODA outcome modifies next OODA parameters
surprise_level = 1.0 - confidence
adjusted_lr = metaplasticity_svc.calculate_learning_rate(surprise_level)
new_max_steps = metaplasticity_svc.calculate_max_steps(surprise_level)

# Update agents for next cycle
for agent in [perception, reasoning, metacognition]:
    agent.max_steps = new_max_steps
```

**Self-Evolution**: OODA loop that rewrites its own cycle parameters based on performance

## Further Reading

- **Research**:
  - Boyd, J. (1976). "Destruction and Creation" - Original OODA theory
  - Osinga, F. (2007). "Science, Strategy and War: The Strategic Theory of John Boyd"
  - Friston, K. (2010). "Free-energy principle" - Active Inference foundation

- **Documentation**:
  - [[01-metacognition-two-layer-model]] - Procedural metacognition as OODA regulator
  - [[05-thoughtseed-competition-explained]] - Competition during ORIENT→DECIDE
  - [[02-agency-and-altered-states]] - OODA reorganization in altered states

- **Implementation**:
  - `specs/039-smolagents-v2-alignment/spec.md` - OODA loop design specification
  - `api/agents/heartbeat_agent.py` - Top-level OODA implementation
  - `api/agents/consciousness_manager.py` - Multi-agent OODA orchestration

- **Blog/Essays**:
  - Chet Richards: "Boyd's OODA Loop" (available at dnipogo.org)
  - Grant Hammond: "The Mind of War: John Boyd and American Security"

---

**Author**: Dr. Mani Saint-Victor, MD
**Last Updated**: 2026-01-02
**Status**: Production
**Integration Event**: Smolagents V2 Alignment (039) → Autonomous Cognitive Decision Cycles
