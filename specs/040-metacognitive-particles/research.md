# Research: Metacognitive Particles Integration

**Feature**: 040-metacognitive-particles
**Date**: 2025-12-30

## Research Summary

All technical decisions resolved. No NEEDS CLARIFICATION remaining.

---

## R1: Particle Classification Algorithm

**Question**: How to classify cognitive processes into particle types?

**Decision**: Structural analysis of Markov blanket configuration.

**Rationale**: Per Sandved-Smith & Da Costa (2024), particle type is determined by blanket structure:

| Type | Structural Signature |
|------|---------------------|
| Cognitive | Has μ → Q_μ(η) belief mapping |
| Passive Metacognitive | μ^(2) exists, no a^(2) paths to μ^(1) |
| Active Metacognitive | Has internal blanket b^(2) = (s^(2), a^(2)) |
| Strange | a^(1) does NOT influence μ^(1) directly |
| Nested (N-level) | N internal Markov blankets detected |

**Algorithm**:
```python
def classify_particle(blanket: MarkovBlanket) -> ParticleType:
    if not has_belief_mapping(blanket):
        return ParticleType.SIMPLE
    if not has_internal_blanket(blanket):
        return ParticleType.COGNITIVE
    if not has_active_paths_to_internal(blanket):
        return ParticleType.PASSIVE_METACOGNITIVE
    if is_strange_configuration(blanket):
        return ParticleType.STRANGE
    n_levels = count_nested_blankets(blanket)
    if n_levels > 1:
        return ParticleType.NESTED_N_LEVEL
    return ParticleType.ACTIVE_METACOGNITIVE
```

**Alternatives Rejected**:
- Behavioral pattern analysis: Requires runtime observation, not deterministic
- Manual annotation: Doesn't scale, prone to inconsistency

---

## R2: KL Divergence for Agency Strength

**Question**: How to compute sense of agency as per Eq.20?

**Decision**: Use scipy.stats.entropy for discrete case, analytical formula for Gaussian.

**Rationale**: Eq.20 defines agency strength as:
```
D_KL[Q(μ¹,a¹) | Q(μ¹)Q(a¹)]
```

For discrete distributions:
```python
from scipy.stats import entropy
agency_strength = entropy(Q_joint.flatten(), Q_independent.flatten())
```

For Gaussian distributions (closed-form):
```python
def kl_divergence_gaussian(p: BeliefState, q: BeliefState) -> float:
    d = len(p.mean)
    diff = q.mean - p.mean
    return 0.5 * (
        np.trace(np.linalg.inv(q.precision) @ p.precision) +
        diff @ q.precision @ diff - d +
        np.log(np.linalg.det(q.precision) / np.linalg.det(p.precision))
    )
```

**Alternatives Rejected**:
- PyTorch KL: Adds ML framework dependency unnecessarily
- Custom implementation: scipy is well-tested and maintained

---

## R3: Epistemic Gain Detection Threshold

**Question**: What threshold for "Aha!" moment detection?

**Decision**: Default 0.3 (30% uncertainty reduction), with adaptive mode.

**Rationale**:
- Spec assumption: 0.3 is reasonable for general cognitive operations
- Adaptive formula: `threshold = mean(historical_gains) + std(historical_gains)`
- Prevents "never triggered" in low-variance domains
- Prevents "always triggered" in high-variance domains

**Configuration**:
```python
EPISTEMIC_GAIN_THRESHOLD = float(os.getenv("EPISTEMIC_GAIN_THRESHOLD", "0.3"))
EPISTEMIC_GAIN_ADAPTIVE = os.getenv("EPISTEMIC_GAIN_ADAPTIVE", "false").lower() == "true"
```

**Alternatives Rejected**:
- Fixed-only threshold: Doesn't adapt to domain characteristics
- ML-based detection: Overengineered for MVP, adds training complexity

---

## R4: Precision Modulation Bounds

**Question**: What bounds for precision values?

**Decision**: [0.01, 100.0] with log-scale storage.

**Rationale**:
- Precision = inverse variance = confidence weighting
- 0.01: Very uncertain, open to all information
- 100.0: Very certain, laser focus on specific beliefs
- Log scale prevents numerical instability in gradient computations

**Implementation**:
```python
MIN_PRECISION = 0.01
MAX_PRECISION = 100.0

def clamp_precision(precision: float) -> float:
    return max(MIN_PRECISION, min(MAX_PRECISION, precision))
```

**Alternatives Rejected**:
- Unbounded: Causes numerical overflow/underflow
- [0,1] normalized: Loses interpretability as inverse variance

---

## R5: Cognitive Core Nesting Limit

**Question**: Maximum nesting depth for metacognitive hierarchies?

**Decision**: 5 levels, configurable via environment variable.

**Rationale**:
- Free energy principle limits useful depth (complexity cost exceeds accuracy gain)
- 5 levels = μ¹ → μ² → μ³ → μ⁴ → μ⁵ (cognitive core)
- Per paper: "I can never conceive what it is like to be me" (innermost limit)

**Configuration**:
```python
MAX_NESTING_DEPTH = int(os.getenv("METACOGNITIVE_MAX_DEPTH", "5"))
```

**Enforcement**:
```python
def enforce_cognitive_core(particle: MetacognitiveParticle) -> None:
    if particle.level >= MAX_NESTING_DEPTH:
        raise CognitiveCoreViolation(
            f"Cannot create metacognitive level {particle.level + 1}. "
            f"Cognitive core reached at level {MAX_NESTING_DEPTH}."
        )
```

**Alternatives Rejected**:
- Unlimited with warning: Violates theoretical constraint
- Fixed 3 levels: Too restrictive for complex self-modeling

---

## Dependencies Verified

| Dependency | Status | Location |
|------------|--------|----------|
| MarkovBlanket | EXISTS | api/models/markov_blanket.py |
| MetacognitionAgent | EXISTS | api/agents/metacognition_agent.py |
| EFE Engine | EXISTS | api/services/efe_engine.py |
| scipy | AVAILABLE | pip install scipy |
| numpy | AVAILABLE | Already in requirements |

---

## Conclusion

All research tasks complete. No blockers for Phase 1 design.
