# Inner Architect System Curriculum - Data Model Specification

**Version**: 1.0
**Author**: Dr. Mani Saint-Victor
**Date**: 2026-01-01
**Status**: Production

---

## Overview

This document specifies the canonical data model for the Inner Architect System curriculum stored in Neo4j. All access to this data MUST go through n8n webhooks - NEVER direct Neo4j access.

---

## Source of Truth Documents

The IAS curriculum is documented in these canonical files:

| Document | Path | Purpose |
|----------|------|---------|
| **Avatar Source of Truth** | `/Volumes/Asylum/dev/dionysus3-core/data/ground-truth/analytical-empath-avatar-source-of-truth.md` | Complete target audience definition, 3-phase system structure |
| **Product Architecture** | `/Volumes/Asylum/dev/dionysus3-core/data/ground-truth/97-product-architecture.md` | 9-lesson structure, AI de-risking system |
| **Replay Loop Concept** | `/Volumes/Asylum/dev/dionysus3-core/docs/concepts/Replay Loop.md` | Replay Loop Breaker framework |

---

## Curriculum Structure

### Hierarchy

```
IASCurriculum (root)
 ├── Phase 1: Revelation
 │   ├── Lesson 1: Breakthrough Mapping
 │   ├── Lesson 2: [TBD]
 │   └── Lesson 3: Replay Loop Breaker
 │       ├── Step 1: Spot the Story
 │       ├── Step 2: Name the Feeling
 │       └── Step 3: Reveal the Prediction
 ├── Phase 2: Repatterning
 │   ├── Lesson 4: Conviction Gauntlet
 │   ├── Lesson 5: [TBD]
 │   └── Lesson 6: [TBD]
 └── Phase 3: Stabilization
     ├── Lesson 7: Habit Harmonizer
     ├── Lesson 8: [TBD]
     └── Lesson 9: [TBD]
```

**Total**: 3 Phases × 3 Lessons = 9 Lessons
**Per Lesson**: 3 Steps (27 total steps)

---

## Neo4j Node Types

### 1. IASCurriculum (Root Node)

**Label**: `IASCurriculum`

**Properties**:
```cypher
{
  id: "ias-curriculum-v1",
  name: "Inner Architect System",
  version: "1.0",
  created_at: datetime(),
  updated_at: datetime(),
  description: "Neuroscience-backed guided breakthrough program for Analytical Empaths",
  target_audience: "Analytical Empaths",
  total_phases: 3,
  total_lessons: 9,
  total_steps: 27
}
```

### 2. Phase

**Label**: `IASPhase`

**Properties**:
```cypher
{
  id: "phase-{number}",
  name: "{Revelation|Repatterning|Stabilization}",
  order: {1|2|3},
  description: "Phase description",
  created_at: datetime(),
  updated_at: datetime()
}
```

**Example**:
```cypher
{
  id: "phase-1",
  name: "Revelation",
  order: 1,
  description: "Redirect Replay Loop from evidence-gathering to pattern recognition",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 3. Lesson

**Label**: `IASLesson`

**Properties**:
```cypher
{
  id: "lesson-{number}",
  name: "Lesson name",
  phase_order: {1|2|3},
  lesson_order: {1|2|3},
  global_order: {1-9},
  description: "What this lesson teaches",
  objective: "Learning objective",
  created_at: datetime(),
  updated_at: datetime()
}
```

**Example**:
```cypher
{
  id: "lesson-3",
  name: "Replay Loop Breaker",
  phase_order: 1,
  lesson_order: 3,
  global_order: 3,
  description: "Interrupt SSAR cycle: Shame → Spiral → Abandon → Restart",
  objective: "Break the replay loop and establish new cognitive patterns",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 4. Step

**Label**: `IASStep`

**Properties**:
```cypher
{
  id: "step-{lesson}-{number}",
  name: "Step name",
  order: {1|2|3},
  instruction: "What to do",
  tagline: "Brief memorable phrase",
  created_at: datetime(),
  updated_at: datetime()
}
```

**Example**:
```cypher
{
  id: "step-3-1",
  name: "Spot the Story",
  order: 1,
  instruction: "Identify the narrative your brain is trying to prove right now",
  tagline: "Observe the prediction. Don't collapse your life.",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 5. Obstacle (Leading False Belief)

**Label**: `IASObstacle`

**Properties**:
```cypher
{
  id: "obstacle-{step-id}",
  false_belief: "The limiting belief creating resistance",
  what_they_dread: ["List of specific dreads"],
  truth_they_dont_know: "The actual truth",
  created_at: datetime(),
  updated_at: datetime()
}
```

**Example**:
```cypher
{
  id: "obstacle-step-3-1",
  false_belief: "If I see the real story, I'll have to admit I've been wrong about everything—and that will unravel my entire identity",
  what_they_dread: [
    "Exposing themselves as a fraud or failure",
    "Dismantling competence and starting over",
    "Blowing up their life (quit job, leave relationship)",
    "Confirming worst fear: wasted years building wrong life"
  ],
  truth_they_dont_know: "Spotting the story doesn't mean you were wrong—it means you were loyal to old data. The story was adaptive once; now it's just outdated.",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 6. FalseAction (What They DON'T Need To Do)

**Label**: `IASFalseAction`

**Properties**:
```cypher
{
  id: "false-action-{step-id}-{number}",
  action: "Specific action they fear they must do",
  order: {1-n},
  created_at: datetime()
}
```

**Example**:
```cypher
{
  id: "false-action-step-3-1-1",
  action: "Confess to everyone that they've been 'faking it'",
  order: 1,
  created_at: datetime()
}
```

### 7. TrueAction (What They Actually Need To Do)

**Label**: `IASTrueAction`

**Properties**:
```cypher
{
  id: "true-action-{step-id}",
  action: "Actual required action",
  description: "How to do it",
  created_at: datetime(),
  updated_at: datetime()
}
```

**Example**:
```cypher
{
  id: "true-action-step-3-1",
  action: "Simply observe",
  description: "My brain has been running this prediction. Here's the evidence it's been collecting. That makes sense given X, Y, Z. Now I see it. No confession. No collapse. Just clarity.",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 8. SourceDocument

**Label**: `IASSourceDocument`

**Properties**:
```cypher
{
  id: "source-{doc-name}",
  title: "Document title",
  file_path: "Absolute path to file",
  doc_type: "{avatar|product|concept|client-story}",
  created_at: datetime(),
  updated_at: datetime()
}
```

---

## Relationships

### Curriculum → Phase
```cypher
(IASCurriculum)-[:HAS_PHASE {order: 1}]->(IASPhase)
```

### Phase → Lesson
```cypher
(IASPhase)-[:CONTAINS_LESSON {order: 1}]->(IASLesson)
```

### Lesson → Step
```cypher
(IASLesson)-[:HAS_STEP {order: 1}]->(IASStep)
```

### Step → Obstacle
```cypher
(IASStep)-[:HAS_OBSTACLE]->(IASObstacle)
```

### Step → TrueAction
```cypher
(IASStep)-[:DO_ACTION]->(IASTrueAction)
```

### Step → FalseAction
```cypher
(IASStep)-[:AVOID_ACTION {order: 1}]->(IASFalseAction)
```

### Curriculum → SourceDocument
```cypher
(IASCurriculum)-[:DOCUMENTED_IN {doc_type: "avatar"}]->(IASSourceDocument)
```

---

## Access Protocol

### ⛔ FORBIDDEN

- **NEVER** access Neo4j directly via:
  - Cypher queries from Python
  - `neo4j-driver` connections
  - `cypher-shell` commands
  - Docker exec into neo4j container
  - bolt:// connections
  - Reading NEO4J_PASSWORD from environment

### ✅ REQUIRED

- **ALWAYS** access via n8n webhooks:
  - `POST https://72.61.78.89:5678/webhook/ias/create-curriculum`
  - `POST https://72.61.78.89:5678/webhook/ias/add-lesson`
  - `POST https://72.61.78.89:5678/webhook/ias/query-curriculum`
  - `GET https://72.61.78.89:5678/webhook/ias/get-lesson/{id}`

---

## Query Patterns

### Get Full Curriculum Structure
```http
GET /webhook/ias/query-curriculum
Response:
{
  "curriculum": {...},
  "phases": [...],
  "lessons": [...]
}
```

### Get Specific Lesson with Steps
```http
GET /webhook/ias/get-lesson/lesson-3
Response:
{
  "lesson": {...},
  "steps": [...],
  "obstacles": [...],
  "actions": {...}
}
```

### Add New Lesson
```http
POST /webhook/ias/add-lesson
Body:
{
  "phase": "Revelation",
  "lesson": {
    "name": "New Lesson",
    "order": 2,
    "description": "..."
  }
}
```

---

## Implementation Notes

1. **All writes** go through n8n workflow validation
2. **All reads** return structured JSON from n8n
3. **No direct Cypher** allowed outside n8n workflows
4. **Idempotency**: Creating same node twice returns existing node
5. **Versioning**: Track curriculum version for schema migrations

---

## Next Steps

1. Create n8n workflow: `ias-curriculum-manager.json`
2. Create population script: `scripts/populate_ias_curriculum.py`
3. Populate initial content from user-provided Replay Loop Breaker data
4. Extend with remaining 8 lessons as content becomes available

---

**PRIME DIRECTIVE**: This is HIGH VALUE business asset. All access MUST respect the n8n-only protocol.
