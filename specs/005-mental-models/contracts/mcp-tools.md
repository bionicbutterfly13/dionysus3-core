# MCP Tool Contracts: Mental Models

**Feature**: 005-mental-models
**Version**: 1.0.0
**Date**: 2025-12-16

## Tool: create_model

Create a new mental model from constituent basins.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Human-readable model name",
      "maxLength": 255
    },
    "domain": {
      "type": "string",
      "enum": ["user", "self", "world", "task_specific"],
      "description": "Model domain/type"
    },
    "basin_ids": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" },
      "minItems": 1,
      "description": "Memory cluster (basin) IDs to combine"
    },
    "description": {
      "type": "string",
      "description": "Optional detailed description"
    },
    "prediction_templates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "trigger": { "type": "string" },
          "predict": { "type": "string" },
          "suggest": { "type": "string" }
        }
      },
      "description": "Optional prediction patterns"
    }
  },
  "required": ["name", "domain", "basin_ids"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "model_id": { "type": "string", "format": "uuid" },
    "message": { "type": "string" }
  },
  "required": ["success"]
}
```

### Example

```json
// Request
{
  "name": "User Emotional Patterns",
  "domain": "user",
  "basin_ids": ["550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440002"],
  "description": "Predicts user emotional states based on conversation patterns",
  "prediction_templates": [
    {
      "trigger": "user mentions work stress",
      "predict": "likely experiencing anxiety about performance",
      "suggest": "acknowledge feelings before problem-solving"
    }
  ]
}

// Response
{
  "success": true,
  "model_id": "660e8400-e29b-41d4-a716-446655440099",
  "message": "Model 'User Emotional Patterns' created with 2 basins"
}
```

### Error Cases

| Code | Message | Cause |
|------|---------|-------|
| INVALID_BASIN | "One or more basin IDs do not exist" | Basin ID not found in memory_clusters |
| INVALID_DOMAIN | "Domain must be one of: user, self, world, task_specific" | Invalid domain value |
| DUPLICATE_NAME | "A model with this name already exists" | Name collision |

---

## Tool: list_models

List mental models with optional filtering.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "domain": {
      "type": "string",
      "enum": ["user", "self", "world", "task_specific"],
      "description": "Filter by domain"
    },
    "status": {
      "type": "string",
      "enum": ["draft", "active", "deprecated"],
      "description": "Filter by status"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20,
      "description": "Maximum results"
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "models": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "domain": { "type": "string" },
          "status": { "type": "string" },
          "prediction_accuracy": { "type": "number" },
          "basin_count": { "type": "integer" },
          "revision_count": { "type": "integer" }
        }
      }
    },
    "total": { "type": "integer" }
  }
}
```

### Example

```json
// Request
{
  "domain": "user",
  "status": "active",
  "limit": 10
}

// Response
{
  "models": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440099",
      "name": "User Emotional Patterns",
      "domain": "user",
      "status": "active",
      "prediction_accuracy": 0.72,
      "basin_count": 2,
      "revision_count": 3
    }
  ],
  "total": 1
}
```

---

## Tool: get_model

Get detailed information about a specific model.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "model_id": {
      "type": "string",
      "format": "uuid",
      "description": "Model ID to retrieve"
    },
    "include_predictions": {
      "type": "boolean",
      "default": false,
      "description": "Include recent predictions"
    },
    "include_revisions": {
      "type": "boolean",
      "default": false,
      "description": "Include revision history"
    }
  },
  "required": ["model_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "model": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "name": { "type": "string" },
        "domain": { "type": "string" },
        "description": { "type": "string" },
        "status": { "type": "string" },
        "constituent_basins": {
          "type": "array",
          "items": { "type": "string", "format": "uuid" }
        },
        "basin_relationships": { "type": "object" },
        "prediction_templates": { "type": "array" },
        "prediction_accuracy": { "type": "number" },
        "revision_count": { "type": "integer" },
        "created_at": { "type": "string", "format": "date-time" },
        "updated_at": { "type": "string", "format": "date-time" }
      }
    },
    "predictions": {
      "type": "array",
      "description": "Included if include_predictions=true"
    },
    "revisions": {
      "type": "array",
      "description": "Included if include_revisions=true"
    }
  }
}
```

### Error Cases

| Code | Message | Cause |
|------|---------|-------|
| NOT_FOUND | "Model not found" | Invalid model_id |

---

## Tool: revise_model

Trigger manual revision of a model.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "model_id": {
      "type": "string",
      "format": "uuid",
      "description": "Model ID to revise"
    },
    "trigger_description": {
      "type": "string",
      "description": "Reason for revision"
    },
    "add_basins": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" },
      "description": "Basin IDs to add to model"
    },
    "remove_basins": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" },
      "description": "Basin IDs to remove from model"
    }
  },
  "required": ["model_id", "trigger_description"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "revision_id": { "type": "string", "format": "uuid" },
    "message": { "type": "string" },
    "new_accuracy": { "type": "number" }
  }
}
```

### Example

```json
// Request
{
  "model_id": "660e8400-e29b-41d4-a716-446655440099",
  "trigger_description": "Adding career patterns basin based on recent conversations",
  "add_basins": ["550e8400-e29b-41d4-a716-446655440003"]
}

// Response
{
  "success": true,
  "revision_id": "770e8400-e29b-41d4-a716-446655440100",
  "message": "Model revised: added 1 basin",
  "new_accuracy": 0.72
}
```

### Error Cases

| Code | Message | Cause |
|------|---------|-------|
| NOT_FOUND | "Model not found" | Invalid model_id |
| INVALID_BASIN | "One or more basin IDs do not exist" | Invalid add_basins/remove_basins |
| WOULD_EMPTY | "Cannot remove all basins from model" | remove_basins would leave 0 basins |

---

## Versioning

- **1.0.0** (2025-12-16): Initial release
  - create_model
  - list_models
  - get_model
  - revise_model

### Breaking Change Policy

Per Constitution V (Versioned Contracts):
- Tool input/output schemas are immutable within major version
- New optional parameters → minor version bump
- Required parameter additions → major version bump
