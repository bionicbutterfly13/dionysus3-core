# Data Model: Metacognitive Particles Integration

**Feature**: 040-metacognitive-particles
**Date**: 2025-12-30

---

## Entities

### MetacognitiveParticle

Represents a classified cognitive process with Markov blanket structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier |
| type | ParticleType (enum) | Yes | Classification result |
| level | int | Yes | Nesting level (0 = base, N = cognitive core) |
| has_agency | bool | Yes | Whether particle has sense of agency |
| agent_id | str | Yes | Reference to the cognitive agent |
| blanket_id | UUID | Yes | Reference to MarkovBlanket |
| belief_state_id | UUID | No | Reference to current BeliefState |
| parent_id | UUID | No | Parent particle (for nested hierarchies) |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

**ParticleType Enum**:
- `COGNITIVE` - Basic cognitive particle with beliefs about external
- `PASSIVE_METACOGNITIVE` - Beliefs about beliefs, no direct control
- `ACTIVE_METACOGNITIVE` - Has mental action capability
- `STRANGE_METACOGNITIVE` - Actions inferred via sensory (no a→μ)
- `NESTED_N_LEVEL` - Multiple internal Markov blankets

**Validation Rules**:
- level >= 0
- level <= MAX_NESTING_DEPTH (default 5)
- parent_id required if level > 0
- blanket_id must reference valid MarkovBlanket

---

### BeliefState

Probability distribution parameterized by sufficient statistics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier |
| mean | List[float] | Yes | Distribution mean vector |
| precision | List[List[float]] | Yes | Precision matrix (inverse covariance) |
| entropy | float | Yes | Computed entropy value |
| dimension | int | Yes | Dimensionality of the belief space |
| particle_id | UUID | Yes | Owning particle reference |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

**Validation Rules**:
- precision matrix must be symmetric positive-definite
- precision values bounded to [0.01, 100.0]
- entropy >= 0
- dimension must match mean length and precision matrix size

**Computed Properties**:
```python
@property
def entropy(self) -> float:
    """Gaussian entropy from precision matrix."""
    d = self.dimension
    return 0.5 * d * (1 + np.log(2 * np.pi)) - 0.5 * np.log(np.linalg.det(self.precision))
```

---

### MentalAction

Higher-level action that modulates lower-level parameters.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier |
| action_type | MentalActionType (enum) | Yes | Type of modulation |
| source_agent | str | Yes | Agent executing the action |
| target_agent | str | Yes | Agent being modulated |
| modulation_params | dict | Yes | Parameters of modulation |
| prior_state | dict | Yes | State before modulation |
| new_state | dict | Yes | State after modulation |
| executed_at | datetime | Yes | Execution timestamp |

**MentalActionType Enum**:
- `PRECISION_DELTA` - Adjust precision by delta amount
- `SET_PRECISION` - Set precision to absolute value
- `FOCUS_TARGET` - Direct attentional spotlight
- `SPOTLIGHT_PRECISION` - Set spotlight precision

**Modulation Params Structure**:
```python
# For PRECISION_DELTA
{"precision_delta": float}  # e.g., +0.1 or -0.15

# For SET_PRECISION
{"precision": float}  # e.g., 0.8

# For FOCUS_TARGET
{"focus_target": str, "spotlight_precision": float}
```

---

### EpistemicGainEvent

Record of significant learning ("Aha!" moment).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier |
| magnitude | float | Yes | Uncertainty reduction (0.0 to 1.0) |
| prior_entropy | float | Yes | Entropy before update |
| posterior_entropy | float | Yes | Entropy after update |
| affected_beliefs | List[UUID] | Yes | BeliefState IDs affected |
| noetic_quality | bool | Yes | True if certainty without proportional evidence |
| particle_id | UUID | Yes | Particle that experienced gain |
| detected_at | datetime | Yes | Detection timestamp |

**Validation Rules**:
- magnitude = (prior_entropy - posterior_entropy) / prior_entropy
- magnitude must be >= configured threshold (default 0.3) to be recorded
- noetic_quality flagged when evidence reduction < uncertainty reduction

---

### CognitiveAssessment

Output of procedural metacognition monitoring function.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier |
| agent_id | str | Yes | Agent being assessed |
| progress | float | Yes | Task progress (0.0 to 1.0) |
| confidence | float | Yes | Overall confidence level |
| prediction_error | float | Yes | Current prediction error magnitude |
| issues | List[str] | Yes | Identified issues |
| recommendations | List[str] | Yes | Suggested actions |
| assessed_at | datetime | Yes | Assessment timestamp |

**Issue Categories**:
- `HIGH_PREDICTION_ERROR` - Error exceeds threshold
- `LOW_CONFIDENCE` - Precision below threshold
- `STALLED_PROGRESS` - No progress in N cycles
- `ATTENTION_SCATTERED` - Spotlight precision too low

---

## Relationships

```
┌─────────────────┐     1:1      ┌──────────────────┐
│   ThoughtSeed   │◄────────────►│MetacognitiveParticle│
└─────────────────┘              └────────┬─────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼ 1:1                 ▼ 1:1                 ▼ N:1
           ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
           │ MarkovBlanket │     │  BeliefState  │     │MetacognitiveParticle│
           │   (exists)    │     │               │     │    (parent)   │
           └───────────────┘     └───────┬───────┘     └───────────────┘
                                         │
                                         ▼ 1:N
                                ┌───────────────────┐
                                │EpistemicGainEvent │
                                └───────────────────┘

MetacognitiveParticle ──1:N──► MentalAction
CognitiveAssessment (standalone, references agent_id)
```

---

## Neo4j Schema

### Node Labels

```cypher
// Create node for MetacognitiveParticle
(:MetacognitiveParticle {
  id: $id,
  type: $type,
  level: $level,
  has_agency: $has_agency,
  agent_id: $agent_id,
  created_at: datetime(),
  updated_at: datetime()
})

// Create node for BeliefState
(:BeliefState {
  id: $id,
  mean: $mean,
  precision: $precision,
  entropy: $entropy,
  dimension: $dimension,
  created_at: datetime()
})

// Create node for EpistemicGainEvent
(:EpistemicGainEvent {
  id: $id,
  magnitude: $magnitude,
  prior_entropy: $prior_entropy,
  posterior_entropy: $posterior_entropy,
  noetic_quality: $noetic_quality,
  detected_at: datetime()
})
```

### Relationship Types

```cypher
// Particle hierarchy (nesting)
(child:MetacognitiveParticle)-[:NESTED_IN]->(parent:MetacognitiveParticle)

// Particle owns belief state
(particle:MetacognitiveParticle)-[:HAS_BELIEF]->(belief:BeliefState)

// Particle has blanket (using existing MarkovBlanket)
(particle:MetacognitiveParticle)-[:HAS_BLANKET]->(blanket:MarkovBlanket)

// Particle executes mental action
(particle:MetacognitiveParticle)-[:EXECUTED]->(action:MentalAction)

// Mental action targets belief
(action:MentalAction)-[:MODULATES]->(belief:BeliefState)

// Belief state produces epistemic gain
(belief:BeliefState)-[:PRODUCED]->(gain:EpistemicGainEvent)

// Bridge to ThoughtSeed (Spec 038)
(seed:ThoughtSeed)-[:MANIFESTS_AS]->(particle:MetacognitiveParticle)
```

---

## State Transitions

### MetacognitiveParticle Lifecycle

```
UNCLASSIFIED ──classify()──► CLASSIFIED
     │                            │
     │                            ▼
     │                      [type assigned]
     │                            │
     └──────────────────────────►─┤
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
                   ▼                             ▼
            ACTIVE_STATE                   ARCHIVED
         (normal operation)            (particle obsolete)
```

### BeliefState Updates

```
INITIAL ──update()──► UPDATED ──check_gain()──► [EpistemicGainEvent?]
    │                    │
    └────────────────────┘
         (continuous cycle)
```

---

## Indexes & Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT particle_id IF NOT EXISTS
FOR (p:MetacognitiveParticle) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT belief_id IF NOT EXISTS
FOR (b:BeliefState) REQUIRE b.id IS UNIQUE;

// Performance indexes
CREATE INDEX particle_agent IF NOT EXISTS
FOR (p:MetacognitiveParticle) ON (p.agent_id);

CREATE INDEX particle_type IF NOT EXISTS
FOR (p:MetacognitiveParticle) ON (p.type);

CREATE INDEX particle_level IF NOT EXISTS
FOR (p:MetacognitiveParticle) ON (p.level);

CREATE INDEX gain_magnitude IF NOT EXISTS
FOR (g:EpistemicGainEvent) ON (g.magnitude);
```
