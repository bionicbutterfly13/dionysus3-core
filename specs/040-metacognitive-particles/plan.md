# Implementation Plan: Metacognitive Particles Integration

**Branch**: `040-metacognitive-particles` | **Date**: 2025-12-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/040-metacognitive-particles/spec.md`

## Summary

Integrate theoretical frameworks from two academic papers (Sandved-Smith & Da Costa 2024, Seragnoli et al. 2025) into Dionysus cognitive architecture. Implements particle type classification, mental actions via precision modulation, sense of agency computation (KL divergence), epistemic gain detection, cognitive core enforcement, and procedural metacognition. Leverages existing infrastructure: markov_blanket.py, metacognition_agent.py, efe_engine.py.

## Technical Context

**Language/Version**: Python 3.11+ (async/await, Pydantic v2)
**Primary Dependencies**: FastAPI, smolagents, Pydantic v2, numpy, scipy (for KL divergence)
**Storage**: Neo4j via n8n webhooks (Graphiti for direct access as approved exception)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux server (VPS deployment via Docker)
**Project Type**: Single monolith (api/ directory structure)
**Performance Goals**: <200ms latency for all metacognitive operations (per SC-006)
**Constraints**: Real-time agency scoring within 100ms (SC-001), epistemic gain within 50ms (SC-003)
**Scale/Scope**: Integration with existing agent pool, 5-level max nesting depth

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Existing Infrastructure | PASS | Leverages api/models/markov_blanket.py, api/agents/metacognition_agent.py |
| Test-First | PASS | Acceptance scenarios defined for all user stories |
| Integration Testing | PASS | FR-021/022/023 require integration tests |
| Observability | PASS | FR-023 mandates observable events for logging |
| Simplicity | PASS | Extends existing patterns, no new frameworks |

**Gate Result**: PASS - No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/040-metacognitive-particles/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── metacognitive_api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
api/
├── models/
│   ├── markov_blanket.py         # EXISTS - Extend with particle types
│   ├── metacognitive_particle.py # NEW - Particle classification models
│   ├── belief_state.py           # NEW - BeliefState with precision
│   └── epistemic_gain.py         # NEW - EpistemicGainEvent model
├── services/
│   ├── particle_classifier.py    # NEW - Classify cognitive processes
│   ├── agency_service.py         # NEW - Sense of agency computation
│   ├── epistemic_gain_service.py # NEW - Detect "Aha!" moments
│   ├── procedural_metacognition.py # NEW - Monitor/control functions
│   └── efe_engine.py             # EXISTS - Extend for precision tracking
├── agents/
│   └── metacognition_agent.py    # EXISTS - Extend mental actions
└── routers/
    └── metacognition.py          # NEW - API endpoints

tests/
├── unit/
│   ├── test_particle_classifier.py
│   ├── test_agency_service.py
│   └── test_epistemic_gain.py
└── integration/
    ├── test_metacognitive_flow.py
    └── test_thoughtseed_particle_bridge.py
```

**Structure Decision**: Extends existing api/ monolith structure. New services follow established patterns (class-based with Pydantic validation). No new top-level directories needed.

## Complexity Tracking

> No violations requiring justification. Design uses existing patterns.

---

# Phase 0: Research

## Research Tasks

### R1: Particle Classification Algorithm

**Decision**: Use structural analysis of Markov blanket configuration to classify particles.

**Rationale**: Per Sandved-Smith paper, particle type is determined by:
- Cognitive: Has beliefs about external (μ → Q_μ(η))
- Passive Metacognitive: μ^(2) influences μ^(1) only via blanket, no direct control
- Active Metacognitive: Has internal Markov blanket with a^(2) paths
- Strange: Active paths don't directly influence internal (remove a→μ)
- Nested: N levels of internal blankets

**Alternatives Considered**:
- Behavioral analysis (observe patterns) - Rejected: requires runtime data
- Manual tagging - Rejected: doesn't scale, error-prone

### R2: KL Divergence for Agency Strength

**Decision**: Use scipy.stats.entropy for KL divergence computation between joint and independent distributions.

**Rationale**: Eq.20 from paper: D_KL[Q(μ¹,a¹) | Q(μ¹)Q(a¹)]
- scipy.stats.entropy handles the discrete case
- For continuous (Gaussian), use analytical KL formula

**Alternatives Considered**:
- Custom implementation - Rejected: scipy is battle-tested
- PyTorch KL - Rejected: adds dependency, overkill for this use case

### R3: Epistemic Gain Detection Threshold

**Decision**: Default threshold 0.3 (30% uncertainty reduction) with adaptive option.

**Rationale**:
- Per assumption in spec
- Adaptive threshold = mean of historical gains + 1 std dev
- Prevents threshold from never being crossed in low-variance environments

**Alternatives Considered**:
- Fixed threshold only - Rejected: doesn't adapt to domain
- ML-based detection - Rejected: overengineered for MVP

### R4: Precision Modulation Bounds

**Decision**: Precision values bounded to [0.01, 100.0] (log scale recommended).

**Rationale**:
- 0.01 = very low confidence (open to all information)
- 100.0 = very high confidence (laser focus)
- Log scale prevents numerical instability

**Alternatives Considered**:
- Unbounded precision - Rejected: can cause numerical issues
- Normalized [0,1] - Rejected: loses interpretability as inverse variance

### R5: Cognitive Core Nesting Limit

**Decision**: Maximum 5 levels, configurable via environment variable.

**Rationale**:
- Per spec assumption
- Free energy principle limits useful depth
- 5 levels provides μ¹ → μ² → μ³ → μ⁴ → μ⁵ (cognitive core)

**Alternatives Considered**:
- Unlimited with warning - Rejected: violates theoretical constraint
- Fixed 3 levels - Rejected: too restrictive for complex cognition

---

# Phase 1: Design & Contracts

## Data Model

See [data-model.md](./data-model.md) for full entity specifications.

### Core Entities Summary

| Entity | Purpose | Key Attributes |
|--------|---------|----------------|
| MetacognitiveParticle | Classified cognitive process | type, level, has_agency, belief_state_id, blanket_id |
| BeliefState | Probability distribution | mean, precision, entropy, updated_at |
| MentalAction | Precision/spotlight modulation | action_type, target_agent, prior_state, new_state |
| EpistemicGainEvent | Learning detection | magnitude, affected_beliefs, noetic_quality |
| CognitiveAssessment | Monitoring output | progress, confidence, issues, recommendations |

### Entity Relationships

```
ThoughtSeed <--1:1--> MetacognitiveParticle
MetacognitiveParticle --1:1--> MarkovBlanket (existing)
MetacognitiveParticle --1:1--> BeliefState
MetacognitiveParticle --N:1--> MetacognitiveParticle (parent/child nesting)
MetacognitiveParticle --1:N--> MentalAction (executed actions)
BeliefState --1:N--> EpistemicGainEvent (gains from belief updates)
```

## API Contracts

See [contracts/metacognitive_api.yaml](./contracts/metacognitive_api.yaml) for OpenAPI spec.

### Endpoints Summary

| Method | Path | Purpose | FR Reference |
|--------|------|---------|--------------|
| POST | /metacognition/classify | Classify a cognitive process | FR-001, FR-002 |
| POST | /metacognition/mental-action | Execute mental action | FR-004, FR-005, FR-006 |
| GET | /metacognition/agency/{agent_id} | Get agency strength | FR-008, FR-009 |
| POST | /metacognition/epistemic-gain/check | Check for epistemic gain | FR-011, FR-012 |
| GET | /metacognition/monitoring/{agent_id} | Get cognitive assessment | FR-018 |
| POST | /metacognition/control | Apply control action | FR-019 |

## Service Interfaces

### ParticleClassifier

```python
class ParticleClassifier:
    async def classify(
        self,
        agent_id: str,
        blanket: MarkovBlanket
    ) -> Tuple[ParticleType, float]:
        """
        Returns (particle_type, confidence_score).
        Analyzes blanket structure per paper formalism.
        """
```

### AgencyService

```python
class AgencyService:
    async def compute_agency_strength(
        self,
        particle: MetacognitiveParticle
    ) -> float:
        """
        Returns KL divergence D_KL[Q(μ,a) | Q(μ)Q(a)].
        0.0 = no agency, higher = stronger agency sense.
        """

    async def has_agency(
        self,
        particle: MetacognitiveParticle,
        threshold: float = 1e-6
    ) -> bool:
        """Returns True if agency strength > threshold."""
```

### EpistemicGainService

```python
class EpistemicGainService:
    async def check_gain(
        self,
        prior_belief: BeliefState,
        posterior_belief: BeliefState,
        threshold: float = 0.3
    ) -> Optional[EpistemicGainEvent]:
        """
        Returns EpistemicGainEvent if uncertainty reduction > threshold.
        None otherwise.
        """
```

### ProceduralMetacognition

```python
class ProceduralMetacognition:
    async def monitor(
        self,
        agent_id: str
    ) -> CognitiveAssessment:
        """Non-invasive assessment of cognitive state."""

    async def control(
        self,
        assessment: CognitiveAssessment
    ) -> List[MentalAction]:
        """Returns recommended control actions based on assessment."""
```

---

## Implementation Priority

| Priority | Component | Estimated Effort | Dependencies |
|----------|-----------|------------------|--------------|
| P1 | MetacognitiveParticle model | 2 hours | MarkovBlanket (exists) |
| P1 | ParticleClassifier service | 4 hours | MetacognitiveParticle |
| P1 | Extend MetacognitionAgent | 3 hours | ParticleClassifier |
| P2 | AgencyService | 4 hours | MetacognitiveParticle, scipy |
| P2 | EpistemicGainService | 3 hours | BeliefState |
| P2 | BeliefState model | 2 hours | None |
| P3 | CognitiveCoreEnforcer | 2 hours | MetacognitiveParticle |
| P3 | ProceduralMetacognition | 4 hours | All above |
| P3 | API Router | 3 hours | All services |
| P3 | ThoughtSeed bridge | 3 hours | Spec 038 |

**Total Estimated Effort**: ~30 hours (3-4 days focused work)

---

## Next Steps

1. Run `/speckit.tasks` to generate task breakdown
2. Create Archon project and import tasks
3. Begin P1 implementation with MetacognitiveParticle model
