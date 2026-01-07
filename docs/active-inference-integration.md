# ActiveInference.jl Integration - Complete Guide

**Status**: ✅ Production Ready
**Date**: 2026-01-03
**Author**: Mani Saint-Victor, MD

---

## Executive Summary

Dionysus now uses **ActiveInference.jl** (Nehrer et al., 2025) as the field-standard computational backend for active inference algorithms. This ensures field credibility while maintaining Python integration in the Dionysus architecture.

**Key Achievement**: Field-respected Julia implementation wrapped in Python service layer.

---

## Installation Complete

✅ **Julia 1.12.3** installed via Homebrew
✅ **PyJulia bridge** configured
✅ **ActiveInference.jl** package installed
✅ **Python service wrapper** created (`api/services/active_inference_service.py`)
✅ **Integration tested** (5/5 tests passing)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Dionysus Python Layer                                  │
│  - ThoughtSeeds framework                               │
│  - Cognitive services                                   │
│  - API endpoints                                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  ActiveInferenceService (api/services/)                 │
│  - Python wrapper for Julia functions                   │
│  - Type conversion (numpy ↔ Julia arrays)               │
│  - ThoughtSeed integration layer                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼ PyJulia Bridge
┌─────────────────────────────────────────────────────────┐
│  Julia Runtime (1.12.3)                                 │
│  - ActiveInference.jl package                           │
│  - Field-standard algorithms                            │
│  - POMDP generative models                              │
│  - VFE/EFE calculations                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Thoughtseeds ↔ ActiveInference.jl Equation Mapping

### Core Mappings

| Thoughtseeds Concept | Equation | ActiveInference.jl Function | Implementation |
|----------------------|----------|---------------------------|----------------|
| **NP Free Energy** | Eq 3: F_i = D_KL[q(μ_i) ‖ p(μ_i \| s_i)] | `calculate_vfe(belief, obs, model)` | ✅ Implemented |
| **TS Policy Selection** | Eq 13: TS_dominant = argmin F_m | `infer_policies(belief, model, γ)` | ✅ Implemented |
| **Active Pool** | Eq 12: A_pool = {TS \| α ≥ τ} | `select_dominant_thoughtseed()` | ✅ Implemented |
| **POMDP A Matrix** | Eq 6: P(o\|s) | `GenerativeModel.A` | ✅ Implemented |
| **POMDP B Matrix** | Eq 6: P(s'\|s,a) | `GenerativeModel.B` | ✅ Implemented |
| **Goal Preferences** | Eq 16: G_agent | `GenerativeModel.C` | ✅ Implemented |
| **State Prior** | Eq 2: P(s_0) | `GenerativeModel.D` | ✅ Implemented |

### Detailed Equation Mappings

#### 1. Neuronal Packet Free Energy (Kavi et al., Eq 3)

**Thoughtseeds**:
```
F_i = D_KL[q(μ_i) || p(μ_i | s_i, a_i, θ_i, K_i, S_i)]
      - E_q[log p(s_i, a_i | μ_i, θ_i, KD_parent, K_i, S_i)]
```

**ActiveInference.jl** (Nehrer et al., Eq 5):
```
F = D_{KL}[q(s) || p(o,s)]
```

**Python Service**:
```python
vfe = service.calculate_vfe(
    belief=BeliefState(qs=posterior_states),
    observation=observed_outcome,
    model=generative_model
)
```

**Maps to**:
- `q(μ_i)` → `belief.qs` (posterior belief over states)
- `s_i` → `observation` (sensory input)
- `F_i` → `vfe` (scalar free energy value)

---

#### 2. ThoughtSeed Policy Selection (Kavi et al., Eq 13)

**Thoughtseeds**:
```
TS_dominant = argmin_{TS_m ∈ A_pool} F_m
```

**ActiveInference.jl** (Nehrer et al., Eq 17-18):
```
π* = argmin_π G(π)
where G(π) = E[D_{KL}[q(o|π) || p(o*)]]  (pragmatic)
           - E[H[q(s|π)]]                 (epistemic)
```

**Python Service**:
```python
dominant_ts = service.select_dominant_thoughtseed(
    thoughtseeds=active_thoughtseeds,
    threshold=activation_threshold
)
```

**Algorithm**:
1. Filter active pool: `{TS | activation_level ≥ threshold}`
2. Calculate VFE for each TS in pool
3. Select TS with minimum VFE
4. Return dominant TS

---

#### 3. Expected Free Energy (Kavi et al., Eq 17.3)

**Thoughtseeds**:
```
EFE_agent = Σ_{TS_m ∈ A_pool} (α_m × EFE_m)
```

**ActiveInference.jl** (Nehrer et al., Eq 17):
```
EFE(π) = Pragmatic Value - Epistemic Value
```

**Python Service**:
```python
efe = service.calculate_efe(
    belief=current_belief,
    model=generative_model,
    policy=policy_sequence,
    horizon=planning_horizon
)
```

**Decomposition**:
- **Pragmatic**: Preference satisfaction `D_KL[q(o|π) || C]`
- **Epistemic**: Information gain `H[q(o)] - E[H[q(o|s)]]`

---

#### 4. Knowledge Domain Generative Model (Kavi et al., Eq 6)

**Thoughtseeds**:
```
P(a_k, s_k, μ_k, C_k, v_k, r_k | θ_k, TS_parent)
```

**ActiveInference.jl** (Nehrer et al., Eq 1):
```
POMDP = (S, A, O, T, R, Ω)
where:
  S: State space
  A: Action space
  O: Observation space
  T: Transition model (B matrix)
  R: Reward/preference (C matrix)
  Ω: Observation model (A matrix)
```

**Python Service**:
```python
model = GenerativeModel(
    A=observation_likelihood,  # P(o|s)
    B=transition_dynamics,     # P(s'|s,a)
    C=preferences,             # P(o*)
    D=state_prior             # P(s_0)
)
```

**Component Mapping**:
- `s_k` → States `S`
- `a_k` → Actions `A`
- `C_k` → Observations `O` (content of consciousness)
- `θ_k` → Parameters embedded in A, B, C, D matrices

---

## Usage Examples

### Example 1: Basic State Inference

```python
from api.services.active_inference_service import (
    get_active_inference_service,
    GenerativeModel,
    BeliefState
)
import numpy as np

# Initialize service
service = get_active_inference_service()

# Create generative model
model = service.create_simple_model(
    num_states=3,
    num_observations=2,
    num_actions=2
)

# Create prior belief (uniform)
prior = BeliefState(qs=np.array([0.33, 0.33, 0.34]))

# Observe outcome 0
observation = 0

# Infer states (VFE minimization)
posterior = service.infer_states(
    observation=observation,
    model=model,
    prior_belief=prior.qs
)

print(f"Posterior belief: {posterior.qs}")
print(f"VFE: {service.calculate_vfe(posterior, observation, model)}")
```

### Example 2: ThoughtSeed Competition

```python
# Create multiple thoughtseeds
thoughtseeds = []

for i in range(5):
    model = service.create_simple_model(2, 2, 2)

    ts = {
        'id': f'ts_{i}',
        'activation_level': np.random.uniform(0.3, 0.9),
        'belief_state': BeliefState(qs=np.random.dirichlet([1, 1])),
        'observation': np.random.randint(0, 2),
        'generative_model': model
    }
    thoughtseeds.append(ts)

# Select dominant via VFE minimization (Eq 13)
dominant = service.select_dominant_thoughtseed(
    thoughtseeds,
    threshold=0.5
)

print(f"Dominant: {dominant['id']}")
print(f"Activation: {dominant['activation_level']:.2f}")
```

### Example 3: Policy Planning with EFE

```python
# Set up model with preferences
model = service.create_simple_model(2, 2, 2)
model.C = np.array([[0.9], [0.1]])  # Prefer observation 0

# Current belief
belief = BeliefState(qs=np.array([0.6, 0.4]))

# Evaluate policy: [action 0, action 1, action 0]
policy = np.array([0, 1, 0])

# Calculate EFE (Eq 17)
efe = service.calculate_efe(
    belief=belief,
    model=model,
    policy=policy,
    horizon=3
)

print(f"EFE for policy {policy}: {efe:.4f}")
```

---

## Integration with Existing Dionysus Services

### ThoughtSeed Service Integration

```python
# api/services/thoughtseed_service.py

from api.services.active_inference_service import get_active_inference_service

class ThoughtSeedService:
    def __init__(self):
        self.active_inference = get_active_inference_service()

    async def compete_thoughtseeds(self, thoughtseeds):
        """
        ThoughtSeed competition via active inference (Eq 12-13).

        Maps Thoughtseeds to active inference framework:
        - activation_level → threshold filtering
        - belief_state → posterior q(s)
        - VFE → competition metric
        """
        # Convert ThoughtSeeds to active inference format
        ai_thoughtseeds = []
        for ts in thoughtseeds:
            ai_ts = {
                'id': str(ts.id),
                'activation_level': ts.activation_level,
                'belief_state': self._convert_to_belief(ts),
                'observation': ts.current_observation,
                'generative_model': ts.generative_model
            }
            ai_thoughtseeds.append(ai_ts)

        # Select dominant (Eq 13)
        dominant = self.active_inference.select_dominant_thoughtseed(
            ai_thoughtseeds,
            threshold=ts.activation_threshold
        )

        return dominant
```

---

## Testing

### Test Suite: `scripts/test_active_inference_integration.py`

**Results**: ✅ 5/5 tests passing

1. **Julia Loading** - Verifies Julia runtime and ActiveInference.jl available
2. **Generative Model** - Creates POMDP models with A, B, C, D matrices
3. **VFE Calculation** - Computes variational free energy (Eq 3, 5)
4. **EFE Calculation** - Computes expected free energy (Eq 17-18)
5. **ThoughtSeed Selection** - Selects dominant via VFE minimization (Eq 13)

**Run tests**:
```bash
python scripts/test_active_inference_integration.py
```

---

## Performance Characteristics

### Computational Cost

| Operation | Complexity | Notes |
|-----------|------------|-------|
| VFE calculation | O(S) | S = number of states |
| EFE calculation | O(H × S²) | H = horizon, S = states |
| State inference | O(I × S) | I = iterations (~16) |
| Policy inference | O(P × H × S²) | P = policies |

### Memory Footprint

- Julia runtime: ~750 MB
- ActiveInference.jl package: ~100 MB
- Python service overhead: ~10 MB
- **Total**: ~860 MB (acceptable for VPS deployment)

### Lazy Loading

Service uses lazy initialization - Julia only loads when first needed:

```python
service = get_active_inference_service(lazy_load=True)  # No Julia load
result = service.calculate_vfe(...)  # Julia loads here
```

---

## References

### Primary Implementation

**Nehrer, S. W., Laursen, J. E., Heins, C., Friston, K., Mathys, C., & Waade, P. T. (2025)**. Introducing ActiveInference.jl: A Julia Library for Simulation and Parameter Estimation with Active Inference Models. *Entropy*, 27(1), 62. [https://doi.org/10.3390/e27010062](https://doi.org/10.3390/e27010062)

### Theoretical Foundation

**Kavi, P. C., Zamora-López, G., & Friedman, D. A. (2025)**. From Neuronal Packets to Thoughtseeds: A Hierarchical Model of Embodied Cognition in the Global Workspace.

**Friston, K. J. (2010)**. The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127-138.

### Supporting Implementations

- **pymdp**: Python active inference library (reference implementation)
- **SPM DEM**: MATLAB canonical implementation (Friston lab)
- **RxInfer.jl**: High-performance alternative (factor graphs)

---

## Field Credibility

**Why ActiveInference.jl**:

1. ✅ **Peer-reviewed publication** (Entropy, 2025)
2. ✅ **Computational Psychiatry standard** (field-recognized)
3. ✅ **Exact algorithms** - matches theoretical papers
4. ✅ **Active development** - released January 2025
5. ✅ **Integration with Turing.jl** - Bayesian inference ecosystem

**Comparison to alternatives**:

| Implementation | Language | Status | Field Adoption |
|----------------|----------|--------|----------------|
| **ActiveInference.jl** | Julia | ✅ Using | High (2025) |
| pymdp | Python | Reference | Medium |
| SPM DEM | MATLAB | Gold standard | Very High |
| RxInfer.jl | Julia | Alternative | Medium |

**Result**: Using ActiveInference.jl ensures Dionysus implements field-standard active inference while maintaining Python architecture.

---

## Troubleshooting

### Issue: Julia not loading

**Solution**:
```bash
# Reconfigure PyJulia
source .venv/bin/activate
python -c "import julia; julia.install()"
```

### Issue: ActiveInference.jl not found

**Solution**:
```bash
julia -e 'using Pkg; Pkg.add(url="https://github.com/ComputationalPsychiatry/ActiveInference.jl.git")'
```

### Issue: VFE/EFE calculations seem incorrect

**Check**:
1. Generative model matrices are valid probability distributions (rows sum to 1)
2. Belief states are normalized (sum to 1)
3. Observations are valid indices (0 to num_obs-1)

---

## Future Enhancements

### Phase 2 (Planned)

1. **Direct Julia function calls** - Bypass Python wrapper for performance
2. **GPU acceleration** - Use CUDA.jl for large-scale models
3. **Hierarchical models** - Multi-level POMDP nesting
4. **Parameter learning** - Dirichlet updates for A, B matrices (Eq 19-20 from paper)

### Phase 3 (Research)

1. **Continuous state spaces** - Extend beyond discrete POMDPs
2. **Deep active inference** - Neural network function approximators
3. **Multi-agent coordination** - ThoughtSeed social dynamics

---

## Summary

✅ **Julia 1.12.3 + ActiveInference.jl installed**
✅ **Python service wrapper created**
✅ **5/5 integration tests passing**
✅ **ThoughtSeeds equations mapped to Julia functions**
✅ **Field-standard algorithms ensure credibility**

**Dionysus now implements active inference using the computational neuroscience field standard while maintaining Python architecture integration.**

---

**Maintained by**: Dionysus3-core team
**Last updated**: 2026-01-03
**Next review**: After Phase 2 enhancements
