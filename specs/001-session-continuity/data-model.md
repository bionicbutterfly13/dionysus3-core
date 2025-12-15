# Data Model: Session Continuity

**Date**: 2025-12-13
**Input**: research.md decisions, spec.md entities

## Entity Overview

```
Journey (1) ──┬── (*) Session
              └── (*) JourneyDocument
```

---

## Journey

Represents a device's complete interaction history across multiple sessions.

### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | UUID | Yes | gen_random_uuid() | Primary key |
| device_id | UUID | Yes | - | Device identifier (always present, stored in ~/.dionysus/device_id) |
| created_at | TIMESTAMPTZ | Yes | CURRENT_TIMESTAMP | Journey creation time |
| updated_at | TIMESTAMPTZ | Yes | CURRENT_TIMESTAMP | Last modification |
| metadata | JSONB | No | {} | Extensible metadata |

*Deferred fields (post-MVP):*
- `thoughtseed_trajectory` JSONB - Array of thoughtseed states over time
- `attractor_dynamics_history` JSONB - Array of attractor basin activations

### Validation Rules

- `device_id` uniqueness enforced (one journey per device)
- `device_id` must be valid UUID v4

### Pydantic Model

```python
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

class Journey(BaseModel):
    id: UUID
    device_id: UUID  # Always required
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = {}

class JourneyCreate(BaseModel):
    device_id: UUID  # Required - from ~/.dionysus/device_id
    metadata: dict[str, Any] = {}
```

---

## Session

A single conversation within a journey, containing messages and optional diagnosis.

### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | UUID | Yes | gen_random_uuid() | Primary key |
| journey_id | UUID | Yes | - | FK to journeys.id |
| created_at | TIMESTAMPTZ | Yes | CURRENT_TIMESTAMP | Session start time |
| updated_at | TIMESTAMPTZ | Yes | CURRENT_TIMESTAMP | Last message time |
| summary | TEXT | No | NULL | Auto-generated session summary for search |
| messages | JSONB | No | [] | Array of {role, content, timestamp} |
| diagnosis | JSONB | No | NULL | IAS diagnosis result if completed |
| confidence_score | INTEGER | No | 0 | Diagnosis confidence 0-100 |

### Validation Rules

- `journey_id` must reference existing journey (FK constraint)
- `messages` entries must have `role` (user|assistant) and `content` fields
- `confidence_score` must be 0-100
- `summary` is auto-generated from messages (not user-editable)

### Pydantic Model

```python
class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: Optional[datetime] = None

class Diagnosis(BaseModel):
    step_id: int
    action_id: int
    obstacle_id: int
    explanation: str
    contrarian_insight: str

class Session(BaseModel):
    id: UUID
    journey_id: UUID
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    messages: list[Message] = []
    diagnosis: Optional[Diagnosis] = None
    confidence_score: int = 0

class SessionCreate(BaseModel):
    journey_id: UUID
    messages: list[Message] = []
```

---

## JourneyDocument

A document or artifact linked to a journey.

### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | UUID | Yes | gen_random_uuid() | Primary key |
| journey_id | UUID | Yes | - | FK to journeys.id |
| document_type | TEXT | Yes | - | Type: "woop_plan", "file_upload", "artifact" |
| title | TEXT | No | NULL | Document title |
| content | TEXT | No | NULL | Document content (or path) |
| metadata | JSONB | No | {} | Extensible metadata |
| created_at | TIMESTAMPTZ | Yes | CURRENT_TIMESTAMP | Creation time |

### Validation Rules

- `journey_id` must reference existing journey (FK constraint)
- `document_type` must be one of allowed types
- ON DELETE CASCADE from journey (no orphan documents)

### Pydantic Model

```python
class JourneyDocument(BaseModel):
    id: UUID
    journey_id: UUID
    document_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: dict[str, Any] = {}
    created_at: datetime

class JourneyDocumentCreate(BaseModel):
    journey_id: UUID
    document_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: dict[str, Any] = {}
```

---

## State Transitions

### Journey Lifecycle

```
[Created] → [Active] → [Inactive]
              ↑
              └── Session added
```

- Journey is **Created** on first session
- Journey is **Active** while sessions exist with recent activity
- Journey becomes **Inactive** after configurable idle period (for cleanup)

### Session Lifecycle

```
[Created] → [Gathering Info] → [Ready to Diagnose] → [Diagnosed]
```

- **Created**: Empty session, linked to journey
- **Gathering Info**: Messages added, confidence < 85
- **Ready to Diagnose**: confidence >= 85
- **Diagnosed**: diagnosis field populated

---

## Database Indexes

```sql
-- Journey lookups
CREATE INDEX idx_journeys_device ON journeys(device_id);

-- Session lookups
CREATE INDEX idx_sessions_journey ON sessions(journey_id);
CREATE INDEX idx_sessions_created ON sessions(created_at DESC);

-- Full-text search on summaries
CREATE INDEX idx_sessions_summary_gin ON sessions
    USING GIN (to_tsvector('english', summary));

-- Document lookups
CREATE INDEX idx_journey_docs_journey ON journey_documents(journey_id);
CREATE INDEX idx_journey_docs_type ON journey_documents(document_type);
```
