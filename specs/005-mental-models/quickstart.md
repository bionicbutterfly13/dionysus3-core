# Quickstart: Mental Models

**Feature**: 005-mental-models
**Time**: ~15 minutes

## Prerequisites

- PostgreSQL running with dionysus schema
- Memory basins (clusters) already exist
- Heartbeat system operational

## Step 1: Apply Migration

```bash
# From project root
psql $DATABASE_URL -f migrations/008_create_mental_models.sql
```

Verify tables created:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('mental_models', 'model_predictions', 'model_revisions');
```

Expected: 3 rows

## Step 2: Create Your First Model

### Option A: MCP Tool

```json
// Request to create_model tool
{
  "name": "User Work Patterns",
  "domain": "user",
  "basin_ids": ["<your-basin-id-1>", "<your-basin-id-2>"],
  "description": "Predicts user behavior around work and productivity",
  "prediction_templates": [
    {
      "trigger": "user mentions deadline",
      "predict": "likely feeling time pressure",
      "suggest": "help prioritize or break down task"
    }
  ]
}
```

### Option B: REST API

```bash
curl -X POST http://localhost:8000/api/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "User Work Patterns",
    "domain": "user",
    "basin_ids": ["<your-basin-id-1>", "<your-basin-id-2>"],
    "description": "Predicts user behavior around work and productivity"
  }'
```

### Option C: Direct SQL

```sql
SELECT create_mental_model(
    'User Work Patterns',
    'user',
    ARRAY['<basin-id-1>'::uuid, '<basin-id-2>'::uuid],
    'Predicts user behavior around work and productivity'
);
```

## Step 3: Activate the Model

Models start in 'draft' status. Activate for use:

```bash
curl -X PUT http://localhost:8000/api/models/<model-id> \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

Or via SQL:

```sql
UPDATE mental_models SET status = 'active' WHERE name = 'User Work Patterns';
```

## Step 4: Verify Heartbeat Integration

The heartbeat loop automatically:
1. **OBSERVE**: Retrieves active models relevant to context
2. **OBSERVE**: Generates predictions from matched models
3. **ORIENT**: Compares predictions to observations
4. **ORIENT**: Calculates prediction errors

Check for predictions:

```sql
SELECT mp.*, mm.name as model_name
FROM model_predictions mp
JOIN mental_models mm ON mp.model_id = mm.id
ORDER BY mp.created_at DESC
LIMIT 5;
```

## Step 5: Check Model Health

### Active Models Summary

```sql
SELECT * FROM active_models_summary;
```

Shows: prediction accuracy, basin count, total predictions per model.

### Models Needing Revision

```sql
SELECT * FROM models_needing_revision;
```

Lists models with >50% average error over last 7 days.

## Step 6: Manual Revision (Optional)

If a model needs improvement:

```bash
curl -X POST http://localhost:8000/api/models/<model-id>/revisions \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_description": "Adding new basin based on recent patterns",
    "add_basins": ["<new-basin-id>"]
  }'
```

## Troubleshooting

### "One or more basin IDs do not exist"

Basin IDs must reference existing `memory_clusters`. Check:

```sql
SELECT id, name FROM memory_clusters LIMIT 10;
```

### Model Not Generating Predictions

1. Ensure model status is 'active':
   ```sql
   SELECT id, name, status FROM mental_models WHERE name = '<name>';
   ```

2. Check heartbeat is running and processing OBSERVE phase

3. Verify context matches model domain

### High Prediction Error

1. Check recent predictions:
   ```sql
   SELECT prediction, observation, prediction_error
   FROM model_predictions
   WHERE model_id = '<model-id>'
   ORDER BY created_at DESC LIMIT 10;
   ```

2. Consider revising model structure or updating prediction templates

## Next Steps

- Create domain-specific models (self, world, task_specific)
- Add more prediction templates
- Monitor accuracy trends
- Set up alerts for models needing revision

## Common Model Patterns

### User Emotional Patterns

```json
{
  "name": "User Emotional Patterns",
  "domain": "user",
  "prediction_templates": [
    {"trigger": "frustration keywords", "predict": "needs acknowledgment", "suggest": "validate feelings first"},
    {"trigger": "celebration keywords", "predict": "wants to share success", "suggest": "celebrate with them"}
  ]
}
```

### Self Capability Model

```json
{
  "name": "My Technical Strengths",
  "domain": "self",
  "prediction_templates": [
    {"trigger": "code review request", "predict": "high confidence", "suggest": "proceed directly"},
    {"trigger": "emotional support request", "predict": "may need extra care", "suggest": "ask clarifying questions"}
  ]
}
```

### Domain Knowledge Model

```json
{
  "name": "Career Transition Dynamics",
  "domain": "world",
  "prediction_templates": [
    {"trigger": "career change mention", "predict": "identity uncertainty likely", "suggest": "explore values first"},
    {"trigger": "skill gap mention", "predict": "imposter syndrome risk", "suggest": "normalize learning curve"}
  ]
}
```
