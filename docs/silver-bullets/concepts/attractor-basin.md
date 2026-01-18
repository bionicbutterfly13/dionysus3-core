# Attractor Basin

**Category**: Core Concept
**Type**: Cognitive Pattern
**Implementation**: `api/services/memory_basin_router.py`, `api/agents/callbacks/basin_callback.py`

---

## Definition

An **attractor basin** is a stable mental state that captures and holds your thoughts, like a valley that catches and keeps a rolling ball. Once your mind enters a basin, it naturally stays there until sufficient energy pushes it out.

Think of it as a **valley in a landscape of possible thoughts**—your mental state gravitates toward the bottom and resists leaving.

## Key Characteristics

- **Stability**: Once entered, the basin maintains itself without effort
- **Attraction**: Nearby mental states naturally flow into the basin
- **Energy Barrier**: Requires activation energy to escape the basin
- **Self-Reinforcing**: Actions within the basin strengthen the basin
- **Unconscious**: You don't choose which basin you're in—initial conditions determine it
- **Fractal**: Basins nest within larger basins (micro, meso, macro scales)

## How It Works

### The Valley Metaphor

```
    [Mountain Peak] - High Free Energy
         /\
        /  \
       /    \
      /      \     [Shallow Basin]
     /        \___/  ← Easily escaped
    /
   /         [Deep Basin]
  /         /      \___
 /         /           \____  ← Stable, hard to escape
/__________________________________
         [Energy Landscape]
```

### Step-by-Step Process

1. **Initial State**: Your mind exists in some current mental state (a point on the landscape)
2. **Perturbation**: New information or thought arrives (small push to the ball)
3. **Within-Basin Response**: If perturbation is small, you settle back to the attractor
4. **Basin Transition**: If perturbation crosses the basin boundary, you fall into a new basin
5. **Stabilization**: The new basin captures your thoughts and becomes self-reinforcing

### Visual Representation

```
Ball = Current Mental State
Valley Depth = Basin Stability
Height = Free Energy

Example: Problem-Solving Basin

        Confusion         Normal           Flow
           /\              /\              /\
          /  \            /  \            /  \
         /    \          /    \          /    \
    F=4.0      \    F=2.5      \    F=1.2      \___
               ↓               ↓                    \____
         [Unstable]      [Moderate]            [Deep Stable]

Your mind naturally rolls toward lower energy states (deeper valleys).
```

## Implementation

### Memory Basin Router

**Code**: `api/services/memory_basin_router.py:22-51`

Maps memory types to specialized basins:
- **experiential-basin** - Episodic memories (time-tagged experiences)
- **conceptual-basin** - Semantic knowledge (facts, relationships)
- **procedural-basin** - Skills and how-to knowledge
- **strategic-basin** - Planning and decision frameworks

Each basin has:
- `strength` - Depth of the basin (stability)
- `activation_count` - How often it's been entered
- `stability` - Resistance to displacement
- `concepts` - Core ideas that define the basin

```python
# From memory_basin_router.py:197-226
create_cypher = """
MERGE (b:AttractorBasin {name: $name})
ON CREATE SET
    b.strength = $strength,
    b.stability = 0.5,
    b.activation_count = 1
ON MATCH SET
    b.strength = CASE
        WHEN b.strength < 2.0 THEN b.strength + 0.05
        ELSE b.strength
    END,
    b.activation_count = b.activation_count + 1
"""
```

### Basin Activation Callback

**Code**: `api/agents/callbacks/basin_callback.py:37-106`

When agents perform semantic recall:
1. Extract query from tool call
2. Find basins related to query (keyword matching)
3. Activate basins (increase `current_activation`)
4. Strengthen connections between co-activated basins (Hebbian learning)

```python
# Hebbian strengthening: neurons that fire together wire together
# From basin_callback.py:86-99
if len(activated) >= 2:
    await session.run("""
        MATCH (b1:MemoryCluster {id: b1_id})
        MATCH (b2:MemoryCluster {id: b2_id})
        MERGE (b1)-[r:CO_ACTIVATED]->(b2)
        SET r.count = r.count + 1,
            r.strength = r.strength + 0.05
    """)
```

### Tests

- **Integration**: `tests/integration/test_metacognition_semantic_storage.py`
- **Unit**: `tests/unit/test_graphiti_extraction.py`

## Related Concepts

**Prerequisites** (understand these first):
- [[free-energy]] - Metric that determines basin depth
- [[thoughtseed]] - Competing hypotheses before basin formation

**Builds Upon** (this uses):
- [[prediction-error]] - Basin stability depends on prediction accuracy
- [[active-inference]] - Basins are low free-energy states

**Used By** (depends on this):
- [[basin-transition]] - Shifts between attractor basins
- [[basin-stability]] - Resistance to leaving a basin
- [[thoughtseed-competition]] - Winner becomes an attractor basin
- [[metacognitive-feelings]] - Generated during basin transitions

**Related** (similar or complementary):
- [[selective-attention]] - Basins determine what receives attention
- [[declarative-metacognition]] - Knowledge stored in semantic basins
- [[procedural-metacognition]] - Skills stored in procedural basins

## Examples

### Example 1: Hypervigilance Basin

**Clinical Context**: [LEGACY_AVATAR_HOLDER] stuck in threat-detection mode

```
Basin Properties:
- Name: "threat-detection-basin"
- Strength: 2.8 (very deep, highly stable)
- Core prediction: "Threat is likely"
- Activation pattern: Ambiguous cues → interpreted as threats

Self-Reinforcement Loop:
1. Scan environment for threats
2. Find ambiguous social cue
3. Interpret as threat (to minimize surprise)
4. Defensive response
5. Others react defensively
6. Confirms "threat was real" → strengthens basin
```

**Escape Strategy**: Meta-recognition creates boundary crossing
- "This is Basin #2, the hypervigilance pattern"
- Naming the basin shifts relationship to it
- You're no longer the valley—you're the ball that sees the valley

### Example 2: Problem-Solving Basin

**Code**: From `api/agents/callbacks/basin_callback.py:58-74`

```python
# Debugging session activates problem-solving basin
query = "Why is the test failing?"

activated_basins = await _activate_related_basins(query)
# Returns:
# [
#   {"name": "debugging-basin", "activation": 0.85, "state": "active"},
#   {"name": "test-analysis-basin", "activation": 0.72, "state": "activating"}
# ]

# Basin properties guide attention:
# - Focus on: code changes, test fixtures, error messages
# - Ignore: unrelated features, optimization ideas
# - Persist: until test passes or clear blocker identified
```

### Example 3: Infrastructure Liberation

**Real-World**: From `docs/journal/2025-12-31-infrastructure-liberation.md`

```
Before Basin:
- Attractor: "More tools = more capability"
- State: Complex orchestration, heavy infrastructure
- Activation energy: High (4GB RAM, many dependencies)

Transition Event: `docker stop $(docker ps -q)`

After Basin:
- Attractor: "Less tooling = more velocity"
- State: Core API, lean dependencies
- Activation energy: Low (minimal infrastructure)

Result: Phase transition, not gradual improvement
- 4GB RAM freed
- New stable equilibrium
- Cannot easily return to old basin (high activation barrier)
```

## Common Misconceptions

**Misconception 1**: "I can just choose to think differently"
**Reality**: You can't willpower your way out of a basin. You're already in it. You need to recognize the basin structure and find the boundary-crossing perturbation.

**Misconception 2**: "Attractor basins are bad and I should avoid them"
**Reality**: Basins provide cognitive efficiency. The problem isn't basins—it's being stuck in the *wrong* basin for the current context.

**Misconception 3**: "Once in a basin, I'm trapped forever"
**Reality**: Basins have varying depths. Shallow basins are easily escaped. Deep basins require larger perturbations but can still transition with sufficient activation energy.

**Misconception 4**: "Basin transitions are always gradual"
**Reality**: Transitions can be phase shifts—sudden, discontinuous jumps to new stable states (like the infrastructure liberation example).

## When to Use

✅ **Use this concept when**:
- Explaining why certain thought patterns persist
- Designing interventions for stuck mental states (therapy, coaching)
- Understanding consciousness continuity across sessions
- Implementing memory routing systems
- Creating self-reinforcing cognitive loops

❌ **Don't use when**:
- Explaining single, isolated thoughts (use [[thoughtseed]] instead)
- Rapid task-switching without persistent focus
- Shallow processing without attentional depth
- Random exploration without convergence

## Basin Lifecycle

### Formation
```python
# Thoughtseed wins competition → creates basin
winner = min(thoughtseeds, key=lambda s: s.free_energy)

# Basin depth determined by free energy
basin_depth = 1.0 / winner.free_energy  # Lower F → deeper basin
```

### Strengthening
```python
# Each activation strengthens the basin
# From memory_basin_router.py:208-214
ON MATCH SET
    b.strength = CASE
        WHEN b.strength < 2.0 THEN b.strength + 0.05
        ELSE b.strength
    END,
    b.activation_count = b.activation_count + 1
```

### Transition
```python
# Perturbation crosses boundary when:
delta_F = new_observation.free_energy - current_basin.free_energy

if delta_F > activation_threshold:
    # Basin transition
    current_basin = new_basin
```

### Decay
```python
# Unused basins weaken over time
# From api/services/graphiti_service.py (TTL-based pruning)
if basin.last_activated > 30_days_ago and basin.strength < 0.5:
    # Basin decays, becomes easier to escape
    basin.stability -= 0.1
```

## Physics Foundation

### Dynamical Systems Theory

- **State space**: All possible mental configurations
- **Attractor**: Stable configuration the system settles into
- **Basin of attraction**: Region of state space that flows toward the attractor
- **Trajectory**: Path through state space over time

### Free Energy Principle

From Karl Friston's active inference:
- Systems minimize variational free energy
- Attractor basins = low free-energy states
- Basin depth ∝ prediction accuracy
- Self-reinforcing: Actions confirm predictions → lower surprise → deeper basin

### Research Foundation

- Kelso (1995): "Dynamic Patterns: The Self-Organization of Brain and Behavior"
- Friston (2010): "The free-energy principle: a unified brain theory?"
- Spec 038: Thoughtseeds Framework (attractor basin implementation)

## Further Reading

- **Research**: Friston, K. (2010). Free-energy principle. Scholarpedia, 5(2), 6314
- **Documentation**:
  - [[01-metacognition-two-layer-model]] - Theoretical foundation
  - [[05-thoughtseed-competition-explained]] - Competition → basin formation
  - [[02-agency-and-altered-states]] - Basin reorganization via psychedelics
- **Implementation**:
  - `docs/concepts/Attractor Basin Dynamics.md` - Extended explanation
  - `.specify/features/038-thoughtseeds-framework/spec.md` - Design spec
- **Real-world example**:
  - `docs/journal/2025-12-31-infrastructure-liberation.md` - Phase transition case study

---

**Author**: Dr. Mani Saint-Victor, MD
**Last Updated**: 2026-01-02
**Status**: Production
**Integration Event**: Thoughtseeds Framework (038) → Dionysus Cognitive Architecture
