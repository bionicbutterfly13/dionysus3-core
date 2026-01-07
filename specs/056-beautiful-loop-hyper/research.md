# Research: Beautiful Loop Hyper-Model Implementation

**Feature Branch**: `056-beautiful-loop-hyper`
**Date**: 2026-01-05
**Status**: Complete

---

## Research Task 1: Precision Profile Representation

**Question**: How to represent per-layer and per-modality precision weights efficiently?

### Decision: Pydantic Model with Dict[str, float]

**Rationale**:
- Pydantic v2 provides native validation with minimal overhead
- Dictionary keys allow dynamic layer/modality names without schema changes
- NumPy arrays would require serialization for API responses and Graphiti storage
- Existing `BeliefState` uses similar dict patterns for probability distributions

**Implementation**:
```python
class PrecisionProfile(BaseModel):
    layer_precisions: dict[str, float] = Field(default_factory=dict)
    modality_precisions: dict[str, float] = Field(default_factory=dict)
    temporal_depth: float = Field(ge=0.0, le=1.0, default=0.5)
    meta_precision: float = Field(ge=0.0, le=1.0, default=0.5)
    context_embedding: list[float] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Alternatives Considered**:
| Approach | Pros | Cons |
|----------|------|------|
| NumPy arrays | Fast computation | Serialization overhead, schema rigidity |
| Python dicts | Flexible, JSON-native | No type hints for values |
| Pydantic Model | Validated, documented, fast | Slightly more verbose |

**Performance Note**: For <50ms forecast requirement (SC-001), Pydantic v2's Rust-based validation adds <1ms overhead.

---

## Research Task 2: Hyper-Model Learning Algorithm

**Question**: What algorithm for second-order precision learning?

### Decision: Exponential Moving Average (EMA) with Bounded Learning Rate

**Rationale**:
- EMA is computationally simple: O(1) per update
- Natural forgetting factor handles non-stationary environments
- Existing `MetaplasticityService` uses similar decay patterns
- Kalman filter would require state covariance tracking (too complex for MVP)
- Gradient descent requires loss function definition and backpropagation

**Implementation**:
```python
# Hyper-model update rule
new_precision = (1 - alpha) * predicted_precision + alpha * actual_precision_needed

# Where alpha is bounded:
alpha = clip(base_learning_rate * surprise_magnitude, min=0.01, max=0.3)
```

**Learning Rate Bounds**:
- **min=0.01**: Prevents complete stagnation; ensures some adaptation
- **max=0.3**: Prevents instability from large corrections
- **base_learning_rate=0.1**: Matches MetaplasticityService defaults

**Alternatives Considered**:
| Approach | Pros | Cons |
|----------|------|------|
| EMA | Simple, O(1), stable | No uncertainty quantification |
| Kalman Filter | Optimal, tracks uncertainty | O(n³) per update, complex |
| Gradient Descent | Well-understood | Requires loss function, backprop |
| Bayesian Online | Principled uncertainty | Computational overhead |

**SC-003 Validation**: 20% error reduction after 100 cycles achievable with alpha=0.1 given typical surprise distributions.

---

## Research Task 3: Binding Capacity Limits

**Question**: What is the optimal binding capacity for the system?

### Decision: Configurable with Default of 7±2 (Miller's Law)

**Rationale**:
- Miller's Law (1956): Human working memory capacity is 7±2 items
- Provides theoretical grounding while allowing tuning
- Too low (3-4): Insufficient context for complex reasoning
- Too high (15+): Dilutes binding strength, loses selectivity
- Configurable allows experimentation for SC-005 validation

**Implementation**:
```python
class BindingConfig(BaseModel):
    min_capacity: int = Field(default=5, ge=1)
    max_capacity: int = Field(default=9, ge=1)
    default_capacity: int = Field(default=7, ge=1)
    
    # Dynamic adjustment based on task complexity
    def get_capacity(self, task_complexity: float) -> int:
        """Higher complexity → lower capacity (more selective)."""
        span = self.max_capacity - self.min_capacity
        return int(self.max_capacity - (task_complexity * span))
```

**Alternatives Considered**:
| Approach | Pros | Cons |
|----------|------|------|
| Fixed 7 | Simple, theoretically grounded | No adaptation |
| Dynamic 4-12 | Flexible | Needs complexity metric |
| Unlimited | No artificial constraint | Loses binding semantics |

**Edge Case (EC-005)**: When unified state exceeds memory, prioritized pruning uses binding strength as the sort key.

---

## Research Task 4: Coherence Computation

**Question**: How to compute coherence between beliefs?

### Decision: Normalized Cosine Similarity on Belief Embeddings

**Rationale**:
- Cosine similarity is fast: O(n) where n = embedding dimension
- Scale-invariant: Works regardless of belief magnitude
- Existing `BeliefState` already has embedding infrastructure
- KL divergence requires probability normalization (not all beliefs are distributions)
- Attractor basin distance requires basin computation (circular dependency)

**Implementation**:
```python
def compute_coherence(
    candidate: BoundInference,
    reality_model: UnifiedRealityModel
) -> float:
    """
    Coherence = average cosine similarity between candidate
    and all currently bound beliefs.
    """
    if not reality_model.bound_inferences:
        return 1.0  # First inference is maximally coherent
    
    similarities = []
    for bound in reality_model.bound_inferences:
        sim = cosine_similarity(candidate.embedding, bound.embedding)
        similarities.append(sim)
    
    # Normalize to [0, 1]
    return (sum(similarities) / len(similarities) + 1) / 2
```

**Coherence Thresholds**:
- **High coherence (>0.7)**: Strongly aligned with reality model
- **Medium coherence (0.4-0.7)**: Compatible but not reinforcing
- **Low coherence (<0.4)**: Potentially disruptive, requires high precision

**Alternatives Considered**:
| Approach | Pros | Cons |
|----------|------|------|
| Cosine Similarity | Fast, scale-invariant | Ignores belief structure |
| KL Divergence | Information-theoretic | Requires probability distributions |
| Basin Distance | Semantically rich | Circular dependency, slow |
| Graph Overlap | Captures relationships | Requires graph structure |

---

## Research Task 5: EventBus Integration

**Question**: How to broadcast precision updates efficiently?

### Decision: Typed Events via Existing EventBus with New Event Types

**Rationale**:
- Existing `EventBus` handles cognitive event routing (FR-027)
- Adding new event types is non-breaking
- Async dispatch ensures non-blocking broadcast
- Existing subscribers (ConsciousnessManager, agents) can opt-in

**Implementation**:
```python
# New event types for precision broadcast
class PrecisionForecastEvent(CognitiveEvent):
    """Emitted at OODA cycle start with new precision profile."""
    event_type: Literal["precision_forecast"] = "precision_forecast"
    precision_profile: PrecisionProfile
    cycle_id: str

class PrecisionErrorEvent(CognitiveEvent):
    """Emitted at OODA cycle end with precision errors."""
    event_type: Literal["precision_error"] = "precision_error"
    errors: list[PrecisionError]
    cycle_id: str

class PrecisionUpdateEvent(CognitiveEvent):
    """Emitted after hyper-model update with new Φ."""
    event_type: Literal["precision_update"] = "precision_update"
    new_profile: PrecisionProfile
    learning_delta: float
```

**Subscription Pattern**:
```python
# In ConsciousnessManager.__init__
self.event_bus.subscribe("precision_forecast", self._on_precision_forecast)
self.event_bus.subscribe("precision_update", self._apply_new_precision)
```

**Alternatives Considered**:
| Approach | Pros | Cons |
|----------|------|------|
| EventBus events | Existing infrastructure, async | Loose coupling |
| Direct method calls | Explicit dependencies | Tight coupling, blocking |
| Shared state object | Simple reads | Race conditions, no notifications |
| Message queue | Durable, ordered | External dependency overkill |

**Performance Note**: EventBus dispatch is O(subscribers), typically <10 for precision events.

---

## Additional Findings

### Existing Code Patterns to Follow

From codebase analysis:

1. **Service Pattern** (`api/services/`):
   ```python
   class ServiceName:
       def __init__(self, event_bus: EventBus, ...):
           self.event_bus = event_bus
       
       async def operation(self, ...) -> Result:
           # Async operations with event emission
           await self.event_bus.emit(SomeEvent(...))
   ```

2. **Model Pattern** (`api/models/`):
   ```python
   class ModelName(BaseModel):
       model_config = ConfigDict(frozen=True)  # Immutable where appropriate
       
       field: type = Field(description="...", ge=0, le=1)
   ```

3. **Test Pattern** (`tests/unit/`):
   ```python
   @pytest.mark.asyncio
   async def test_operation_success():
       service = ServiceName(mock_event_bus)
       result = await service.operation(valid_input)
       assert result.field == expected
   ```

### Integration Points Confirmed

| Component | Integration Method | File |
|-----------|-------------------|------|
| ActiveInferenceService | Direct import, VFE/EFE calls | `api/services/active_inference_service.py` |
| BeliefState | Model composition | `api/models/belief_state.py` |
| MetaplasticityService | Extend for hyper-model | `api/services/metaplasticity_service.py` |
| EventBus | Inject, subscribe, emit | `api/utils/event_bus.py` |
| ConsciousnessManager | Modify OODA cycle | `api/agents/consciousness_manager.py` |

---

## Summary

All research tasks resolved. Ready to proceed to Phase 1 design.

| Task | Decision | Confidence |
|------|----------|------------|
| Precision Representation | Pydantic Model with Dict | High |
| Learning Algorithm | EMA with bounded alpha | High |
| Binding Capacity | Configurable 7±2 | High |
| Coherence Computation | Cosine Similarity | Medium-High |
| EventBus Integration | New typed events | High |
