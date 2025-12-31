# Data Model: Thoughtseeds Framework

## Entities

### ThoughtSeed (Augmented)
- **Fields**:
    - `id`: UUID
    - `layer`: Enum (SENSORIMOTOR, PERCEPTUAL, CONCEPTUAL, ABSTRACT, METACOGNITIVE)
    - `content`: String
    - `probabilities`: List[float] (for entropy)
    - `vector`: List[float] (embedding)
    - `efe_score`: float
    - `precision_weight`: float (0-1)
- **Relationships**:
    - `[:SENSORY]`: Inbound from environment/other thoughts.
    - `[:ACTIVE]`: Outbound to actions/other thoughts.
    - `[:PART_OF]`: To Superordinate Ensemble.

### Prior (Identity/Constraint)
- **Fields**:
    - `id`: UUID
    - `level`: Enum (BASAL, DISPOSITIONAL, LEARNED)
    - `description`: String
    - `precision`: float (0-1)
    - `rule_vector`: List[float] (optional, for semantic matching)
- **Relationships**:
    - `[:CONSTRAINS]`: To `ThoughtSeed` or `Action`.

### InnerScreen Log (EpisodicMemory)
- **Fields**:
    - `id`: UUID
    - `timestamp`: DateTime
    - `thought_id`: UUID (reference to winner)
    - `brightness`: float (1 - EFE)
    - `focus_summary`: String

## Validation Rules
- `precision_weight` MUST be between 0.0 and 1.0.
- `efe_score` MUST be calculated before winner selection.
- `BASAL` priors cannot be modified by standard agent actions.
