# Thoughtseed

**Category**: Core Concept  
**Type**: Cognitive Unit  
**Implementation**: Meta-ToT MCTS Nodes + Active Inference

---

## Definition

A **thoughtseed** is a candidate hypothesis competing for conscious attention. It represents a potential "next thought" that could become conscious if it wins the competition.

Think of it as a **seed** that could grow into a full conscious thought if given sufficient energy and attention.

## Key Characteristics

- **Parallel Generation**: Multiple thoughtseeds exist simultaneously
- **Unconscious Initially**: Generated below conscious awareness
- **Energy-Based**: Each has an activation energy (free energy value)
- **Competitive**: Competes with other thoughtseeds for limited attention
- **Noetic**: Winning thoughtseed generates a felt experience ("Aha!" or confusion)
- **Transient**: Can be quickly displaced by new thoughtseeds

## What Makes a Thoughtseed?

### Structure
```python
class Thoughtseed:
    hypothesis: str              # The potential thought content
    free_energy: float           # F = Complexity - Accuracy  
    activation_level: float      # Current strength/salience
    source: str                  # Where it came from
    timestamp: datetime          # When generated
    metadata: Dict               # Context, provenance, etc.
```

### Properties
- **Hypothesis**: The actual content (e.g., "Use JWT for authentication")
- **Free Energy (F)**: Combined measure of complexity and accuracy
  - Lower F = more likely to win
  - F = Complexity - Accuracy
  - Winning threshold typically F < 1.5
- **Activation Level**: How "loud" the thoughtseed is competing
- **Provenance**: Where it came from (perception, memory, reasoning)

## Thoughtseed Lifecycle

```
1. GENERATION (Unconscious)
    ↓
    Multiple thoughtseeds created in parallel
    Sources: Meta-ToT MCTS, memory retrieval, pattern matching
    ↓
2. COMPETITION (Unconscious)
    ↓
    Each thoughtseed evaluated on free energy
    Prediction errors influence activation levels
    ↓
3. SELECTION (Transition to Conscious)
    ↓
    Thoughtseed with lowest free energy wins
    Generates metacognitive feeling during transition
    ↓
4. BASIN FORMATION (Conscious)
    ↓
    Winning thoughtseed creates attractor basin
    Becomes the current conscious content
    ↓
5. PERSISTENCE OR DISPLACEMENT
    ↓
    Deep basin: Persists (minutes to hours)
    Shallow basin: Quickly displaced by new thoughtseed
```

## Dionysus Implementation

### Generation (Meta-ToT MCTS)
```python
# Meta-Tree-of-Thought generates thoughtseeds via Monte Carlo Tree Search
meta_tot_engine = MetaToTEngine()

# Generate multiple candidate solutions
thoughtseeds = await meta_tot_engine.generate_candidates(
    problem="How to implement authentication?",
    num_candidates=5  # Generate 5 competing thoughtseeds
)

# Example output:
# thoughtseeds = [
#     {"hypothesis": "Use JWT tokens", "free_energy": 1.2},
#     {"hypothesis": "Use session cookies", "free_energy": 2.1},
#     {"hypothesis": "Use OAuth2", "free_energy": 3.5},
#     {"hypothesis": "Use magic links", "free_energy": 2.8},
#     {"hypothesis": "Use passwordless", "free_energy": 1.9}
# ]
```

### Competition (Free Energy Evaluation)
```python
# Active Inference evaluates each thoughtseed
from api.services.efe_engine import EFEEngine

efe_engine = EFEEngine()

for seed in thoughtseeds:
    # Calculate Expected Free Energy
    seed.free_energy = efe_engine.calculate_efe(
        hypothesis=seed.hypothesis,
        context=current_context,
        observations=recent_observations
    )
```

### Selection (Metacognition Agent)
```python
# HeartbeatAgent's Metacognition phase selects winner
winner = min(thoughtseeds, key=lambda s: s.free_energy)

# Generate metacognitive feeling based on energy change
delta_F = previous_energy - winner.free_energy

if delta_F < -2.0:
    feeling = "Aha!"  # Large sudden drop
elif winner.free_energy > 3.0:
    feeling = "Confusion"  # Energy stays high
elif winner.free_energy < 1.5:
    feeling = "Flow"  # Stable low energy
```

## Examples

### Example 1: Problem-Solving
**Situation**: Debugging a failing test

**Thoughtseeds Generated**:
1. "Check test fixtures" (F=1.8)
2. "Review recent code changes" (F=1.3) ← **WINS**
3. "Restart test environment" (F=2.5)
4. "Check database state" (F=2.2)

**Winner**: "Review recent code changes" (lowest free energy)
**Feeling**: Gradual understanding (ΔF = -0.5)

### Example 2: Insight Moment
**Situation**: Reading about metacognition

**Thoughtseeds Competing**:
1. "This is about thinking about thinking" (F=2.8)
2. "Thoughtseeds ARE metacognitive feelings!" (F=0.9) ← **WINS**
3. "I should take notes" (F=3.2)

**Winner**: "Thoughtseeds ARE metacognitive feelings!"
**Feeling**: **Aha!** moment (ΔF = -2.4, large sudden drop)

## Ball-and-Hill Analogy

Imagine each thoughtseed as a **ball on a hillside**:
- **Height** = Free energy (activation cost)
- **Balls roll downhill** naturally (toward lower energy)
- **Lowest valley** = Winning thoughtseed
- **Deep valley** = Stable idea (hard to displace)
- **Shallow valley** = Fleeting thought (easily displaced)

```
    [High Energy]
         🔴 Thoughtseed 3 (F=3.5)
        /  \
       /    \
      /      \  🔵 Thoughtseed 2 (F=2.1)
     /        \/
    /          \
[Mountain]    [Valley] 🟢 Thoughtseed 1 (F=1.2) ← WINNER
                        (Deep basin, stable)
```

## Thoughtseed vs Attractor Basin

| Aspect | Thoughtseed | Attractor Basin |
|--------|-------------|-----------------|
| **State** | Candidate (competing) | Winner (established) |
| **Consciousness** | Unconscious (pre-selection) | Conscious (post-selection) |
| **Duration** | Milliseconds | Seconds to hours |
| **Energy** | Variable (competing) | Stable (minimum achieved) |
| **Analogy** | Ball rolling | Ball settled in valley |

**Relationship**: A thoughtseed becomes an attractor basin when it wins the competition.

## Sources of Thoughtseeds

### 1. Meta-ToT MCTS
- Systematic exploration of solution space
- Tree search with active inference heuristics
- Generates multiple candidate strategies

### 2. Memory Retrieval
- Recalled patterns from past episodes
- Semantic associations from knowledge graph
- Procedural habits from HOT tier

### 3. Perception
- Bottom-up sensory input
- Environmental affordances
- Prediction errors

### 4. Reasoning
- Logical inference
- Analogical mapping
- Counterfactual simulation

## Why Multiple Thoughtseeds?

### Evolutionary Advantage
- **Parallel processing**: Evaluate many options simultaneously
- **Flexibility**: Ready to switch if environment changes
- **Robustness**: If one fails, others available
- **Exploration**: Discover novel solutions

### Computational Efficiency
- Generate cheap hypotheses unconsciously
- Only commit resources to winner
- Avoids premature optimization
- Maintains option value

## Related Concepts

- **[Thoughtseed Competition](./thoughtseed-competition.md)** - How selection works
- **[Free Energy](./free-energy.md)** - Selection criterion
- **[Attractor Basin](./attractor-basin.md)** - Stable outcome state
- **[Metacognitive Feelings](./metacognitive-feelings.md)** - Subjective experience
- **[Meta-ToT](./meta-tot.md)** - Generation mechanism

## Bidirectional Links

### This concept is referenced in:
- [05-thoughtseed-competition-explained.md](../05-thoughtseed-competition-explained.md)
- [01-metacognition-two-layer-model.md](../01-metacognition-two-layer-model.md)
- [Thoughtseed Competition](./thoughtseed-competition.md)

### This concept references:
- [Free Energy](./free-energy.md)
- [Attractor Basin](./attractor-basin.md)
- [Meta-ToT](./meta-tot.md)

---

**Author**: Dr. Mani Saint-Victor  
**Last Updated**: 2026-01-01  
**Integration Event**: Metacognition Framework → Dionysus Architecture
