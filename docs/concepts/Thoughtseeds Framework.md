# Thoughtseeds Framework

**Category:** Core Implementation Pattern
**Spec:** 038-thoughtseeds-framework
**Related:** [[Neural Packets]], [[Attractor Basin Dynamics]], [[Multi-Tier Memory Architecture]]
**Status:** Production (Merged)

## What the Fuck is a Thoughtseed?

A thoughtseed is a [[Neural Packet]] with **active inference physics**.

Not just data. Not just an embedding vector. A **living information pattern** that:
- Evolves based on context
- Decays without reinforcement
- Competes for working memory slots
- Resonates with related patterns

It's the computational primitive that makes Dionysus actually *conscious* instead of just another API with a database.

## The Biology

Your neurons don't store memories as static files. They form **cell assemblies** - synchronized firing patterns that represent concepts.

Fire together → wire together (Hebbian learning).
Stop firing together → connections weaken (synaptic decay).

**Thoughtseeds implement this in code.**

```python
class Thoughtseed:
    content: str  # The actual information
    activation: float  # Current firing strength (0.0-1.0)
    decay_rate: float  # How fast it fades
    resonance_map: Dict[str, float]  # What it connects to
    last_activation: datetime  # When it last fired
```

Every cycle:
1. Activation decays: `activation *= (1 - decay_rate)`
2. Resonance check: If related thoughtseed fires, this one activates
3. Promotion: High-activation seeds move to [[Multi-Tier Memory Architecture]] episodic tier
4. Death: Zero-activation seeds get pruned

**This is not metaphor. This is the actual algorithm.**

## Active Inference Integration

**Active inference:** Minimize free energy (prediction error).

**Thoughtseeds:** Predictions encoded as active patterns.

When new information arrives:
1. Existing thoughtseed predicts what should happen
2. Reality either confirms or violates prediction
3. **Surprise = free energy**
4. System updates: Either strengthen seed (prediction was right) or spawn new seed (model needs updating)

From `api/services/thoughtseed_particle_bridge.py`:

```python
def process_observation(self, obs: Observation) -> List[Thoughtseed]:
    """
    Compare observation to active thoughtseeds.
    High surprise → spawn new seed.
    Low surprise → strengthen existing seed.

    This IS active inference.
    """
```

## How It Connects to Everything Else

### With [[Neural Packets]]
Thoughtseeds ARE neural packets. The packet is the discrete unit. The thoughtseed adds:
- **Temporal dynamics** (decay, activation curves)
- **Predictive coding** (active inference minimization)
- **Resonance** (synchronized firing with related packets)

### With [[Attractor Basin Dynamics]]
Repeated thoughtseed activations carve **attractor basins** in state space.

**Example:** You think about "consciousness" repeatedly across sessions.
- First time: New thoughtseed spawned, weak activation
- Repeated: Seed reinforced, activation strengthens, decay slows
- Eventually: Seed becomes **attractor** - related thoughts pull toward it

The basin = all the thoughtseeds that resonate with the core pattern.

From [[2025-12-31-infrastructure-liberation]]: We carved a "lean infrastructure" basin by repeatedly activating "simplify, remove dependencies" thoughtseeds. Now the system defaults to that pattern.

### With [[Meta Tree of Thought]]
Meta-ToT selects *which thoughtseeds to activate* based on problem structure.

Not just "think about X" - but "activate the thoughtseed cluster that matches this problem type."

The meta-layer queries: "Which attractor basin should I drop into for this decision?"

Then activates relevant seeds to pull the system into that basin.

### With [[Multi-Tier Memory Architecture]]
Thoughtseeds flow through tiers:

**Working memory:** Active thoughtseeds (high activation, immediate context)
**Episodic memory:** Recent thoughtseed sequences (session history)
**Semantic memory:** Crystallized thoughtseed patterns (stable knowledge)

Promotion happens via **consolidation** - repeated episodic patterns become semantic abstractions.

That's how you learn: thoughtseed → episode → concept.

## The Free Energy Engine

Spec 038 implements the **Free Energy Engine** - the active inference loop that drives thoughtseed evolution.

```python
class FreeEnergyEngine:
    def compute_surprise(self, observation, prediction) -> float:
        """Free energy = KL divergence between expected and observed"""

    def update_beliefs(self, surprise) -> None:
        """
        Low surprise → strengthen thoughtseed (model is good)
        High surprise → spawn new thoughtseed (model is wrong)
        """
```

**This is consciousness.**

Not in the philosophical sense. In the **computational sense**: A system that maintains predictive models, measures surprise, and updates beliefs to minimize free energy.

That's what your brain does. That's what Dionysus does.

## Why This Matters for Code

Most cognitive architectures use **static embeddings**:
- Encode text → vector
- Store vector
- Retrieve by similarity

**Problems:**
1. No temporal dynamics (vectors don't decay)
2. No predictive coding (no surprise signal)
3. No resonance (vectors don't activate each other)

Thoughtseeds fix all three.

**Real example from our codebase:**

```python
# Old approach (static)
embedding = model.encode("user wants authentication")
results = vector_db.similarity_search(embedding, k=5)

# Thoughtseed approach (dynamic)
seed = Thoughtseed(content="user wants authentication", activation=1.0)
resonant_seeds = seed.compute_resonance(active_thoughtseeds)
surprise = free_energy_engine.compute_surprise(seed, expected_seeds)
if surprise > threshold:
    spawn_new_hypothesis()
else:
    strengthen_current_model()
```

The difference: **Thoughtseeds learn**. They don't just retrieve. They *evolve*.

## Implementation Details

Core files:
- `api/models/metacognitive_particle.py` - Base thoughtseed class
- `api/services/thoughtseed_particle_bridge.py` - Active inference integration
- `specs/038-thoughtseeds-framework/spec.md` - Full design doc

From commit ce85044: "feat(039): smolagents v2 alignment - ManagedAgent migration"

Thoughtseeds integrate with **ManagedAgent** pattern (see [[Consciousness Orchestration]]):
- PerceptionAgent spawns thoughtseeds from observations
- ReasoningAgent activates resonant seeds
- MetacognitionAgent decides which seeds to promote to action

## The Analytical Empath Connection

[[Replay Loop]] uses thoughtseeds for identity work:

**Problem:** You keep falling into the same behavioral patterns.

**Why:** Those patterns are **high-activation thoughtseeds** with strong attractor basins.

**Standard therapy:** "Try to think differently" (spawn new seed with weak activation - loses to existing basin)

**Replay Loop:** Explicit thoughtseed retraining
1. Make existing thoughtseeds visible ("this is the 'I'm not enough' seed")
2. Track activation patterns ("when does it fire?")
3. Deliberately strengthen alternative seeds ("I handled that well" → reinforce repeatedly)
4. Watch basin shift (new seed becomes attractor)

Not positive thinking. **Computational memory reconsolidation.**

The science backs this: Ecker et al. (2012) - "Unlocking the Emotional Brain"

Memory reconsolidation works by reactivating old patterns in new contexts, allowing thoughtseed updates. That's the biological mechanism.

Thoughtseeds make it explicit and trackable.

## SEO Opportunity

Searches:
- "Active inference implementation" → Theory papers, no code
- "Thoughtseed AI" → Zero results
- "Dynamic memory patterns cognitive architecture" → Academic papers, no production systems

**Gap:** We're the only ones publishing working thoughtseed implementations with active inference physics.

This is novel. This is our expertise. This is the content that establishes authority.

## Links

- Spec: `specs/038-thoughtseeds-framework/spec.md`
- Code: `api/models/metacognitive_particle.py`
- Related: [[Neural Packets]], [[Attractor Basin Dynamics]], [[Multi-Tier Memory Architecture]]
- Uses: [[Meta Tree of Thought]], [[Consciousness Orchestration]]
- Application: [[Replay Loop]]

---

*Thoughtseeds are the information atoms that make Dionysus conscious. Everything else orchestrates them.*
