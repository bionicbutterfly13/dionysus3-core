# Quickstart: Beautiful Loop Hyper-Model

**Feature Branch**: `056-beautiful-loop-hyper`
**Date**: 2026-01-05

---

## Overview

The Beautiful Loop implements three conditions for consciousness from Laukkonen et al. (2025):

1. **Unified Reality Model** - Single container for all cognitive states
2. **Bayesian Binding** - Precision-weighted inferential competition
3. **Epistemic Depth** - Recursive self-knowing via hyper-model precision forecasting

---

## Quick Integration

### 1. Import Core Components

```python
from api.models.beautiful_loop import (
    PrecisionProfile,
    EpistemicState,
    PrecisionError,
    BoundInference,
)
from api.services.unified_reality_model import UnifiedRealityModel
from api.services.bayesian_binder import BayesianBinder
from api.services.hyper_model_service import HyperModelService
from api.services.epistemic_field_service import EpistemicFieldService
```

### 2. Initialize Services

```python
from api.utils.event_bus import EventBus
from api.services.active_inference_service import ActiveInferenceService

# Reuse existing services
event_bus = EventBus()
active_inference = ActiveInferenceService()

# Initialize new services
hyper_model = HyperModelService(event_bus=event_bus)
binder = BayesianBinder(event_bus=event_bus)
reality_model = UnifiedRealityModel()
epistemic_field = EpistemicFieldService(hyper_model=hyper_model)
```

### 3. Run Beautiful Loop in OODA Cycle

```python
async def enhanced_ooda_cycle(observations):
    # Step 1: Forecast precision profile
    phi = await hyper_model.forecast_precision_profile(
        context=reality_model.current_context,
        internal_states=get_layer_states(),
        recent_errors=recent_precision_errors
    )
    
    # Step 2: Run inference with precision weighting
    candidates = await perception_agent.observe(observations, precision=phi)
    
    # Step 3: Bayesian binding
    bound = await binder.bind(
        candidates=candidates,
        reality_model=reality_model,
        precision_profile=phi
    )
    
    # Step 4: Update reality model
    reality_model.integrate(bound)
    
    # Step 5: Compute precision errors
    errors = await hyper_model.compute_precision_errors(
        predicted_phi=phi,
        actual_errors=collect_prediction_errors()
    )
    
    # Step 6: Update hyper-model (learning)
    await hyper_model.update_hyper_model(errors)
    
    # Step 7: Broadcast new Φ for next cycle
    new_phi = await hyper_model.forecast_precision_profile(...)
    await hyper_model.broadcast_phi(new_phi)
    
    return action
```

---

## API Endpoints

### Precision Management

```bash
# Forecast precision profile
curl -X POST http://localhost:8000/api/v1/beautiful-loop/precision/forecast \
  -H "Content-Type: application/json" \
  -d '{"context": {"task": "analysis", "complexity": 0.7}}'

# Get current precision profile
curl http://localhost:8000/api/v1/beautiful-loop/precision/profile

# Record precision errors
curl -X POST http://localhost:8000/api/v1/beautiful-loop/precision/errors \
  -H "Content-Type: application/json" \
  -d '{"errors": [...], "cycle_id": "cycle-123"}'
```

### Binding Operations

```bash
# Evaluate binding candidates
curl -X POST http://localhost:8000/api/v1/beautiful-loop/binding/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {"inference_id": "inf-1", "source_layer": "perception", "embedding": [0.1, 0.2, ...]}
    ],
    "binding_capacity": 7
  }'
```

### Reality Model

```bash
# Get unified reality model
curl http://localhost:8000/api/v1/beautiful-loop/reality-model

# Get coherence score
curl http://localhost:8000/api/v1/beautiful-loop/reality-model/coherence
```

### Epistemic State

```bash
# Get epistemic state (luminosity)
curl http://localhost:8000/api/v1/beautiful-loop/epistemic/state

# Get depth score only
curl http://localhost:8000/api/v1/beautiful-loop/epistemic/depth
```

---

## Configuration

### Binding Configuration

```python
from api.models.beautiful_loop import BindingConfig

config = BindingConfig(
    min_capacity=5,          # Minimum binding slots
    max_capacity=9,          # Maximum binding slots  
    default_capacity=7,      # Default (Miller's 7±2)
    precision_threshold=0.3, # Minimum precision to consider
    coherence_threshold=0.4  # Minimum coherence to bind
)
```

### Hyper-Model Configuration

```python
from api.models.beautiful_loop import HyperModelConfig

config = HyperModelConfig(
    base_learning_rate=0.1,   # EMA alpha base
    min_learning_rate=0.01,   # Prevents stagnation
    max_learning_rate=0.3,    # Prevents instability
    default_layers=["perception", "reasoning", "metacognition", "action"],
    default_modalities=["visual", "semantic", "procedural", "episodic"]
)
```

---

## Event Bus Integration

### Subscribe to Precision Events

```python
from api.utils.event_bus import EventBus

event_bus = EventBus()

# React to new precision forecasts
@event_bus.subscribe("precision_forecast")
async def on_precision_forecast(event):
    phi = event.precision_profile
    # Apply new precision weights to inference layer
    
# React to precision updates (post-learning)
@event_bus.subscribe("precision_update")
async def on_precision_update(event):
    new_phi = event.new_profile
    learning_delta = event.learning_delta
    # Log or react to hyper-model learning
```

### Emit Events

```python
from api.models.beautiful_loop import PrecisionForecastEvent

await event_bus.emit(PrecisionForecastEvent(
    precision_profile=phi,
    cycle_id="cycle-123"
))
```

---

## Testing

### Run Unit Tests

```bash
# All Beautiful Loop tests
pytest tests/unit/test_beautiful_loop*.py -v

# Specific component
pytest tests/unit/test_hyper_model_service.py -v
pytest tests/unit/test_bayesian_binder.py -v
pytest tests/unit/test_unified_reality_model.py -v

# With coverage
pytest tests/unit/test_beautiful_loop*.py --cov=api.services --cov=api.models --cov-report=term-missing
```

### Run Integration Tests

```bash
pytest tests/integration/test_beautiful_loop_ooda.py -v
```

### Performance Tests

```bash
# Verify <50ms forecast time (SC-001)
pytest tests/unit/test_hyper_model_service.py::test_forecast_performance -v

# Verify <10% OODA latency increase (SC-006)
pytest tests/integration/test_beautiful_loop_ooda.py::test_ooda_latency -v
```

---

## Success Criteria Verification

| Criterion | Test Command |
|-----------|--------------|
| SC-001: <50ms forecast | `pytest -k "test_forecast_performance"` |
| SC-002: 95% binding consistency | `pytest -k "test_binding_consistency"` |
| SC-003: 20% error reduction | `pytest -k "test_learning_curve"` |
| SC-004: Coherence correlation | `pytest -k "test_coherence_correlation"` |
| SC-005: State differentiation | `pytest -k "test_state_differentiation"` |
| SC-006: <10% latency increase | `pytest -k "test_ooda_latency"` |
| SC-007: No regression | `pytest tests/ --ignore=tests/unit/test_beautiful_loop*` |
| SC-008: >90% coverage | `pytest --cov --cov-fail-under=90` |

---

## Troubleshooting

### Common Issues

**Precision forecast too slow (>50ms)**
- Check context_embedding dimension (should be 768)
- Reduce number of layers/modalities
- Profile with `cProfile` to identify bottleneck

**Binding returns empty**
- Lower `precision_threshold` (default 0.3)
- Lower `coherence_threshold` (default 0.4)
- Check that candidates have valid embeddings

**Hyper-model not learning**
- Verify precision errors are being recorded
- Check `learning_delta` in PrecisionErrorsResponse
- Ensure `base_learning_rate` > 0

**Coherence always 1.0**
- Need at least 2 bound inferences for pairwise comparison
- Check that embeddings are not all identical

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         OODA Cycle                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   OBSERVE    │───►│    ORIENT    │───►│    DECIDE    │      │
│  │              │    │              │    │              │      │
│  │ + Precision  │    │ + Bayesian   │    │ + Epistemic  │      │
│  │   Forecast   │    │   Binding    │    │   Depth      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              UnifiedRealityModel                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────────┐  │   │
│  │  │ Beliefs │ │ Active  │ │ Meta-   │ │ Bound         │  │   │
│  │  │         │ │Inference│ │cognitive│ │ Inferences    │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   HyperModelService                      │   │
│  │  forecast() → apply() → compute_errors() → update()     │   │
│  │                         ↓                                │   │
│  │                  EpistemicState                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼ EventBus                        │
│  ┌──────────────┐                            ┌──────────────┐  │
│  │     ACT      │◄───── Precision Update ────│   Next Cycle │  │
│  └──────────────┘                            └──────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
