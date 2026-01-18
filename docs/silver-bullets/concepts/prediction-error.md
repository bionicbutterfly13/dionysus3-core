# Prediction Error

**Category**: Core Concept
**Type**: Cognitive Metric
**Implementation**: `api/core/engine/active_inference.py:53-54`, `api/models/meta_tot.py:29-36`

---

## Definition

A **prediction error** is the mismatch between what the system expected (its internal model prediction) and what actually occurred (observed reality). It quantifies the surprise signal that drives learning and adaptation.

Think of it as the **gap between your mental map and the terrain** - when reality doesn't match your expectations, prediction error tells you how far off you were.

## Key Characteristics

- **Magnitude-Based**: Measured as absolute difference (L2 norm for vectors, scalar diff for values)
- **Precision-Weighted**: Scaled by confidence in the prediction (higher precision = larger impact)
- **Learning Signal**: Drives belief updates and model revision
- **Multi-Scale**: Operates across all cognitive timescales (milliseconds to hours)
- **Bidirectional**: Can be positive (reality exceeds expectation) or negative (reality falls short)
- **Accumulative**: Multiple prediction errors compound to trigger basin transitions

## How It Works

### Calculation Process

1. **Generate Prediction**: System makes internal forecast based on current beliefs
2. **Observe Reality**: Actual outcome is measured or perceived
3. **Compute Mismatch**: Difference calculated (often L2 norm or absolute value)
4. **Weight by Precision**: Error scaled by certainty in prediction
5. **Propagate Signal**: Error triggers updates across relevant systems

### Mathematical Formulation

```python
# Scalar case (single value)
prediction_error = |observed_value - predicted_value| * precision

# Vector case (multi-dimensional)
prediction_error = ||observed_vector - predicted_vector||_2 * precision

# Example from meta_tot.py
def compute_prediction_error(self, observation: Dict[str, float]) -> float:
    total_error = 0.0
    for key, observed_value in observation.items():
        predicted_value = self.beliefs.get(key, observed_value)
        error = abs(observed_value - predicted_value)
        total_error += error * self.precision
    return total_error
```

### Thresholds in Dionysus

- **Low Error**: < 0.15 (stable, flow state)
- **Moderate Error**: 0.15 - 0.30 (curiosity mode)
- **High Error**: 0.30 - 0.50 (exploration triggered)
- **Critical Error**: > 0.50 (basin destabilization, major revision needed)

## Implementation

**Core Calculation**: `api/core/engine/active_inference.py:53-54`
```python
# Simplified as divergence for thoughtseed scoring
prediction_error = divergence  # ||thought_vector - goal_vector||
```

**Active Inference State**: `api/models/meta_tot.py:29-36`
```python
class ActiveInferenceState:
    prediction_error: float = 0.0

    def compute_prediction_error(self, observation: Dict[str, float]) -> float:
        total_error = 0.0
        for key, observed_value in observation.items():
            predicted_value = self.beliefs.get(key, observed_value)
            error = abs(observed_value - predicted_value)
            total_error += error * self.precision
        self.prediction_error = total_error
        return total_error
```

**Metaplasticity Integration**: `api/services/metaplasticity_service.py:118-166`
```python
# Learning rate adapts based on prediction error
def calculate_learning_rate(self, prediction_error: float) -> float:
    diff = prediction_error - self.surprise_threshold
    if diff > 0:  # High error
        adjustment = 1.0 + sigmoid(diff)  # Increase learning rate
    else:  # Low error
        adjustment = 1.0 - 0.1 * abs(diff)  # Maintain stability
    return self.base_learning_rate * adjustment
```

**Procedural Metacognition**: `api/services/procedural_metacognition.py:136-138`
```python
# Detection of high prediction error issues
if prediction_error > self.prediction_error_threshold:
    issues.append(IssueType.HIGH_PREDICTION_ERROR)
    recommendations.append("Reduce prediction error through belief update")
```

**Tests**: `tests/unit/test_meta_tot_engine.py:31-36`

## Related Concepts

**Prerequisites** (understand these first):
- [[precision-weighting]] - Scales prediction error by confidence
- [[attractor-basin]] - Stable states that prediction errors can destabilize

**Builds Upon** (this uses):
- Internal models (beliefs about world state)
- Observation mechanisms (perception agents)

**Used By** (depends on this):
- [[free-energy]] - Free Energy = Prediction Error + Complexity
- [[surprise-score]] - Unexpected prediction error magnitude
- [[thoughtseed]] - Competition driven by minimizing prediction error
- [[basin-transition]] - Triggered by sustained high prediction errors
- [[metacognitive-feelings]] - Confusion = high prediction error

**Related** (similar or complementary):
- [[active-inference]] - Prediction error drives action selection
- [[metaplasticity]] - Learning rate adapts to prediction error
- [[precision-weighting]] - Modulates prediction error impact

## Examples

### Example 1: Debugging Code

**Scenario**: You expect a test to pass, but it fails.

```python
# Prediction
expected_result = "All tests pass"
confidence = 0.8  # High confidence

# Observation
actual_result = "3 tests failed"

# Prediction Error
prediction_error = |0.0 - 1.0| * 0.8 = 0.8  # High error
# Triggers: Review recent changes (new thoughtseed)
# Feeling: Confusion (basin destabilized)
```

### Example 2: API Response Time

**Scenario**: Monitoring service latency

```python
# Prediction (from historical model)
predicted_latency = 50ms
precision = 1.2  # High precision for critical service

# Observation
observed_latency = 350ms

# Prediction Error
error = abs(350 - 50) * 1.2 = 360 units
# Triggers: HIGH_PREDICTION_ERROR issue
# Action: Increase monitoring precision, investigate cause
```

### Example 3: Thoughtseed Competition

**Scenario**: Multiple hypotheses competing

```python
# Thoughtseed A: "Use JWT authentication"
predicted_complexity_A = 0.3
actual_complexity_A = 0.4
error_A = 0.1

# Thoughtseed B: "Use OAuth2"
predicted_complexity_B = 0.5
actual_complexity_B = 0.9
error_B = 0.4

# Winner: Thoughtseed A (lower prediction error)
# Result: JWT selected, basin forms around this solution
```

### Example 4: Clinical Context ([LEGACY_AVATAR_HOLDER]s)

**Real-world application**: Identity prediction errors

```
Belief: "If I rest, I'm failing"
Predicted outcome: Productivity drops when resting
Observed reality: Most productive after deliberate rest

Prediction Error: HIGH
Trigger: Reconsolidation window opens
Opportunity: Rewrite maladaptive belief during MoSAEIC protocol
```

## Common Misconceptions

**Misconception 1**: "Prediction errors are always bad"
**Reality**: Prediction errors are the **primary learning signal**. High errors indicate novelty and trigger adaptive responses (increased learning rates, basin transitions, insight moments). Zero error = no learning.

**Misconception 2**: "Prediction error is the same as free energy"
**Reality**: Free energy = Prediction Error + Complexity. Free energy combines accuracy (prediction error) with model simplicity. You can have low prediction error but high free energy if the model is overly complex.

**Misconception 3**: "All prediction errors have equal impact"
**Reality**: Prediction errors are **precision-weighted**. High-confidence predictions that fail generate larger effective errors than low-confidence predictions. This prevents the system from over-reacting to uncertain guesses.

**Misconception 4**: "Prediction errors only affect current processing"
**Reality**: Prediction errors accumulate over time to trigger **higher-order changes** like basin transitions, worldview revisions, and metaplasticity adjustments. They're tracked across multiple timescales.

## When to Use

✅ **Use when**:
- Evaluating thoughtseed quality (lower error = better fit)
- Detecting when internal models need updating
- Triggering metaplasticity (learning rate adjustment)
- Identifying high-uncertainty situations requiring exploration
- Generating metacognitive feelings (confusion, surprise, insight)
- Driving active inference action selection

❌ **Don't use when**:
- You need a holistic quality metric (use free energy instead)
- Comparing vastly different prediction types without normalization
- Operating in purely deterministic contexts (no uncertainty)
- Ignoring precision weighting (creates false equivalences)

## Relationship to Free Energy

```
Free Energy (F) = Prediction Error + Complexity

F = ||observed - predicted||² + KL(q||p)
    \_________________/         \________/
    Prediction Error            Complexity
    (Accuracy cost)             (Model cost)
```

**Key Distinction**:
- **Prediction Error**: How wrong was the prediction?
- **Complexity**: How complicated is the model making predictions?
- **Free Energy**: Combined metric balancing accuracy and simplicity

**Example**:
```
Model A: Perfect predictions (error=0), 1000 parameters (complex)
Model B: Slightly off (error=0.1), 10 parameters (simple)

Prediction Error: A wins (0 < 0.1)
Free Energy: B might win (0.1 + small_penalty < 0 + large_penalty)
```

## Visual Representation

```
PREDICTION ERROR AS LEARNING SIGNAL

Time →
Error ↑
  1.0 │                    ╱╲  ← Critical error
      │                   ╱  ╲    (basin transition)
  0.5 │         ╱╲       ╱    ╲
      │        ╱  ╲     ╱      ╲___
  0.3 │   ╱╲  ╱    ╲___╱           ╲  ← High error
      │  ╱  ╲╱                      ╲    (exploration mode)
  0.15│_╱                            ╲__ ← Low error
      │                                  (flow state)
  0.0 └────────────────────────────────────→
       Events: Novel  Adapted  Novel   Adapted

EFFECTS:
- High Error → ↑ Learning Rate, ↓ Precision, Explore
- Low Error  → ↓ Learning Rate, ↑ Precision, Exploit
```

## Further Reading

- **Research**: Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127-138.
- **Documentation**:
  - [[free-energy]] - Includes prediction error as accuracy term
  - [[active-inference]] - Prediction error drives action selection
  - [[precision-weighting]] - How confidence scales prediction error
  - [[05-thoughtseed-competition-explained.md]](../05-thoughtseed-competition-explained.md#step-3-competition-happens-through-prediction-error)
- **Implementation**:
  - Active Inference Engine: `api/core/engine/active_inference.py`
  - Metaplasticity Service: `api/services/metaplasticity_service.py`
  - Meta-ToT Models: `api/models/meta_tot.py:29-44`
- **Specs**:
  - 034-network-self-modeling: Prediction error drives metaplasticity
  - 040-metacognitive-particles: HIGH_PREDICTION_ERROR issue detection
  - 041-meta-tot-engine: Thoughtseed scoring via prediction error

---

**Last Updated**: 2026-01-02
**Maintainer**: Agent-2
**Status**: Production
