# Thoughtseed Competition

**Category**: Core Concept
**Type**: Process
**Implementation**: `api/services/efe_engine.py`, `api/services/meta_tot_engine.py`, `api/models/meta_tot.py`

---

## Definition

**Thoughtseed competition** is the unconscious process by which multiple candidate hypotheses (thoughtseeds) compete for limited conscious attention through free energy minimization. The thoughtseed with the lowest free energy wins and becomes the current conscious content.

This is not a metaphor—the computational process of parallel evaluation and winner-take-all selection IS what we experience as selective attention and thought formation.

## Competition Mechanism

### Step-by-Step Process

1. **Parallel Generation** (Unconscious)
   - Multiple thoughtseeds created simultaneously from different sources
   - Sources: Meta-ToT MCTS, memory retrieval, perception, reasoning
   - All thoughtseeds exist below conscious awareness
   - Each represents a potential "next thought"

2. **Free Energy Evaluation** (Unconscious)
   - Each thoughtseed assigned a free energy score: `F = Complexity - Accuracy`
   - Lower F indicates better hypothesis (simpler + more accurate)
   - Evaluation uses EFE Engine with precision weighting
   - Formula: `EFE = (1/Precision) * Uncertainty + Precision * Divergence`

3. **Winner-Take-All Selection** (Transition Point)
   - Thoughtseed with minimum F wins competition
   - Winner crosses threshold from unconscious to conscious
   - Threshold typically F < 1.5 for stable selection
   - Generates metacognitive feeling based on ΔF (energy change)

4. **Basin Formation** (Conscious)
   - Winning thoughtseed creates attractor basin
   - Basin depth proportional to inverse of F (deeper = lower energy)
   - Stable basin persists as conscious content
   - Shallow basins quickly displaced by new competition

5. **Continuous Cycling** (OODA Loop)
   - Competition repeats every few seconds
   - New observations trigger new thoughtseed generation
   - Previous winner can be displaced if new thoughtseed has lower F
   - Process runs continuously during waking consciousness

### Visual Representation

```
        UNCONSCIOUS COMPETITION

    ⬤ Thoughtseed A (F=3.5)     [High Energy - Unlikely]
       /
      /
     /   ⬤ Thoughtseed B (F=2.1) [Medium Energy - Possible]
    /      \
   /        \
  /          \  ⬤ Thoughtseed C (F=1.2) [Low Energy - WINNER]
 /            \/
/              \  ← Conscious Threshold (F ≈ 1.5)
───────────────────────────────────────────────────
         CONSCIOUS AWARENESS

         🎯 Thoughtseed C wins
         Forms attractor basin
         Becomes current thought
```

**Energy landscape interpretation**:
- Height = Free energy (F)
- Valleys = Low energy states (stable)
- Peaks = High energy states (unstable)
- Balls naturally "roll downhill" toward lower F
- Deepest valley = Winner

## Selection Criteria

### Primary Criterion: Free Energy (F)

**Formula**: `F = Complexity - Accuracy`

**Components**:
- **Complexity**: Cognitive cost to maintain hypothesis
  - Number of assumptions
  - Processing requirements
  - Memory demands
  - Information content

- **Accuracy**: Predictive power of hypothesis
  - P(observations | beliefs)
  - Reduction in prediction error
  - Goal alignment
  - Explanatory coherence

**Thresholds**:
- **F < 1.0**: Strong candidate (very likely to win)
- **F < 1.5**: Viable candidate (stable if selected)
- **F = 1.5-3.0**: Weak candidate (unlikely to win)
- **F > 3.0**: Poor candidate (triggers confusion, generates new competition)

### Precision Weighting (Feature 048)

Competition can be modulated by **precision** (confidence):

```python
# Standard EFE
EFE = Uncertainty + Divergence

# Precision-weighted EFE
EFE = (1/Precision) * Uncertainty + Precision * Divergence
```

**Effects**:
- **High precision** (confident): Emphasize goal-seeking, de-emphasize exploration
- **Low precision** (uncertain): Emphasize exploration, de-emphasize goal commitment
- **Adaptive modulation**: Metacognitive feelings adjust precision dynamically

**Implementation**: `api/services/efe_engine.py:61-84`

## Implementation

### Core Selection Logic

**File**: `api/services/efe_engine.py:103-133`

```python
def select_dominant_thought(
    self,
    candidates: List[Dict[str, Any]],
    goal_vector: List[float],
    precision: float = 1.0
) -> EFEResponse:
    """
    Winner-take-all selection of the dominant ThoughtSeed
    based on minimal EFE.
    """
    if not candidates:
        return EFEResponse(dominant_seed_id="none", scores={})

    results = {}
    goal_vec = np.array(goal_vector)

    for candidate in candidates:
        seed_id = candidate.get("id")
        probs = candidate.get("probabilities", [0.5, 0.5])
        thought_vec = np.array(candidate.get("vector", [0.0]*len(goal_vector)))

        # Calculate EFE for this thoughtseed
        efe = self.calculate_efe(probs, thought_vec, goal_vec, precision)

        results[seed_id] = EFEResult(
            seed_id=seed_id,
            efe_score=efe,
            uncertainty=self.calculate_entropy(probs),
            goal_divergence=self.calculate_goal_divergence(thought_vec, goal_vec)
        )

    # Select dominant seed (minimum EFE)
    dominant_seed_id = min(results, key=lambda k: results[k].efe_score)

    return EFEResponse(
        dominant_seed_id=dominant_seed_id,
        scores=results
    )
```

### Meta-ToT MCTS Integration

**File**: `api/services/meta_tot_engine.py:53-71`

```python
def compute_ucb_score(
    self,
    total_parent_visits: int,
    exploration_constant: float = 2.0
) -> float:
    """
    UCB score combines exploitation + exploration + prediction bonus.
    This drives thoughtseed competition in MCTS tree search.
    """
    if self.visit_count == 0:
        return float("inf")  # Unexplored nodes win initially

    exploitation = self.value_estimate
    exploration = exploration_constant * math.sqrt(
        math.log(max(total_parent_visits, 1)) / self.visit_count
    )
    prediction_bonus = 1.0 / (1.0 + self.active_inference_state.prediction_error)

    return exploitation + exploration + prediction_bonus
```

### Data Models

**File**: `api/models/meta_tot.py:15-44`

```python
class ActiveInferenceState(BaseModel):
    """Active inference currency state for thoughtseed."""

    state_id: str
    prediction_error: float = 0.0
    free_energy: float = 0.0
    surprise: float = 0.0
    precision: float = 1.0
    beliefs: Dict[str, float]
    prediction_updates: Dict[str, float]
    reasoning_level: int = 0

    def update_beliefs(self, prediction_error: float, learning_rate: float = 0.1):
        """Update beliefs based on prediction error (active inference)."""
        for belief_key, belief_value in list(self.beliefs.items()):
            gradient = self.prediction_updates.get(belief_key, 0.0)
            belief_update = -learning_rate * gradient * prediction_error
            self.beliefs[belief_key] = max(0.0, min(1.0, belief_value + belief_update))

        # Compute free energy: prediction error + complexity penalty
        self.free_energy = prediction_error + 0.01 * len(self.beliefs)
        self.surprise = -math.log(max(0.001, 1.0 - min(prediction_error, 0.99)))
```

### Tests

**Unit Tests**: `tests/integration/test_metacognition_semantic_storage.py:131-137`
**Integration Tests**: `tests/unit/test_metacognition_runtime_integration.py`

## Key Characteristics

### 1. Unconscious Process
Competition happens below conscious awareness. You experience only the winner, not the competition itself.

### 2. Parallel Evaluation
All thoughtseeds evaluated simultaneously, not sequentially. This enables rapid selection without serial bottleneck.

### 3. Winner-Take-All
Only one thoughtseed becomes conscious at a time (or small coherent set). Losers remain unconscious or fade.

### 4. Energy-Based Selection
Pure computational criterion: lowest free energy wins. No homunculus, no central decider—emergent from dynamics.

### 5. Continuous Competition
Process never stops during waking consciousness. Even stable basins face ongoing challenges from new thoughtseeds.

### 6. Metacognitively Transparent
The transition generates metacognitive feelings (Aha!, confusion, flow) that signal competition outcome.

## Examples

### Example 1: Debugging Problem

**Situation**: Test failing unexpectedly, multiple hypotheses compete

**Thoughtseeds Generated**:
```
1. "Check test fixtures"
   Complexity: 0.8 (moderate investigation)
   Accuracy: 0.5 (might not be the issue)
   F = 0.8 - 0.5 = 0.3

2. "Review recent code changes"
   Complexity: 0.5 (quick git log scan)
   Accuracy: 0.8 (likely culprit)
   F = 0.5 - 0.8 = -0.3 ← WINNER (negative F = excellent)

3. "Restart test environment"
   Complexity: 1.5 (time-consuming rebuild)
   Accuracy: 0.3 (unlikely to help)
   F = 1.5 - 0.3 = 1.2

4. "Check database state"
   Complexity: 1.2 (requires investigation)
   Accuracy: 0.6 (possible factor)
   F = 1.2 - 0.6 = 0.6
```

**Competition Outcome**:
- **Winner**: "Review recent code changes" (F = -0.3)
- **ΔF**: Small gradual decrease (0.3 → -0.3)
- **Feeling**: Gradual understanding, confidence building
- **Basin**: Medium depth (persists for minutes)
- **Action**: Open git log, scan recent commits

**Displacement Event**: After reviewing code, no obvious issues found
- Previous basin destabilizes (F increases: -0.3 → 2.0)
- New competition triggered
- New winner: "Check database state" (now most promising)

### Example 2: Insight Moment

**Before Insight**:
```
Thoughtseed A: "Metacognition is thinking about thinking"
Complexity: 2.0 (vague, circular definition)
Accuracy: 0.4 (doesn't explain mechanism)
F = 2.0 - 0.4 = 1.6 (mediocre, persistent confusion)
```

**Reading Documentation**: New information arrives

**Sudden Insight**:
```
Thoughtseed B: "Thoughtseeds ARE metacognitive feelings!"
Complexity: 0.3 (elegant unification)
Accuracy: 0.95 (explains everything coherently)
F = 0.3 - 0.95 = -0.65 (excellent!)
```

**Competition Outcome**:
- **Winner**: Thoughtseed B (F = -0.65)
- **ΔF**: Large sudden drop (1.6 → -0.65 = -2.25)
- **Feeling**: **"Aha!"** moment (epistemic gain)
- **Basin**: Very deep (persists for hours/days)
- **Phenomenology**: Flash of understanding, emotional charge, body relaxation

### Example 3: Architecture Decision

**Context**: Choosing authentication strategy for API

**Thoughtseeds Competing**:
```
Candidate A: "JWT tokens"
Complexity: 1.3 (signing, verification, storage)
Accuracy: 0.85 (fits stateless API requirement)
F = 1.3 - 0.85 = 0.45 ← WINNER

Candidate B: "Session cookies"
Complexity: 1.5 (server-side sessions, scaling issues)
Accuracy: 0.6 (conflicts with stateless requirement)
F = 1.5 - 0.6 = 0.9

Candidate C: "OAuth2 with PKCE"
Complexity: 3.5 (multiple endpoints, complex flow)
Accuracy: 0.4 (massive overkill for simple API)
F = 3.5 - 0.4 = 3.1

Candidate D: "Magic links"
Complexity: 2.5 (email infrastructure, UX complexity)
Accuracy: 0.6 (novel but uncertain)
F = 2.5 - 0.6 = 1.9
```

**Competition Outcome**:
- **Winner**: JWT tokens (F = 0.45)
- **Feeling**: Flow state (stable low energy)
- **Basin**: Deep (F < 1.5, resistant to displacement)
- **Persistence**: Hours to days (remains stable during implementation)
- **Resistance**: Requires significant new evidence to displace (e.g., security audit finding critical flaw)

## Related Concepts

**Prerequisites** (understand these first):
- [[thoughtseed]] - What competes in thoughtseed competition
- [[free-energy]] - The selection criterion (F = Complexity - Accuracy)
- [[prediction-error]] - What drives free energy calculation

**Builds Upon** (this uses):
- [[active-inference]] - Theoretical foundation for free energy minimization
- [[surprise-score]] - Entropy component of free energy
- [[precision-weighting]] - Confidence modulation of competition

**Used By** (depends on this):
- [[attractor-basin]] - Outcome of winning competition
- [[basin-transition]] - Competition-driven reorganization
- [[metacognitive-feelings]] - Subjective signals of competition outcome
- [[ooda-loop]] - Continuous cycling of competition

**Related** (similar or complementary):
- [[meta-tot]] - MCTS implementation of thoughtseed generation
- [[selective-attention]] - Conscious manifestation of competition
- [[consciousness-stream]] - Temporal sequence of competition outcomes

**Foundational Document**:
- [05-thoughtseed-competition-explained.md](../05-thoughtseed-competition-explained.md) - Comprehensive visual explanation

## Metacognitive Feelings Generated

Different competition patterns produce distinct subjective feelings:

| Competition Pattern | ΔF (Energy Change) | Feeling | Phenomenology |
|--------------------|--------------------|---------|---------------|
| Sudden large drop | ΔF < -2.0 | **Aha!** | Flash of insight, emotional charge, relief |
| Gradual decrease | ΔF ≈ -0.3/step | **Understanding** | Pieces falling into place, confidence building |
| Stays high | F > 3.0 | **Confusion** | Mental fog, uncertainty, need for new approach |
| Oscillating | F varies ±0.5 | **Uncertainty** | Torn between options, indecision |
| Stable low | F < 1.5 | **Flow** | Effortless thought, clarity, coherence |
| Rising then drop | F ↑ then ↓ | **Effort → Relief** | Struggle followed by breakthrough |
| Rapid displacement | Many winners/sec | **Distraction** | Can't focus, thoughts racing |

**See**: [[metacognitive-feelings]] for detailed mapping

## Common Misconceptions

**Misconception 1**: "I consciously choose which thought to think"
**Reality**: Competition is unconscious. You experience only the winner. The "choosing" IS the competition process, not a separate conscious act.

**Misconception 2**: "All my thoughts compete equally"
**Reality**: Competition is biased by precision, goals, and current basin. Deep basins resist displacement (conservatism). Novel thoughtseeds may need very low F to win.

**Misconception 3**: "The winner is always the 'best' thought"
**Reality**: Winner is lowest F in current context. Context changes, goals shift, new information arrives—yesterday's winner may be today's loser.

**Misconception 4**: "Competition is serial (one after another)"
**Reality**: Parallel evaluation. All thoughtseeds assessed simultaneously. Winner emerges from collective dynamics, not sequential testing.

**Misconception 5**: "Consciousness is passive reception of thoughtseeds"
**Reality**: Consciousness IS the competition process. Selection, basin formation, and feeling generation are consciousness, not inputs to it.

## When to Use

### In Cognitive Architecture

✅ **Use thoughtseed competition when**:
- Selecting between multiple hypotheses
- Implementing selective attention
- Generating metacognitive feelings
- Modeling consciousness as dynamical process
- Explaining insight moments computationally

❌ **Don't use when**:
- Single hypothesis available (no competition)
- Selection based on external rules (not free energy)
- Purely reflex behavior (no deliberation)

### In Clinical Context (IAS)

✅ **Use to explain**:
- Why some thoughts "stick" (deep basins)
- Why insight feels sudden (large ΔF)
- Why distraction happens (shallow basins)
- Why rumination persists (very deep maladaptive basins)
- How mindfulness works (observing competition without attachment)

❌ **Don't use to**:
- Blame patients for "wrong" thoughts (competition is unconscious)
- Prescribe which thoughtseeds should win (emergent from dynamics)
- Override natural competition artificially (causes resistance)

### Implementation Guidance

**When implementing thoughtseed competition**:

1. **Generate thoughtseeds in parallel** (not sequential)
2. **Calculate free energy for each** using EFE engine
3. **Select minimum F** (winner-take-all)
4. **Create attractor basin** for winner
5. **Generate metacognitive feeling** based on ΔF
6. **Repeat continuously** (OODA loop)

**Key implementation files**:
- EFE calculation: `api/services/efe_engine.py:61-133`
- Meta-ToT MCTS: `api/services/meta_tot_engine.py:53-71`
- Active inference state: `api/models/meta_tot.py:15-44`
- Selection response: `api/models/cognitive.py` (EFEResult, EFEResponse)

## Further Reading

**Research Foundation**:
- Friston, K. (2010). "The free-energy principle: a unified brain theory?" *Nature Reviews Neuroscience*
- Hohwy, J. (2013). *The Predictive Mind*
- Dehaene, S. (2014). *Consciousness and the Brain* (Global Workspace Theory)

**Implementation Documentation**:
- [specs/038-thoughtseeds-framework/](../../specs/038-thoughtseeds-framework/) - Original specification
- [specs/041-meta-tot-engine/](../../specs/041-meta-tot-engine/) - Meta-ToT MCTS integration
- [specs/048-precision-modulation/](../../specs/048-precision-modulation/) - Precision weighting feature

**Related Silver Bullets**:
- [01-metacognition-two-layer-model.md](../01-metacognition-two-layer-model.md) - Theoretical foundation
- [04-smolagents-metatot-skills-integration.md](../04-smolagents-metatot-skills-integration.md) - Implementation architecture
- [05-thoughtseed-competition-explained.md](../05-thoughtseed-competition-explained.md) - Visual narrative explanation

**Interactive Visualization**:
- [../visualizations/thoughtseed-competition.html](../visualizations/thoughtseed-competition.html) - Real-time simulation

---

**Last Updated**: 2026-01-02
**Author**: Dr. Mani Saint-Victor, MD
**Maintainer**: Documentation Agent-9
**Status**: Production
