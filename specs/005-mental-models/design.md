# Technical Design: Mental Model Architecture

**Status**: Draft
**Created**: 2025-12-16
**Author**: Claude + Mani Saint-Victor
**Based on**: Yufik's neuronal packet theory (2019, 2021)

> **Note**: This document contains implementation details. For business requirements, see [spec.md](./spec.md).

## Theoretical Foundation

### Source Papers

1. **Yufik (2019)** - "The Understanding Capacity and Information Dynamics in the Human Brain"
   - PMC7514789
   - Introduces neuronal packets as quasi-stable Hebbian assemblies
   - Mental models as structured combinations of packets

2. **Yufik & Malhotra (2021)** - "Situational Understanding in the Human and the Machine"
   - Frontiers in Systems Neuroscience
   - Extends to situational understanding vs awareness
   - Links to Active Inference framework

### Key Concepts

| Concept | Definition | Implementation |
|---------|------------|----------------|
| **Neuronal Packet** | Quasi-stable Hebbian assembly bounded by energy barriers | `memory_clusters` with basin extensions |
| **Mental Model** | Structured combination of packets for prediction/explanation | New `mental_models` table |
| **Decoupling** | Manipulate models without sensory feedback | Heartbeat reasoning (offline) |
| **Arousal Regulation** | Energy distribution for model integrity | Energy budget system |
| **Prediction Error** | Mismatch between model prediction and observation | `active_inference_states.prediction_error` |

### Core Distinction

```
Situational Awareness          Situational Understanding
────────────────────────────────────────────────────────
"What is happening"            "Why + What will happen"
Pattern matching               Model-based prediction
Requires experience            Works in novel situations
OBSERVE phase                  ORIENT + DECIDE phases
```

## Architecture

### Layer Integration

```
┌─────────────────────────────────────────────────────────────┐
│                   MENTAL MODEL LAYER                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │User Model  │  │Self Model  │  │Domain Model│            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        └───────────────┼───────────────┘                    │
│                        ▼                                    │
│              ┌─────────────────┐                           │
│              │   PREDICTIONS   │                           │
│              └────────┬────────┘                           │
└───────────────────────┼─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               ACTIVE INFERENCE LAYER                        │
│    Prediction ──vs── Observation = Prediction Error         │
│         │                              │                    │
│         ▼                              ▼                    │
│    Low Error: Continue           High Error: Revise         │
└─────────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 ATTRACTOR BASIN LAYER                       │
│    Basin A ◄──► Basin B ◄──► Basin C ◄──► Basin D          │
│         ▲           ▲           ▲           ▲              │
│         └───────────┴───────────┴───────────┘              │
│                    Memories                                 │
└─────────────────────────────────────────────────────────────┘
```

### Mental Model Structure

A mental model consists of:

1. **Constituent Basins** - Which attractor basins form this model
2. **Basin Relationships** - How basins relate within the model (causal, temporal, hierarchical)
3. **Prediction Templates** - Patterns the model can predict
4. **Explanatory Scope** - What phenomena it explains
5. **Validation State** - Evidence, accuracy, revision history

## Schema

### Primary Tables

```sql
-- Mental Models
CREATE TABLE mental_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name TEXT NOT NULL,
    domain TEXT NOT NULL,  -- 'user', 'self', 'world', 'task_specific'
    description TEXT,

    -- Packet Assembly (Yufik 2019)
    constituent_basins UUID[] NOT NULL,  -- memory_clusters IDs
    basin_relationships JSONB,           -- How they relate

    -- Prediction Capability (Yufik 2021)
    prediction_templates JSONB[],        -- Prediction patterns
    explanatory_scope TEXT[],            -- What it explains

    -- Decoupling Support
    requires_sensory_input BOOLEAN DEFAULT FALSE,
    temporal_horizon INTERVAL,           -- Prediction range

    -- Validation
    evidence_memories UUID[],            -- Supporting episodic memories
    prediction_accuracy FLOAT DEFAULT 0.5,
    last_validated TIMESTAMPTZ,
    revision_count INTEGER DEFAULT 0,

    -- Lifecycle
    status TEXT DEFAULT 'draft',  -- draft, active, deprecated
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Model Revision History
CREATE TABLE model_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES mental_models(id) ON DELETE CASCADE,

    -- Trigger
    trigger_type TEXT NOT NULL,  -- 'prediction_error', 'new_evidence', 'contradiction', 'manual'
    trigger_memory_id UUID REFERENCES memories(id),
    trigger_description TEXT,

    -- Changes
    old_structure JSONB,
    new_structure JSONB,
    basins_added UUID[],
    basins_removed UUID[],
    change_description TEXT,

    -- Metrics
    prediction_error_before FLOAT,
    prediction_error_after FLOAT,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Model Predictions (for tracking accuracy)
CREATE TABLE model_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES mental_models(id) ON DELETE CASCADE,

    -- Prediction
    prediction JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    context JSONB,  -- What prompted this prediction

    -- Resolution
    observation JSONB,
    prediction_error FLOAT,
    resolved_at TIMESTAMPTZ,

    -- Link to active inference
    inference_state_id UUID REFERENCES active_inference_states(id),

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Link models to active inference
ALTER TABLE active_inference_states
    ADD COLUMN source_model_id UUID REFERENCES mental_models(id);
```

### Indexes

```sql
CREATE INDEX idx_mental_models_domain ON mental_models(domain);
CREATE INDEX idx_mental_models_status ON mental_models(status) WHERE status = 'active';
CREATE INDEX idx_mental_models_basins ON mental_models USING GIN(constituent_basins);

CREATE INDEX idx_model_revisions_model ON model_revisions(model_id);
CREATE INDEX idx_model_revisions_trigger ON model_revisions(trigger_type);

CREATE INDEX idx_model_predictions_model ON model_predictions(model_id);
CREATE INDEX idx_model_predictions_unresolved ON model_predictions(model_id)
    WHERE resolved_at IS NULL;
```

### Views

```sql
-- Active models with statistics
CREATE VIEW active_models_summary AS
SELECT
    m.id,
    m.name,
    m.domain,
    m.prediction_accuracy,
    array_length(m.constituent_basins, 1) as basin_count,
    m.revision_count,
    COUNT(p.id) as total_predictions,
    AVG(p.prediction_error) FILTER (WHERE p.resolved_at IS NOT NULL) as avg_error,
    MAX(p.created_at) as last_prediction
FROM mental_models m
LEFT JOIN model_predictions p ON m.id = p.model_id
WHERE m.status = 'active'
GROUP BY m.id;

-- Models needing revision (high error)
CREATE VIEW models_needing_revision AS
SELECT
    m.id,
    m.name,
    m.domain,
    AVG(p.prediction_error) as recent_avg_error,
    COUNT(p.id) as recent_predictions
FROM mental_models m
JOIN model_predictions p ON m.id = p.model_id
WHERE m.status = 'active'
AND p.resolved_at > NOW() - INTERVAL '7 days'
GROUP BY m.id
HAVING AVG(p.prediction_error) > 0.5
ORDER BY recent_avg_error DESC;
```

## Functions

### Model Operations

```sql
-- Create a mental model from basins
CREATE OR REPLACE FUNCTION create_mental_model(
    p_name TEXT,
    p_domain TEXT,
    p_basin_ids UUID[],
    p_description TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_model_id UUID;
BEGIN
    -- Validate all basins exist
    IF NOT EXISTS (
        SELECT 1 FROM memory_clusters
        WHERE id = ANY(p_basin_ids)
        HAVING COUNT(*) = array_length(p_basin_ids, 1)
    ) THEN
        RAISE EXCEPTION 'One or more basin IDs do not exist';
    END IF;

    INSERT INTO mental_models (name, domain, constituent_basins, description)
    VALUES (p_name, p_domain, p_basin_ids, p_description)
    RETURNING id INTO v_model_id;

    RETURN v_model_id;
END;
$$ LANGUAGE plpgsql;

-- Generate prediction from model
CREATE OR REPLACE FUNCTION generate_model_prediction(
    p_model_id UUID,
    p_context JSONB,
    p_confidence FLOAT DEFAULT 0.5
) RETURNS UUID AS $$
DECLARE
    v_prediction_id UUID;
    v_prediction JSONB;
    v_model RECORD;
BEGIN
    SELECT * INTO v_model FROM mental_models WHERE id = p_model_id;

    IF v_model IS NULL THEN
        RAISE EXCEPTION 'Model not found: %', p_model_id;
    END IF;

    -- Prediction generation would be done by LLM
    -- This just records the prediction for tracking
    v_prediction := jsonb_build_object(
        'model_id', p_model_id,
        'context', p_context,
        'generated_at', NOW()
    );

    INSERT INTO model_predictions (model_id, prediction, confidence, context)
    VALUES (p_model_id, v_prediction, p_confidence, p_context)
    RETURNING id INTO v_prediction_id;

    RETURN v_prediction_id;
END;
$$ LANGUAGE plpgsql;

-- Resolve prediction with observation
CREATE OR REPLACE FUNCTION resolve_prediction(
    p_prediction_id UUID,
    p_observation JSONB,
    p_error FLOAT
) RETURNS VOID AS $$
BEGIN
    UPDATE model_predictions
    SET observation = p_observation,
        prediction_error = p_error,
        resolved_at = NOW()
    WHERE id = p_prediction_id;

    -- Update model accuracy (rolling average)
    UPDATE mental_models m
    SET prediction_accuracy = (
        SELECT AVG(prediction_error)
        FROM model_predictions
        WHERE model_id = m.id
        AND resolved_at IS NOT NULL
        AND resolved_at > NOW() - INTERVAL '30 days'
    ),
    updated_at = NOW()
    FROM model_predictions p
    WHERE p.id = p_prediction_id
    AND m.id = p.model_id;
END;
$$ LANGUAGE plpgsql;

-- Flag model for revision
CREATE OR REPLACE FUNCTION flag_model_revision(
    p_model_id UUID,
    p_trigger_type TEXT,
    p_trigger_memory_id UUID DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_revision_id UUID;
    v_old_structure JSONB;
BEGIN
    SELECT jsonb_build_object(
        'constituent_basins', constituent_basins,
        'basin_relationships', basin_relationships,
        'prediction_templates', prediction_templates
    ) INTO v_old_structure
    FROM mental_models WHERE id = p_model_id;

    INSERT INTO model_revisions (
        model_id, trigger_type, trigger_memory_id,
        trigger_description, old_structure
    )
    VALUES (
        p_model_id, p_trigger_type, p_trigger_memory_id,
        p_description, v_old_structure
    )
    RETURNING id INTO v_revision_id;

    -- Increment revision count
    UPDATE mental_models
    SET revision_count = revision_count + 1,
        updated_at = NOW()
    WHERE id = p_model_id;

    RETURN v_revision_id;
END;
$$ LANGUAGE plpgsql;
```

## Heartbeat Integration

### Enhanced OBSERVE Phase

```python
async def observe(self) -> EnvironmentSnapshot:
    """Gather environment state including model predictions."""
    snapshot = await self._base_observe()

    # Get active models relevant to current context
    active_models = await self.model_service.get_relevant_models(
        context=snapshot.to_dict()
    )

    # Generate predictions from each model
    snapshot.model_predictions = []
    for model in active_models:
        prediction = await self.model_service.generate_prediction(
            model_id=model.id,
            context=snapshot.to_dict()
        )
        snapshot.model_predictions.append(prediction)

    return snapshot
```

### Enhanced ORIENT Phase

```python
async def orient(self, env: EnvironmentSnapshot) -> GoalsSnapshot:
    """Review goals and evaluate model predictions."""
    goals = await self._base_orient(env)

    # Check for prediction errors from previous heartbeat
    unresolved = await self.model_service.get_unresolved_predictions()

    for prediction in unresolved:
        # Compare prediction to current observation
        error = await self.model_service.calculate_error(
            prediction=prediction,
            observation=env.to_dict()
        )

        await self.model_service.resolve_prediction(
            prediction_id=prediction.id,
            observation=env.to_dict(),
            error=error
        )

        # Flag for revision if error is high
        if error > MODEL_REVISION_THRESHOLD:
            goals.model_revision_needed.append({
                "model_id": prediction.model_id,
                "error": error,
                "prediction": prediction.prediction
            })

    return goals
```

### New Action: REVISE_MODEL

```python
class ReviseModelHandler(ActionHandler):
    """Revise a mental model based on prediction errors."""

    action_type = ActionType.REVISE_MODEL

    async def execute(self, request: ActionRequest) -> ActionResult:
        model_id = request.params["model_id"]
        trigger_memories = request.params.get("trigger_memories", [])

        # Get current model state
        model = await self.model_service.get_model(model_id)

        # Get recent prediction errors
        errors = await self.model_service.get_recent_errors(model_id)

        # LLM-based revision
        revision = await self.llm.revise_model(
            model=model,
            errors=errors,
            new_evidence=trigger_memories
        )

        # Apply revision
        await self.model_service.apply_revision(
            model_id=model_id,
            new_basins=revision.basins,
            new_relationships=revision.relationships,
            new_templates=revision.prediction_templates
        )

        return ActionResult(
            action_type=self.action_type,
            status=ActionStatus.COMPLETED,
            energy_cost=COSTS[ActionType.REVISE_MODEL],  # 3 energy
            data={"revision": revision.to_dict()}
        )
```

### Action Cost Addition

```python
# Add to energy_service.py
ActionType.REVISE_MODEL: 3.0,  # Model revision cost
ActionType.BUILD_MODEL: 4.0,   # New model construction
```

## Model Types

### 1. User Model

Models the user's patterns, preferences, and state.

```python
user_model = MentalModel(
    name="User Emotional Patterns",
    domain="user",
    constituent_basins=[
        anxiety_basin_id,
        career_basin_id,
        communication_style_basin_id
    ],
    prediction_templates=[
        {
            "trigger": "user mentions work stress",
            "predict": "likely experiencing anxiety about performance",
            "suggest": "acknowledge feelings before problem-solving"
        }
    ]
)
```

### 2. Self Model

Models the AGI's own capabilities and limitations.

```python
self_model = MentalModel(
    name="My Reasoning Patterns",
    domain="self",
    constituent_basins=[
        strength_technical_basin_id,
        limitation_emotional_basin_id
    ],
    prediction_templates=[
        {
            "trigger": "asked about emotional nuance",
            "predict": "may miss subtle cues",
            "suggest": "ask clarifying questions"
        }
    ]
)
```

### 3. Domain Models

Models specific knowledge domains.

```python
domain_model = MentalModel(
    name="Career Transition Dynamics",
    domain="world",
    constituent_basins=[
        identity_shift_basin_id,
        skill_gap_basin_id,
        fear_of_unknown_basin_id,
        financial_concerns_basin_id
    ],
    prediction_templates=[
        {
            "trigger": "user considering career change",
            "predict": "will experience identity uncertainty",
            "suggest": "explore values before logistics"
        }
    ]
)
```

## References

- Yufik, Y.M. (2019). The Understanding Capacity and Information Dynamics in the Human Brain. Entropy, 21(3), 308.
- Yufik, Y.M. & Malhotra, R. (2021). Situational Understanding in the Human and the Machine. Frontiers in Systems Neuroscience, 15, 786252.
- Active Inference: Friston, K. (2010). The free-energy principle: a unified brain theory?
