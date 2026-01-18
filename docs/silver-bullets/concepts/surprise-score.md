# Surprise Score

**Category**: Core Concept
**Type**: Computational Metric
**Implementation**: `api/core/engine/active_inference.py:59`, `api/services/efe_engine.py:47-52`, `api/models/meta_tot.py:22`

---

## Definition

A **surprise score** quantifies the unexpectedness of an observation relative to the system's predictions. It measures entropy—the degree of uncertainty or novelty in the current state—and serves as a primary signal for exploration vs exploitation decisions.

In active inference terms, surprise is the **negative log probability** of an observation: `-log P(observation | model)`. Higher surprise indicates the observation was unlikely given current beliefs, triggering exploration and learning.

Think of it as **how much the system's eyebrows raise**—low surprise means "as expected," high surprise means "wait, what?!"

## Mathematical Formulation

### Shannon Entropy (Primary Implementation)

```python
# Discrete probability distribution
surprise = -Σ p(x) * log₂(p(x))

# Implementation from efe_engine.py:47-52
def calculate_entropy(probabilities: List[float]) -> float:
    """Calculates Shannon entropy of a probability distribution."""
    return float(entropy(probabilities, base=2))  # bits
```

**Units**: Bits (using log base 2)

### Relationship to Prediction Error

In Dionysus, surprise is often approximated using prediction error metrics:

```python
# From active_inference.py:59
surprise = entropy  # Using entropy as proxy for surprise

# From meta_tot.py:44
self.surprise = -math.log(max(0.001, 1.0 - min(prediction_error, 0.99)))
```

**Key insight**: Surprise ≈ entropy of predictions. High entropy → high uncertainty → high surprise.

### KL Divergence (Alternative Formulation)

```python
# KL divergence between expected and observed distributions
KL(P||Q) = Σ P(x) * log(P(x) / Q(x))

# Used in agency detection for surprise calculation
surprise_score = KL(internal_states || active_states)
```

## Key Characteristics

- **Entropy-Based**: Measured as Shannon entropy of probability distributions (bits of information)
- **Threshold-Driven**: Different surprise levels trigger different system behaviors
- **Learning Signal**: High surprise increases learning rates (metaplasticity)
- **Precision Modulator**: Surprise inversely affects precision (high surprise → lower precision → wider attention)
- **Exploration Trigger**: Sustained high surprise shifts system from exploitation to exploration
- **Metacognitive Feeling**: Maps to confusion (high), curiosity (medium), flow (low)

## Thresholds in Dionysus

### Surprise Levels

- **Low Surprise**: < 0.3 (expected, flow state)
  - Maintain current precision
  - Exploit existing knowledge
  - Stable basin, low free energy

- **Medium Surprise**: 0.3 - 0.7 (novelty detected)
  - Curiosity mode activated
  - Increase exploration slightly
  - Monitor for learning opportunities

- **High Surprise**: > 0.7 (unexpected event)
  - Decrease precision (zoom out)
  - Increase learning rate
  - Trigger exploration mode
  - Potentially destabilize basin

### Control Pattern Thresholds

```python
# From metacognition_patterns_storage.py:90
surprise_threshold: float = 0.7

# Action selection based on surprise
if surprise > self.surprise_threshold:
    return self.actions.get("high_surprise")  # Exploration action
```

### Metaplasticity Thresholds

```python
# From metaplasticity_service.py:36, 81
surprise_threshold: float = 0.5

# Precision modulation
if surprise > 0.5:
    precision_delta = (0.5 - surprise_score) * 0.2  # Negative → decrease precision
else:
    precision_delta = (0.5 - surprise_score) * 0.2  # Positive → increase precision
```

## Implementation

### Core Calculation

**File**: `api/services/efe_engine.py:47-52`

```python
def calculate_entropy(self, probabilities: List[float]) -> float:
    """Calculates Shannon entropy of a probability distribution."""
    if not probabilities:
        return 1.0
    # scipy.stats.entropy uses ln by default, we use base 2 for bits
    return float(entropy(probabilities, base=2))
```

### Active Inference Integration

**File**: `api/core/engine/active_inference.py:46-59`

```python
# Calculate Base Metrics
entropy = self.engine.calculate_entropy(context_probs)
divergence = self.engine.calculate_goal_divergence(thought_np, goal_np)

# Calculate EFE
efe = self.engine.calculate_efe(context_probs, thought_np, goal_np)

# Create Score Object
score = ActiveInferenceScore(
    expected_free_energy=efe,
    surprise=entropy,  # Using entropy as proxy for surprise
    prediction_error=divergence,
    precision=1.0
)
```

### Meta-ToT State Tracking

**File**: `api/models/meta_tot.py:22-44`

```python
class ActiveInferenceState(BaseModel):
    surprise: float = 0.0

    def update_beliefs(self, prediction_error: float, learning_rate: float = 0.1) -> None:
        for belief_key, belief_value in list(self.beliefs.items()):
            gradient = self.prediction_updates.get(belief_key, 0.0)
            belief_update = -learning_rate * gradient * prediction_error
            self.beliefs[belief_key] = max(0.0, min(1.0, belief_value + belief_update))

        self.free_energy = prediction_error + 0.01 * len(self.beliefs)
        self.surprise = -math.log(max(0.001, 1.0 - min(prediction_error, 0.99)))
```

### Metaplasticity Modulation

**File**: `api/services/metaplasticity_service.py:67-84`

```python
def update_precision_from_surprise(self, agent_id: str, surprise_score: float) -> float:
    """
    Dynamically tune precision based on Surprise (Prediction Error).
    High Surprise -> Decrease Precision (Zoom Out / Curiosity)
    Low Surprise -> Increase Precision (Zoom In / Focus)
    """
    current = self.get_precision(agent_id)
    alpha = 0.2  # Modulation sensitivity

    # If surprise > 0.5, decrease precision; if < 0.5, increase precision
    delta = (0.5 - surprise_score) * alpha
    new_value = current + delta

    self.set_precision(agent_id, new_value)
    return self.get_precision(agent_id)
```

### Cognitive Episode Recording

**File**: `api/models/meta_cognition.py:25`

```python
class CognitiveEpisode(BaseModel):
    surprise_score: float = Field(
        0.0,
        description="Metric of prediction error (0.0=Expected, 1.0=Total Surprise)."
    )
```

### Episodic Memory Storage

**File**: `api/services/meta_cognitive_service.py:83, 104, 117`

```python
# Retrieve with surprise_score
surprise_score=float(node.get("surprise_score", 0.0))

# Store in Neo4j
c.surprise_score = $surprise_score

# Query high-surprise episodes
WHERE e.surprise_score > 0.5
ORDER BY e.surprise_score DESC
```

**Tests**: `tests/unit/test_metaplasticity.py`, `tests/unit/test_efe_engine.py`

## Related Concepts

**Prerequisites** (understand these first):
- [[prediction-error]] - Surprise is related to prediction error magnitude
- [[precision-weighting]] - Precision inversely scales with surprise

**Builds Upon** (this uses):
- Shannon entropy (information theory)
- Probability distributions
- Bayesian inference

**Used By** (depends on this):
- [[free-energy]] - Free Energy = Surprise + Complexity (in some formulations)
- [[metaplasticity]] - Learning rate adapts based on surprise
- [[thoughtseed]] - Thoughtseed competition considers surprise in EFE
- [[basin-transition]] - High surprise destabilizes basins
- [[metacognitive-feelings]] - Surprise maps to confusion/curiosity

**Related** (similar or complementary):
- [[active-inference]] - Surprise drives exploration vs exploitation
- [[exploration-exploitation]] - Surprise triggers mode shifts

## Examples

### Example 1: Low Surprise (Flow State)

**Scenario**: Code review of familiar patterns

```python
# Prediction
probabilities = [0.9, 0.1]  # High confidence

# Surprise Calculation
surprise = -Σ p * log₂(p)
         = -(0.9 * log₂(0.9) + 0.1 * log₂(0.1))
         = -(0.9 * -0.152 + 0.1 * -3.322)
         = -(-0.137 + -0.332)
         = 0.469 bits

# Result: Low surprise (< 0.5)
# Action: Maintain precision, continue exploitation
# Feeling: Flow, confidence
```

### Example 2: Medium Surprise (Curiosity)

**Scenario**: Encountering a new API pattern

```python
# Prediction
probabilities = [0.6, 0.4]  # Moderate uncertainty

# Surprise Calculation
surprise = -(0.6 * log₂(0.6) + 0.4 * log₂(0.4))
         = -(0.6 * -0.737 + 0.4 * -1.322)
         = -(-0.442 + -0.529)
         = 0.971 bits

# Result: Medium surprise (0.5 < s < 0.7)
# Action: Slight precision decrease, explore context
# Feeling: Curiosity, engaged investigation
```

### Example 3: High Surprise (Exploration Mode)

**Scenario**: Test fails in unexpected way

```python
# Prediction
probabilities = [0.5, 0.5]  # Maximum uncertainty

# Surprise Calculation (Maximum Entropy)
surprise = -(0.5 * log₂(0.5) + 0.5 * log₂(0.5))
         = -(0.5 * -1.0 + 0.5 * -1.0)
         = -(-0.5 + -0.5)
         = 1.0 bits

# Result: High surprise (> 0.7)
# Action: Decrease precision significantly, explore widely
# Feeling: Confusion, need to investigate
# System Response:
# - Learning rate increased by 20%
# - Precision decreased by 40%
# - Additional exploration steps added (+2)
```

### Example 4: Metaplasticity Response

**Code from metaplasticity_service.py:184-191**

```python
# Scenario: prediction_error = 0.8 (high surprise)
surprise_threshold = 0.5

if prediction_error > surprise_threshold:
    # Increase learning speed by up to 20%
    delta = 0.2 * (0.8 - 0.5) = 0.06
    new_h_state = current_h * (1 + 0.06) = 1.06x faster learning
else:
    # Decrease speed (stable predictions)
    delta = 0.1 * (0.5 - prediction_error)
    new_h_state = current_h * (1 - delta)
```

### Example 5: Cognitive Episode ([LEGACY_AVATAR_HOLDER]s)

**Real-world application**: Recording therapy session insights

```python
episode = CognitiveEpisode(
    task_query="Why do I feel guilty when resting?",
    success=True,
    outcome_summary="Discovered maladaptive belief: 'Rest = Failure'",
    surprise_score=0.75,  # High - unexpected core belief identified
    lessons_learned="Hypervigilance pattern linked to childhood security optimization"
)

# High surprise triggers:
# 1. Increased learning rate for belief update
# 2. Decreased precision to explore related beliefs
# 3. Potential basin transition (identity shift opportunity)
```

## Common Misconceptions

**Misconception 1**: "Surprise is the same as prediction error"
**Reality**: Surprise is **entropy-based** (uncertainty in probability distribution), while prediction error is **magnitude-based** (difference between expected and observed values). They're related but distinct. Surprise = "How uncertain am I?" vs Prediction Error = "How wrong was I?"

**Misconception 2**: "All surprise is bad"
**Reality**: Surprise is the **primary learning signal**. Moderate surprise (curiosity range) is optimal for learning. Zero surprise = no learning. High surprise = exploration mode (valuable for discovery).

**Misconception 3**: "Surprise score is binary (surprised or not)"
**Reality**: Surprise is **continuous** (0.0 to ~1.0+ bits) with different threshold-based behaviors at different levels. It's a gradient, not a switch.

**Misconception 4**: "Surprise only affects current processing"
**Reality**: Surprise modulates **multiple systems simultaneously**: learning rates, precision, exploration budget, basin stability, and metacognitive feelings. It's a global control signal.

## When to Use

✅ **Use when**:
- Deciding exploration vs exploitation balance
- Modulating learning rates dynamically
- Triggering basin transitions (surprise > 0.7 sustained)
- Generating metacognitive feelings (map surprise to emotion)
- Selecting which thoughtseeds to explore
- Adjusting precision/attention width
- Recording cognitive episodes for episodic memory

❌ **Don't use when**:
- You need absolute prediction accuracy (use prediction error instead)
- Comparing uncertainty across vastly different probability spaces
- Working in deterministic contexts (no probability distributions)
- As sole metric for quality (combine with free energy)

## Visual Representation

```
SURPRISE SCORE AS EXPLORATION TRIGGER

Surprise (bits) ↑
  1.0 │                     ╱╲
      │                    ╱  ╲  ← Maximum entropy
      │                   ╱    ╲    (total uncertainty)
  0.7 │──────────────────────────────── High threshold
      │         ╱╲                      (Exploration mode)
  0.5 │────────────╱──╲──────────────── Medium threshold
      │       ╱        ╲               (Curiosity mode)
  0.3 │──────────────────╲──────────── Low threshold
      │  ╱                ╲╲           (Flow state)
  0.0 │_╱__________________╲╲_________→ Time
       Events: Novel  Familiar  Novel  Expected

SYSTEM RESPONSES:
┌─────────────┬──────────────┬─────────────┬────────────────┐
│ Surprise    │ Precision    │ Learning    │ Exploration    │
├─────────────┼──────────────┼─────────────┼────────────────┤
│ Low (<0.3)  │ High (focus) │ Slow        │ Exploit        │
│ Med (0.3-0.7)│ Medium      │ Moderate    │ Balanced       │
│ High (>0.7) │ Low (wide)   │ Fast        │ Explore        │
└─────────────┴──────────────┴─────────────┴────────────────┘
```

## Relationship to Free Energy

**Classic Free Energy Principle**:
```
F = -log P(observations | model)
  = Surprise + Complexity
```

**In Dionysus EFE**:
```
EFE = (1/Precision) * Surprise + Precision * Divergence
    = Weighted_Uncertainty + Weighted_Goal_Distance

Where:
  Surprise ≈ Entropy of predictions
  Divergence ≈ Prediction error (distance from goal)
```

**Key Distinctions**:
- **Surprise**: How uncertain are predictions? (information theory)
- **Prediction Error**: How wrong were predictions? (distance metric)
- **Free Energy**: Combined cost function balancing both

**Example**:
```
Thoughtseed A: Low surprise (0.2), high divergence (0.8)
  → Clear prediction, but far from goal

Thoughtseed B: High surprise (0.9), low divergence (0.1)
  → Uncertain prediction, but close to goal

Which wins depends on precision weighting:
  High precision: A wins (prioritize goal)
  Low precision: B wins (prioritize exploration)
```

## Connection to Metacognitive Feelings

Surprise score directly generates metacognitive feelings:

```
SURPRISE → FEELING MAPPING

0.0 - 0.2  →  Boredom / Certainty
0.2 - 0.4  →  Flow / Confidence
0.4 - 0.6  →  Interest / Engagement
0.6 - 0.8  →  Curiosity / Puzzlement
0.8 - 1.0  →  Confusion / Uncertainty
> 1.0      →  Shock / Disorientation

From consciousness_manager.py:372:
surprise_level = active_inference_state.get("surprise", 0.0)
episode.surprise_score = surprise_level

If surprise_level > 0.7:
    feeling = "confusion"
    action = "explore_more"
elif surprise_level > 0.4:
    feeling = "curiosity"
    action = "investigate"
else:
    feeling = "confidence"
    action = "exploit"
```

## Further Reading

- **Research**:
  - Friston, K. (2010). "The free-energy principle: a unified brain theory?" *Nature Reviews Neuroscience*, 11(2), 127-138.
  - Shannon, C. E. (1948). "A Mathematical Theory of Communication." *Bell System Technical Journal*, 27(3), 379-423.
- **Documentation**:
  - [[free-energy]] - Surprise as component of free energy
  - [[prediction-error]] - Related but distinct metric
  - [[metaplasticity]] - How surprise modulates learning
  - [[precision-weighting]] - Inverse relationship with surprise
  - [[basin-transition]] - High surprise triggers transitions
- **Implementation**:
  - EFE Engine: `api/services/efe_engine.py:47-52`
  - Active Inference Wrapper: `api/core/engine/active_inference.py:59`
  - Metaplasticity Service: `api/services/metaplasticity_service.py:67-84`
  - Meta-ToT Models: `api/models/meta_tot.py:22-44`
- **Specs**:
  - 034-network-self-modeling: Metaplasticity driven by surprise
  - 038-thoughtseeds-framework: Surprise in EFE calculation
  - 041-meta-tot-engine: Surprise tracking in active inference states
  - 048-precision-modulation: Surprise inversely modulates precision

---

**Last Updated**: 2026-01-02
**Maintainer**: Agent-7 (Documentation Specialist)
**Status**: Production
