# Data Model: MOSAEIC Dual Memory Architecture

## Entity Relationship Diagram

```
+------------------------+     +------------------------+
|   FiveWindowCapture    |     |      TurningPoint      |
+------------------------+     +------------------------+
| id: UUID (PK)          |<----|  id: UUID (PK)         |
| session_id: UUID (FK)  |     |  capture_id: UUID (FK) |
| mental: TEXT           |     |  trigger_type: ENUM    |
| observation: TEXT      |     |  trigger_description   |
| senses: TEXT           |     |  narrative_thread_id   |
| actions: TEXT          |     |  life_chapter_id       |
| emotions: TEXT         |     |  vividness_score       |
| emotional_intensity    |     |  created_at            |
| preserve_indefinitely  |     +------------------------+
| context: JSONB         |
| created_at             |
+------------------------+
         |
         | (linked via)
         v
+------------------------+     +------------------------+
|   MaladaptivePattern   |---->|     BeliefRewrite      |
+------------------------+     +------------------------+
| id: UUID (PK)          |     | id: UUID (PK)          |
| belief_content: TEXT   |     | old_belief_id: UUID    |
| domain: ENUM           |     | new_belief: TEXT       |
| severity_score         |     | domain: ENUM           |
| severity_level: ENUM   |     | adaptiveness_score     |
| recurrence_count       |     | evidence_count         |
| intervention_triggered |     | last_verified          |
| last_intervention      |     | prediction_success_ct  |
| linked_capture_ids[]   |     | prediction_failure_ct  |
| linked_model_ids[]     |     | evolution_trigger      |
| created_at             |     | archived: BOOL         |
| updated_at             |     | created_at, updated_at |
+------------------------+     +------------------------+
                                        |
                                        v
                               +------------------------+
                               | VerificationEncounter  |
                               +------------------------+
                               | id: UUID (PK)          |
                               | belief_id: UUID (FK)   |
                               | prediction_id: UUID    |
                               | prediction_content     |
                               | observation: JSONB     |
                               | belief_activated       |
                               | prediction_error       |
                               | session_id             |
                               | timestamp              |
                               | created_at             |
                               +------------------------+
```

## Enumerations

### ExperientialDimension
```python
class ExperientialDimension(str, Enum):
    MENTAL = "mental"
    OBSERVATION = "observation"
    SENSES = "senses"
    ACTIONS = "actions"
    EMOTIONS = "emotions"
```

### TurningPointTrigger
```python
class TurningPointTrigger(str, Enum):
    HIGH_EMOTION = "high_emotion"
    SURPRISE = "surprise"
    CONSEQUENCE = "consequence"
    MANUAL = "manual"
```

### PatternSeverity
```python
class PatternSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
```

### BasinInfluenceType (from active-inference-core)
```python
class BasinInfluenceType(str, Enum):
    REINFORCEMENT = "reinforcement"  # Strengthens existing basin
    COMPETITION = "competition"      # Competes with existing basin
    SYNTHESIS = "synthesis"          # Merges with existing basin
    EMERGENCE = "emergence"          # Creates new basin
```

## PostgreSQL Schema

```sql
-- Enums
CREATE TYPE experiential_dimension AS ENUM (
    'mental', 'observation', 'senses', 'actions', 'emotions'
);

CREATE TYPE turning_point_trigger AS ENUM (
    'high_emotion', 'surprise', 'consequence', 'manual'
);

CREATE TYPE pattern_severity AS ENUM (
    'low', 'moderate', 'high', 'critical'
);

CREATE TYPE basin_influence_type AS ENUM (
    'reinforcement', 'competition', 'synthesis', 'emergence'
);

-- Tables (see spec.md for full DDL)
```

## Integration with Existing Models

### Links to 005-mental-models

| MOSAEIC Entity | Mental Models Link |
|----------------|-------------------|
| BeliefRewrite.domain | ModelDomain enum |
| BeliefRewrite.evolution_trigger | RevisionTrigger + BasinInfluenceType |
| VerificationEncounter.prediction_id | ModelPrediction.id |
| MaladaptivePattern.linked_model_ids | MentalModel.id[] |

### Links to 007-memory-consolidation

| MOSAEIC Entity | Consolidation Link |
|----------------|-------------------|
| FiveWindowCapture | Sessions -> Episodes |
| BeliefRewrite | Predictions -> Facts |
| TurningPoint | preserve_indefinitely exemption |

### Links to 001-session-continuity

| MOSAEIC Entity | Session Link |
|----------------|-------------|
| FiveWindowCapture.session_id | sessions.id |
| VerificationEncounter.session_id | sessions.id |
