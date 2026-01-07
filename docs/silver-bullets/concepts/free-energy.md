# Free Energy

**Category**: Core Concept
**Type**: Computational Metric
**Implementation**: Active Inference Engine + EFE Calculation

---

## Definition

**Free energy** (F) is a prediction error metric that quantifies the discrepancy between an agent's beliefs and observations. It measures how well a hypothesis explains the current situation.

**Formula**: `F = Complexity - Accuracy`

Lower free energy indicates a better hypothesis—one that is both simple to compute and accurate in its predictions.

## Key Characteristics

- **Minimization Principle**: Systems naturally evolve toward states of lower free energy
- **Selection Criterion**: Thoughtseeds compete based on free energy—lowest F wins
- **Dual Components**: Balances simplicity (low complexity) against predictive power (high accuracy)
- **Continuous Metric**: Computed in real-time during active inference cycles
- **Range**: Typically 0.0 to 5.0 in implementation (lower is better)
- **Threshold**: F < 1.5 indicates stable, winning thoughtseed

## The Formula Explained

### F = Complexity - Accuracy

**Complexity**:
- How much information is needed to maintain the current belief state
- Cognitive load required to represent and process the hypothesis
- Number of assumptions, parameters, or dependencies
- Higher complexity → Higher F → Less favorable

**Accuracy**:
- How well beliefs predict future observations
- Probability that predictions will match reality: P(observations | beliefs)
- Reduction in prediction error
- Higher accuracy → Lower F → More favorable

### Expanded Formula

```
F = Complexity - Accuracy
  = |belief_state| - P(observations | beliefs)
  = Information needed - Predictive power
```

### Example Calculation

```
Hypothesis: "Use JWT for authentication"

Complexity:
- Need to implement token signing (0.5)
- Need to implement verification (0.5)
- Need to manage token storage (0.3)
- Total complexity: 1.3

Accuracy:
- Fits stateless API requirement perfectly (0.9)
- Matches security constraints (0.8)
- Predicted accuracy: 0.85

Free Energy:
F = 1.3 - 0.85 = 0.45 (LOW → Good candidate)

---

Hypothesis: "Use OAuth2 with PKCE"

Complexity:
- Multiple endpoints required (1.0)
- Complex flow with state management (1.5)
- Integration with external providers (1.0)
- Total complexity: 3.5

Accuracy:
- Overkill for simple API (0.4)
- Predicted accuracy: 0.4

Free Energy:
F = 3.5 - 0.4 = 3.1 (HIGH → Poor candidate)
```

## How It Works

### Step-by-Step Process

1. **Generate Hypotheses**: Multiple thoughtseeds created as candidate explanations
2. **Calculate Complexity**: Assess cognitive/computational cost of each hypothesis
3. **Calculate Accuracy**: Predict how well each hypothesis explains observations
4. **Compute Free Energy**: F = Complexity - Accuracy for each thoughtseed
5. **Select Winner**: Thoughtseed with minimum F wins competition
6. **Form Basin**: Winning thoughtseed creates stable attractor basin

### Visual Representation

```
High Free Energy (F > 3.0)
         ⬤ Poor hypothesis
        / \
       /   \  (Energy landscape)
      /     \
     /       \
    /         \  ⬤ Medium hypothesis (F ≈ 2.0)
   /           \/
  /             \
 /               \
/                 \  ⬤ Good hypothesis (F < 1.5)
──────────────────────────────────────
        Low Free Energy (Stable)
```

Lower position on energy landscape = Lower F = Better hypothesis

## Implementation

### Core Code

**File**: `api/services/efe_engine.py:61-84`

```python
def calculate_efe(
    self,
    prediction_probs: List[float],
    thought_vector: np.ndarray,
    goal_vector: np.ndarray,
    precision: float = 1.0
) -> float:
    """
    Calculates Expected Free Energy for a candidate thought.
    Lower EFE = More valuable thought.

    EFE = (1/Precision) * Uncertainty + Precision * Divergence
    """
    uncertainty = self.calculate_entropy(prediction_probs)
    divergence = self.calculate_goal_divergence(thought_vector, goal_vector)

    safe_precision = max(0.01, precision)
    efe = (1.0 / safe_precision) * uncertainty + safe_precision * divergence

    return efe
```

**Data Model**: `api/core/engine/models.py:6-14`

```python
class ActiveInferenceScore(BaseModel):
    """Active Inference Currency for valuing reasoning steps."""
    expected_free_energy: float  # Primary value function
    surprise: float              # Entropy/novelty
    prediction_error: float      # Deviation from model
    precision: float = 1.0       # Confidence weighting
```

**Tests**: `tests/integration/test_metacognition_semantic_storage.py:131-137`

## Related Concepts

**Prerequisites** (understand these first):
- [[prediction-error]] - Component of free energy calculation
- [[surprise-score]] - Entropy/uncertainty measure

**Builds Upon** (this uses):
- Entropy calculation (Shannon entropy)
- Cosine distance (goal divergence)
- Bayesian inference principles

**Used By** (depends on this):
- [[thoughtseed]] - Thoughtseeds are ranked by free energy
- [[thoughtseed-competition]] - Competition mechanism uses F as criterion
- [[attractor-basin]] - Basins form at low-energy states
- [[metacognitive-feelings]] - Feelings arise from ΔF transitions

**Related** (similar or complementary):
- [[activation-energy]] - Energy barrier to basin transitions
- [[precision-weighting]] - Modulates free energy calculation

## Examples

### Example 1: Debugging Problem

**Situation**: Test failing unexpectedly

**Thoughtseeds Generated**:

```
1. "Check test fixtures"
   Complexity: 0.8 (moderate work)
   Accuracy: 0.5 (might not be the issue)
   F = 0.8 - 0.5 = 0.3 ✓ Not bad

2. "Review recent code changes"
   Complexity: 0.5 (quick scan)
   Accuracy: 0.8 (likely culprit)
   F = 0.5 - 0.8 = -0.3 ✓✓ WINNER (negative F = very good)

3. "Restart test environment"
   Complexity: 1.5 (time-consuming)
   Accuracy: 0.3 (unlikely to help)
   F = 1.5 - 0.3 = 1.2 ✗ Weak candidate

4. "Check database state"
   Complexity: 1.2 (requires investigation)
   Accuracy: 0.6 (possible)
   F = 1.2 - 0.6 = 0.6 ✗ Moderate
```

**Winner**: "Review recent code changes" (F = -0.3)
**Feeling**: Gradual understanding (small ΔF, stable low energy)

### Example 2: Insight Moment

**Situation**: Reading about metacognition architecture

**Before Insight**:

```
Thoughtseed: "Metacognition is just thinking about thinking"
Complexity: 2.0 (vague concept)
Accuracy: 0.4 (doesn't explain the mechanism)
F = 2.0 - 0.4 = 1.6 (mediocre)
```

**After Reading**:

```
Thoughtseed: "Thoughtseeds ARE metacognitive feelings!"
Complexity: 0.3 (elegant unification)
Accuracy: 0.95 (explains everything)
F = 0.3 - 0.95 = -0.65 (excellent!)
```

**Change**: ΔF = 1.6 - (-0.65) = 2.25 (large drop)
**Feeling**: **Aha!** moment (sudden large free energy reduction)

### Example 3: Architecture Decision

**Context**: Choosing authentication strategy

```
Candidate A: JWT tokens
F = 0.45 (simple, accurate) → SELECTED

Candidate B: Session cookies
F = 1.8 (moderate complexity, moderate fit)

Candidate C: OAuth2
F = 3.1 (complex, overkill)

Candidate D: Magic links
F = 2.8 (novel but uncertain)
```

**Winner**: JWT (F = 0.45)
**Basin**: Deep stable attractor (F < 1.5)
**Persistence**: Hours to days (resistant to displacement)

## Precision Weighting (Feature 048)

Free energy calculation can be modulated by **precision** (confidence weighting):

```python
# Standard formula
EFE = Uncertainty + Divergence

# Precision-weighted formula
EFE = (1/Precision) * Uncertainty + Precision * Divergence
```

**Effects**:
- **High precision** (confident): Emphasize goal-seeking (divergence), de-emphasize uncertainty
- **Low precision** (uncertain): Emphasize exploration (uncertainty), de-emphasize goal commitment

**Use case**: Adaptive exploration vs exploitation based on metacognitive confidence

**Implementation**: `api/services/efe_engine.py:61-84`

## Common Misconceptions

**Misconception 1**: "Free energy is just complexity"
**Reality**: Free energy balances TWO factors—complexity AND accuracy. A complex but highly accurate model can have lower F than a simple but inaccurate one.

**Misconception 2**: "Lower free energy is always better"
**Reality**: Context matters. Sometimes high F indicates necessary exploration or indicates you need more information before committing to a hypothesis.

**Misconception 3**: "Free energy is static"
**Reality**: Free energy is continuously recalculated as new observations arrive. A winning thoughtseed can be displaced if new evidence raises its F.

**Misconception 4**: "Free energy equals surprise"
**Reality**: Surprise (entropy) is a COMPONENT of free energy, but F also includes goal divergence and precision weighting.

## When to Use

✅ **Use when**:
- Selecting between multiple candidate hypotheses
- Evaluating reasoning steps in Meta-ToT search
- Determining thoughtseed competition winners
- Triggering basin transitions (high F → reorganization)
- Generating metacognitive feelings (ΔF patterns)

❌ **Don't use when**:
- Comparing concepts across different problem domains
- Single hypothesis available (no competition)
- Absolute quality assessment needed (F is relative)

## Relationship to Active Inference

Free energy minimization is the core principle of **Active Inference**:

- **Perception**: Update beliefs to minimize F
- **Action**: Select actions that minimize expected F
- **Learning**: Adjust internal models to reduce long-term F

In Dionysus:
- **Perception Agent**: Gathers observations to reduce uncertainty
- **Reasoning Agent**: Generates hypotheses to minimize F
- **Metacognition Agent**: Selects actions based on expected F reduction
- **OODA Loop**: Continuous F minimization cycle

## The "Ball and Hill" Analogy

Free energy is like **gravitational potential energy**:

```
        HIGH ENERGY (F = 3.5)
             ●
            / \
           /   \
          /     \
         /       \
        /         \  MEDIUM ENERGY (F = 2.0)
       /           ●
      /             \
     /               \
    /                 \  LOW ENERGY (F = 0.8)
   /                   ●
  /_____________________|
        Energy Floor
```

- **Balls naturally roll downhill** → Systems minimize F
- **Valleys are stable** → Low F creates attractor basins
- **Hills are unstable** → High F triggers reorganization
- **Deep valleys resist displacement** → Strong hypotheses persist

## Further Reading

- **Research**: Friston, K. (2010). "The free-energy principle: a unified brain theory?" Nature Reviews Neuroscience.
- **Documentation**:
  - [[thoughtseed-competition]] - How F drives selection
  - [[attractor-basin]] - Where low-F thoughtseeds settle
  - [05-thoughtseed-competition-explained.md](../05-thoughtseed-competition-explained.md) - Visual explanation
- **Implementation**:
  - `specs/038-thoughtseeds-framework/` - Original specification
  - `specs/041-meta-tot-engine/` - Meta-ToT integration

---

**Last Updated**: 2026-01-02
**Author**: Dr. Mani Saint-Victor
**Status**: Production
