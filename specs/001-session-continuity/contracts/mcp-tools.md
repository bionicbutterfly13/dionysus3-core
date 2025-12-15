# MCP Tool Contracts: Session Continuity

**Version**: 1.0.0
**Date**: 2025-12-13

## Overview

Three new MCP tools for journey management. All tools follow existing patterns from `mcp/server.py`.

---

## Tool: get_or_create_journey

**Purpose**: Get existing journey for user or create new one.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "format": "uuid",
      "description": "User identifier. NULL/omitted for anonymous journey."
    }
  },
  "required": []
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "journey_id": {
      "type": "string",
      "format": "uuid"
    },
    "user_id": {
      "type": ["string", "null"],
      "format": "uuid"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "session_count": {
      "type": "integer"
    },
    "is_new": {
      "type": "boolean",
      "description": "True if journey was just created"
    }
  },
  "required": ["journey_id", "created_at", "session_count", "is_new"]
}
```

### Behavior

1. If `user_id` provided and journey exists: Return existing journey
2. If `user_id` provided and no journey: Create new journey, return it
3. If `user_id` omitted: Create anonymous journey, return it

### Error Cases

| Code | Condition | Message |
|------|-----------|---------|
| 500 | Database error | "Failed to access journey: {detail}" |

---

## Tool: query_journey_history

**Purpose**: Search journey sessions by keyword, time range, or metadata.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "journey_id": {
      "type": "string",
      "format": "uuid",
      "description": "Journey to search within"
    },
    "query": {
      "type": "string",
      "description": "Keyword search on session summaries"
    },
    "from_date": {
      "type": "string",
      "format": "date-time",
      "description": "Start of time range filter"
    },
    "to_date": {
      "type": "string",
      "format": "date-time",
      "description": "End of time range filter"
    },
    "limit": {
      "type": "integer",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    },
    "include_documents": {
      "type": "boolean",
      "default": false,
      "description": "Include linked documents in results"
    }
  },
  "required": ["journey_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "journey_id": {
      "type": "string",
      "format": "uuid"
    },
    "sessions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "session_id": { "type": "string", "format": "uuid" },
          "created_at": { "type": "string", "format": "date-time" },
          "summary": { "type": "string" },
          "has_diagnosis": { "type": "boolean" },
          "relevance_score": { "type": "number" }
        }
      }
    },
    "documents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": { "type": "string", "format": "uuid" },
          "document_type": { "type": "string" },
          "title": { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "total_results": {
      "type": "integer"
    }
  },
  "required": ["journey_id", "sessions", "total_results"]
}
```

### Behavior

1. Validate `journey_id` exists
2. Apply filters (query, date range) if provided
3. Order by relevance (if query) or date (if no query)
4. Return paginated results with summary snippets

### Error Cases

| Code | Condition | Message |
|------|-----------|---------|
| 404 | Journey not found | "Journey {id} not found" |
| 400 | Invalid date range | "from_date must be before to_date" |
| 500 | Database error | "Failed to query history: {detail}" |

---

## Tool: add_document_to_journey

**Purpose**: Link a document or artifact to a journey.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "journey_id": {
      "type": "string",
      "format": "uuid",
      "description": "Journey to link document to"
    },
    "document_type": {
      "type": "string",
      "enum": ["woop_plan", "file_upload", "artifact", "note"],
      "description": "Type of document"
    },
    "title": {
      "type": "string",
      "description": "Document title"
    },
    "content": {
      "type": "string",
      "description": "Document content or file path"
    },
    "metadata": {
      "type": "object",
      "description": "Additional metadata"
    }
  },
  "required": ["journey_id", "document_type"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "document_id": {
      "type": "string",
      "format": "uuid"
    },
    "journey_id": {
      "type": "string",
      "format": "uuid"
    },
    "document_type": {
      "type": "string"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["document_id", "journey_id", "document_type", "created_at"]
}
```

### Behavior

1. Validate `journey_id` exists
2. Validate `document_type` is allowed
3. Create document record linked to journey
4. Return created document

### Error Cases

| Code | Condition | Message |
|------|-----------|---------|
| 404 | Journey not found | "Journey {id} not found" |
| 400 | Invalid document_type | "document_type must be one of: ..." |
| 500 | Database error | "Failed to add document: {detail}" |

---

## Non-Breaking Guarantee

These tools are **additive only**. No existing MCP tools are modified. This qualifies as a **minor version bump** per Constitution Principle V (Versioned Contracts).

## Changelog Entry

```markdown
## [1.1.0] - 2025-12-XX

### Added
- MCP tool: `get_or_create_journey` - Journey management for session continuity
- MCP tool: `query_journey_history` - Search past conversations and documents
- MCP tool: `add_document_to_journey` - Link artifacts to journeys
```
