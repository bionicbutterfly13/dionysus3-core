# Data Model: Beautiful Loop Hyper-Model

**Feature Branch**: `056-beautiful-loop-hyper`
**Date**: 2026-01-05
**Status**: Complete

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    UnifiedRealityModel                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  BeliefState[]  │  │ActiveInference  │  │ Metacognitive  │  │
│  │   (existing)    │  │   State[]       │  │  Particle[]    │  │
│  │                 │  │   (existing)    │  │   (existing)   │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                │
│  ┌─────────────────────────────▼─────────────────────────────┐  │
│  │                    BoundInference[]                        │  │
│  │  (inferences that passed Bayesian binding competition)     │  │
│  └─────────────────────────────┬─────────────────────────────┘  │
│                                │                                │
│  coherence_score: float ◄──────┘                                │
│  epistemic_affordances: list[str]                               │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ informs
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HyperModelService                          │
│  ┌─────────────────┐           ┌─────────────────────────────┐  │
│  │ PrecisionProfile│◄──────────│ forecast_precision_profile()│  │
│  │  (current Φ)    │           └─────────────────────────────┘  │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼ broadcasts via EventBus                             │
│  ┌─────────────────┐           ┌─────────────────────────────┐  │
│  │ PrecisionError[]│◄──────────│ compute_precision_errors()  │  │
│  │ (second-order)  │           └─────────────────────────────┘  │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼ updates hyper-model                                 │
│  ┌─────────────────┐           ┌─────────────────────────────┐  │
│  │ EpistemicState  │◄──────────│ get_epistemic_state()       │  │
│  │ (luminosity)    │           └─────────────────────────────┘  │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ precision profile
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BayesianBinder                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    bind() method                         │    │
│  │  candidates ──► precision check ──► coherence check ──►  │    │
│  │                 uncertainty check ──► binding strength   │    │
│  │                                       ──► top N winners  │    │
│  └─────────────────────────────────────────────────────────┘    │
│  binding_capacity: int (configurable, default=7)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Entities

### PrecisionProfile (NEW)

**Purpose**: Global precision state broadcast to all inference layers (the Φ parameter).

```python
class PrecisionProfile(BaseModel):
    """Global precision state across all inference layers."""
    
    # Core precision weights
    layer_precisions: dict[str, float] = Field(
        default_factory=dict,
        description="Precision weight per inference layer (0-1)"
    )
    modality_precisions: dict[str, float] = Field(
        default_factory=dict,
        description="Precision weight per sensory modality (0-1)"
    )
    
    # Temporal scope
    temporal_depth: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How far into future to weight predictions (0=immediate, 1=long-term)"
    )
    
    # Meta-level confidence
    meta_precision: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in this precision profile itself"
    )
    
    # Context for learning
    context_embedding: list[float] = Field(
        default_factory=list,
        description="Embedding of context that generated this profile"
    )
    
    # Tracking
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: str | None = Field(default=None, description="OODA cycle that generated this")
```

**Validation Rules**:
- All precision values must be in [0, 1]
- layer_precisions keys must match known layer IDs
- context_embedding dimension must match system embedding size (default: 768)

**State Transitions**:
- Created by `HyperModelService.forecast_precision_profile()`
- Broadcast via `EventBus` to all layers
- Updated by `HyperModelService.update_hyper_model()`

---

### EpistemicState (NEW)

**Purpose**: Track current epistemic depth/luminosity level (recursive self-knowing).

```python
class EpistemicState(BaseModel):
    """Current epistemic depth/luminosity level."""
    
    # Primary metric
    depth_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How 'aware' the system is of its own processing"
    )
    
    # Reality model integration
    reality_model_coherence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How unified the current gestalt is"
    )
    
    # Binding state
    active_bindings: list[str] = Field(
        default_factory=list,
        description="IDs of inferences currently bound into consciousness"
    )
    transparent_processes: list[str] = Field(
        default_factory=list,
        description="IDs of processes running but not 'known'"
    )
    
    # Decomposition
    luminosity_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Contribution of each factor to overall luminosity"
    )
    
    # Tracking
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Validation Rules**:
- depth_score = weighted average of luminosity_factors
- active_bindings.length <= binding_capacity
- No overlap between active_bindings and transparent_processes

**Luminosity Factors**:
- `hyper_model_active`: Is hyper-model forecasting? (0 or 1)
- `bidirectional_sharing`: Fraction of layers sharing precision info
- `meta_precision_level`: Current meta_precision from PrecisionProfile
- `binding_coherence`: Average coherence of bound inferences

---

### PrecisionError (NEW)

**Purpose**: Second-order error recording for hyper-model learning.

```python
class PrecisionError(BaseModel):
    """Second-order error on precision forecast."""
    
    # Location
    layer_id: str = Field(description="Which layer this error occurred at")
    
    # Error computation
    predicted_precision: float = Field(
        ge=0.0,
        le=1.0,
        description="What the hyper-model predicted"
    )
    actual_precision_needed: float = Field(
        ge=0.0,
        le=1.0,
        description="What precision was actually required"
    )
    
    # Derived metrics
    error_magnitude: float = Field(
        ge=0.0,
        description="Absolute difference |predicted - actual|"
    )
    error_direction: Literal["over_confident", "under_confident"] = Field(
        description="Whether we predicted too high or too low"
    )
    
    # Context
    context_hash: str = Field(
        default="",
        description="Hash of context for grouping similar errors"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @model_validator(mode='after')
    def compute_derived(self) -> 'PrecisionError':
        self.error_magnitude = abs(self.predicted_precision - self.actual_precision_needed)
        self.error_direction = (
            "over_confident" if self.predicted_precision > self.actual_precision_needed
            else "under_confident"
        )
        return self
```

**Validation Rules**:
- error_magnitude = |predicted - actual|
- error_direction derived from sign of (predicted - actual)

---

### BoundInference (NEW)

**Purpose**: An inference that passed Bayesian binding competition.

```python
class BoundInference(BaseModel):
    """An inference that passed binding competition."""
    
    # Identity
    inference_id: str = Field(description="Unique identifier")
    source_layer: str = Field(description="Which layer generated this inference")
    
    # Content
    content: dict = Field(
        default_factory=dict,
        description="The inference payload (layer-specific)"
    )
    embedding: list[float] = Field(
        default_factory=list,
        description="Vector representation for coherence computation"
    )
    
    # Binding metrics (all [0,1])
    precision_score: float = Field(ge=0.0, le=1.0)
    coherence_score: float = Field(ge=0.0, le=1.0)
    uncertainty_reduction: float = Field(
        description="How much this reduces overall uncertainty (can be negative)"
    )
    
    # Combined score
    binding_strength: float = Field(
        ge=0.0,
        description="Product of precision * coherence * max(0, uncertainty_reduction)"
    )
    
    # Tracking
    bound_at: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: str | None = Field(default=None)
    
    @model_validator(mode='after')
    def compute_binding_strength(self) -> 'BoundInference':
        self.binding_strength = (
            self.precision_score * 
            self.coherence_score * 
            max(0.0, self.uncertainty_reduction)
        )
        return self
```

**Validation Rules**:
- binding_strength = precision * coherence * max(0, uncertainty_reduction)
- If uncertainty_reduction < 0, binding_strength = 0 (FR-008)

---

### UnifiedRealityModel (NEW)

**Purpose**: Single container unifying all active inference states, belief states, and metacognitive states.

```python
class UnifiedRealityModel(BaseModel):
    """Unified world model container for conscious experience."""
    
    # State containers (reference existing models)
    belief_states: list[BeliefState] = Field(default_factory=list)
    active_inference_states: list[ActiveInferenceState] = Field(default_factory=list)
    metacognitive_particles: list[MetacognitiveParticle] = Field(default_factory=list)
    
    # Bound content
    bound_inferences: list[BoundInference] = Field(default_factory=list)
    
    # Derived metrics
    coherence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How well-integrated the unified state is"
    )
    
    # Epistemic affordances
    epistemic_affordances: list[str] = Field(
        default_factory=list,
        description="Possible actions derivable from current state"
    )
    
    # Context
    current_context: dict = Field(
        default_factory=dict,
        description="Current task/environment context"
    )
    
    # Tracking
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: str | None = Field(default=None)
    
    def compute_coherence(self) -> float:
        """Compute coherence as average pairwise similarity of bound inferences."""
        if len(self.bound_inferences) < 2:
            return 1.0
        
        similarities = []
        for i, inf1 in enumerate(self.bound_inferences):
            for inf2 in self.bound_inferences[i+1:]:
                sim = cosine_similarity(inf1.embedding, inf2.embedding)
                similarities.append(sim)
        
        # Normalize to [0, 1]
        return (sum(similarities) / len(similarities) + 1) / 2
```

**Validation Rules**:
- len(bound_inferences) <= binding_capacity
- coherence_score recomputed on any bound_inferences change
- epistemic_affordances derived from bound beliefs and context

---

## Event Types (NEW)

### PrecisionForecastEvent

```python
class PrecisionForecastEvent(CognitiveEvent):
    """Emitted at OODA cycle start with new precision profile."""
    event_type: Literal["precision_forecast"] = "precision_forecast"
    precision_profile: PrecisionProfile
    cycle_id: str
```

### PrecisionErrorEvent

```python
class PrecisionErrorEvent(CognitiveEvent):
    """Emitted at OODA cycle end with precision errors."""
    event_type: Literal["precision_error"] = "precision_error"
    errors: list[PrecisionError]
    cycle_id: str
```

### PrecisionUpdateEvent

```python
class PrecisionUpdateEvent(CognitiveEvent):
    """Emitted after hyper-model update with new Φ."""
    event_type: Literal["precision_update"] = "precision_update"
    new_profile: PrecisionProfile
    learning_delta: float  # How much the model changed
```

### BindingCompletedEvent

```python
class BindingCompletedEvent(CognitiveEvent):
    """Emitted when Bayesian binding competition completes."""
    event_type: Literal["binding_completed"] = "binding_completed"
    bound_count: int
    rejected_count: int
    average_binding_strength: float
    cycle_id: str
```

---

## Configuration Entities

### BindingConfig

```python
class BindingConfig(BaseModel):
    """Configuration for Bayesian binding."""
    min_capacity: int = Field(default=5, ge=1)
    max_capacity: int = Field(default=9, ge=1)
    default_capacity: int = Field(default=7, ge=1)
    
    precision_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    coherence_threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    
    def get_capacity(self, task_complexity: float) -> int:
        """Higher complexity → lower capacity (more selective)."""
        span = self.max_capacity - self.min_capacity
        return int(self.max_capacity - (task_complexity * span))
```

### HyperModelConfig

```python
class HyperModelConfig(BaseModel):
    """Configuration for hyper-model learning."""
    base_learning_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    min_learning_rate: float = Field(default=0.01, ge=0.0)
    max_learning_rate: float = Field(default=0.3, le=1.0)
    
    # Default layer IDs
    default_layers: list[str] = Field(
        default=["perception", "reasoning", "metacognition", "action"]
    )
    
    # Default modality IDs
    default_modalities: list[str] = Field(
        default=["visual", "semantic", "procedural", "episodic"]
    )
```

---

## Relationships Summary

| Entity | Relates To | Relationship |
|--------|-----------|--------------|
| UnifiedRealityModel | BeliefState | Contains (1:N) |
| UnifiedRealityModel | ActiveInferenceState | Contains (1:N) |
| UnifiedRealityModel | MetacognitiveParticle | Contains (1:N) |
| UnifiedRealityModel | BoundInference | Contains (1:N, max=capacity) |
| PrecisionProfile | PrecisionError | Generates (1:N per cycle) |
| PrecisionProfile | EpistemicState | Influences (1:1) |
| BoundInference | PrecisionProfile | Evaluated by (N:1) |
| HyperModelService | PrecisionProfile | Produces (1:N) |
| HyperModelService | EpistemicState | Maintains (1:1) |
| BayesianBinder | BoundInference | Produces (1:N) |
| EventBus | *Event types | Routes (1:N) |
