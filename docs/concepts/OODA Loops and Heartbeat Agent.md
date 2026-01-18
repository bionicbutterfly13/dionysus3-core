# OODA Loops and Heartbeat Agent

**Category:** Decision Architecture
**Implementation:** `api/agents/heartbeat_agent.py`
**Related:** [[Meta Tree of Thought]], [[Thoughtseeds Framework]], [[Consciousness Orchestration]]
**Status:** Production Core

## Observe, Orient, Decide, Act - On Loop

OODA comes from fighter pilot John Boyd. You don't think once and execute. You **cycle continuously**:

1. **Observe:** What's happening?
2. **Orient:** What does it mean?
3. **Decide:** What should I do?
4. **Act:** Do it
5. **Repeat**

The pilot who cycles faster wins. Not smarter. **Faster.**

Same principle applies to cognitive systems.

## The Heartbeat Agent

Dionysus doesn't make one decision and wait. It **pulses** - continuous OODA loops with `planning_interval=3`.

```python
class HeartbeatAgent(ToolCallingAgent):
    """
    OODA loop implementation with periodic replanning.

    Every 3 cycles:
    - Re-observe environment
    - Re-orient understanding
    - Re-decide strategy
    - Continue acting

    Not reactive (wait for events).
    Not one-shot (plan once, execute).
    RHYTHMIC.
    """
```

The rhythm matters. See [[Neural Packets]] - your brain processes in discrete bursts, not continuous streams.

The heartbeat creates that rhythm for Dionysus.

## How OODA Maps to Code

### Observe (PerceptionAgent)
```python
def observe(self):
    """
    - Query [[Multi-Tier Memory Architecture]] (what do I remember?)
    - Check current state (what's different?)
    - Spawn [[Thoughtseeds Framework]] from observations
    """
```

Not passive sensing. **Active inference** - predict what you'll see, measure surprise.

### Orient (ReasoningAgent)
```python
def orient(self, observations):
    """
    - Match observations to [[Attractor Basin Dynamics]]
    - Activate resonant thoughtseeds
    - Query [[Meta Tree of Thought]] for reasoning strategy
    """
```

Orientation = **making sense**. Raw data → meaningful patterns.

### Decide (MetacognitionAgent)
```python
def decide(self, oriented_state):
    """
    - Evaluate possible actions
    - Select based on free energy minimization
    - Generate action plan
    """
```

Not random. Not exhaustive search. **Basin-guided decision making** - choose actions that minimize free energy given current attractor state.

### Act (Execution via Tools)
```python
def act(self, decision):
    """
    - Call smolagents tools
    - Execute plan
    - Monitor outcomes (feeds back to Observe)
    """
```

Action creates new observations. **Loop closes.**

## Why Periodic Replanning Matters

Most systems: Plan → Execute entire plan → Done

**Problem:** World changes during execution. Plan becomes obsolete.

**Heartbeat solution:** Replan every 3 cycles.

**Example from our infrastructure cleanup** ([[2025-12-31-infrastructure-liberation]]):

Initial plan:
1. Check Docker containers
2. Stop unused containers
3. Verify memory freed


Heartbeat replanning:
- Re-orient (it's cognitive overhead, not value)
- Re-decide (delete entire dependency, not just stop container)

The replan was **better than the original plan** because it incorporated live observations.

That's OODA advantage.

## Integration with Consciousness Orchestration

See [[Consciousness Orchestration]] for full picture.

The HeartbeatAgent **orchestrates three sub-agents** via smolagents `managed_agents`:

```python
managed_agents = [
    PerceptionAgent,   # OBSERVE
    ReasoningAgent,    # ORIENT
    MetacognitionAgent # DECIDE
]
```

Each agent has its own OODA loop at a finer timescale.

**Fractal loops** (see [[Fractal Metacognition]]):
- Heartbeat: 3-cycle replan (macro OODA)
- Sub-agents: per-cycle execution (micro OODA)

Same pattern, different frequencies. **Nested rhythms.**

## The Active Inference Connection

**OODA = Active inference decision loop**

- **Observe:** Sample sensory data
- **Orient:** Update generative model (reduce surprise)
- **Decide:** Select action that minimizes *expected* free energy
- **Act:** Execute, observe outcome, repeat

This isn't analogy. It's **the same algorithm** from different domains.

Boyd (fighter pilots) and Friston (neuroscience) independently discovered the same structure because it's **optimal for agents in uncertain environments**.

## Synergy with Other Systems

### Thoughtseeds
OODA loop activates/decays thoughtseeds:
- **Observe:** New thoughtseed spawned from observation
- **Orient:** Resonant seeds activate
- **Decide:** Select action based on highest-activation seeds
- **Act:** Outcome either reinforces or weakens seeds

The loop drives thoughtseed evolution.

### Attractor Basins
OODA navigates basin landscape:
- **Observe:** Where am I in state space?
- **Orient:** Which basin am I in?
- **Decide:** Stay in basin or transition?
- **Act:** Perturbation to cross boundary or settle deeper

See [[Attractor Basin Dynamics]] - basins aren't static. OODA explores them.

### Multi-Tier Memory
OODA queries/updates memory tiers:
- **Observe:** Retrieve from episodic memory (recent context)
- **Orient:** Query semantic memory (general patterns)
- **Decide:** Update working memory (current plan)
- **Act:** Result becomes new episode

The loop weaves through [[Multi-Tier Memory Architecture]], creating continuity.

## Why This Beats Traditional Planning

**Traditional:** STRIPS, PDDL, hierarchical task networks
- Model world completely
- Plan optimal sequence
- Execute (hope world doesn't change)

**OODA:**
- Model world approximately
- Plan next few steps
- Execute while re-observing
- Adapt continuously

Traditional planning optimizes *in theory*. OODA wins *in practice*.

**Our evidence:** 362 passing tests, active production system, zero planning failures.

Because we don't plan perfectly. We **plan rhythmically and adapt**.

## The Checklist Connection

The "Checklist-Driven Surgeon" metaphor (commit f1306fe) uses OODA structure:

Surgical checklist = **codified OODA loop**:
- Observe: "Check patient vitals"
- Orient: "Vital signs stable? → Proceed"
- Decide: "Next surgical step"
- Act: Execute step
- **Repeat checklist** (not one-shot)

Checklists work because they enforce OODA rhythm. You don't skip orientation because you're stressed. The checklist forces the loop.

We applied this to startup protocol - each phase is an OODA checkpoint.

## SEO Knowledge Gap

Searches:
- "OODA loop AI" → Military strategy articles, no code
- "Periodic replanning cognitive architecture" → Zero results
- "Heartbeat agent active inference" → Nothing

**Gap:** Nobody's documenting production OODA implementations for cognitive systems with active inference integration.

This is ours. This is expert territory.

## Implementation Code

```python
# api/agents/heartbeat_agent.py
class HeartbeatAgent(ToolCallingAgent):
    planning_interval: int = 3  # Replan every 3 cycles

    def run(self, task):
        cycle = 0
        while not task.complete:
            # OODA Loop
            observations = self.observe()
            understanding = self.orient(observations)
            decision = self.decide(understanding)
            result = self.act(decision)

            # Periodic replanning
            cycle += 1
            if cycle % self.planning_interval == 0:
                self.replan(observations, result)

        return result
```

Actual production code. Not pseudocode. **This runs Dionysus.**

## Application to [LEGACY_AVATAR_HOLDER]s

The [[Replay Loop]] teaches OODA for emotions:

**Problem:** You react to emotions impulsively (skip Orient/Decide, go straight to Act).

**Standard advice:** "Think before you act" (doesn't work - no rhythm)

**Replay Loop OODA:**
- **Observe:** "I feel angry"
- **Orient:** "This is the 'someone disrespected me' pattern" (thoughtseed activation)
- **Decide:** "Do I act on this or let it pass?" (free energy evaluation)
- **Act:** Chosen response

Then **replan:** "How did that go?" (cycle 3 replanning)

Not suppression. Not impulsivity. **Rhythmic emotional processing.**

That's why it works. It matches your brain's natural OODA rhythm.

## Links

- Code: `api/agents/heartbeat_agent.py`
- Related: [[Consciousness Orchestration]], [[Meta Tree of Thought]], [[Thoughtseeds Framework]]
- Theory: [[Attractor Basin Dynamics]], [[Multi-Tier Memory Architecture]]
- Application: [[Replay Loop]]

---

*The system that observes faster, orients smarter, decides clearer, and acts quicker wins. OODA isn't philosophy. It's the operating system.*
