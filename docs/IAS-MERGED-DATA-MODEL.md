# Inner Architect System - Merged Data Model

**Version**: 2.0 (Unified)
**Author**: Dr. Mani Saint-Victor
**Date**: 2026-01-02
**Status**: Production

---

## Overview

This model merges two complementary approaches:
1. **Business Layer**: Course structure, marketing, launches (Curriculum → Module → Lesson)
2. **Coaching Layer**: Teaching framework, obstacles, interventions (Lesson → Step → Obstacle/Actions)

**Goal**: Single unified graph supporting both marketing operations AND AI-powered coaching.

---

## Unified Structure

```
Curriculum
├── Module (Phase)
│   ├── Lesson
│   │   ├── Step (NEW - pedagogical)
│   │   │   ├── Obstacle (NEW - false beliefs, dreads, truths)
│   │   │   ├── TrueAction (NEW - what to actually do)
│   │   │   └── FalseAction (NEW - what they fear they must do)
│   │   └── Asset (marketing materials, worksheets)
│   └── Asset (phase-level resources)
├── LaunchEvent
└── SourceDocument (source of truth references)
```

---

## Node Types

### 1. Curriculum (Root)
```cypher
{
  id: "ias-core-v1",
  title: "The Inner Architect System",
  description: "Neuroscience-backed guided breakthrough program",
  target_audience: "Analytical Empaths",
  total_modules: 3,
  total_lessons: 9,
  created_at: datetime(),
  updated_at: datetime()
}
```

### 2. Module (Phase)
```cypher
{
  id: "module-phase-1",
  title: "REVELATION: Predictive Self-Mapping",
  phase: "Revelation",
  order: 1,
  promise: "Expose the hidden sabotage loop...",
  goal: "From Hidden Patterns to Clear Insights",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 3. Lesson
```cypher
{
  id: "lesson-3-v1",
  title: "Replay Loop Breaker",
  order: 3,
  focus: "Emotional Clarity & Self-Regulation",
  transformation: "From drowning in mental replays to skillful loop breaking",
  has_pedagogical_framework: true,  // NEW - indicates Step nodes exist
  created_at: datetime(),
  updated_at: datetime()
}
```

### 4. Step (NEW - Pedagogical Layer)
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

### 5. Obstacle (NEW - Pedagogical Layer)
```cypher
{
  id: "obstacle-step-3-1",
  false_belief: "If I see the real story, I'll have to admit I've been wrong about everything",
  what_they_dread: [
    "Exposing themselves as a fraud or failure",
    "Dismantling competence and starting over",
    "Blowing up their life (quit job, leave relationship)",
    "Confirming worst fear: wasted years building wrong life"
  ],
  truth_they_dont_know: "Spotting the story doesn't mean you were wrong—it means you were loyal to old data",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 6. TrueAction (NEW - Pedagogical Layer)
```cypher
{
  id: "true-action-step-3-1",
  action: "Simply observe",
  description: "My brain has been running this prediction. Here's the evidence it's been collecting. Now I see it. No confession. No collapse. Just clarity.",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 7. FalseAction (NEW - Pedagogical Layer)
```cypher
{
  id: "false-action-step-3-1-1",
  action: "Confess to everyone that they've been 'faking it'",
  order: 1,
  why_unnecessary: "Seeing the pattern doesn't require public confession",
  created_at: datetime()
}
```

### 8. Asset (Existing - Marketing/Resources)
```cypher
{
  id: "asset-lesson-3-worksheet",
  type: "worksheet" | "video" | "action_step" | "notion_snapshot",
  path: "file:///path/to/resource" | "https://..." | "N/A",
  description: "Resource description",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 9. LaunchEvent (Existing - Business)
```cypher
{
  id: "launch-ias-jan8",
  deadline: datetime("2026-01-08T23:59:59-05:00"),
  price_charter: 3975,
  price_regular: 5475,
  framework: "Todd Brown Bullet Campaign",
  created_at: datetime(),
  updated_at: datetime()
}
```

### 10. SourceDocument (NEW - References)
```cypher
{
  id: "source-avatar-sot",
  title: "Analytical Empath Avatar Source of Truth",
  file_path: "/Volumes/Asylum/dev/dionysus3-core/data/ground-truth/analytical-empath-avatar-source-of-truth.md",
  doc_type: "avatar" | "product" | "concept",
  created_at: datetime(),
  updated_at: datetime()
}
```

---

## Relationships

```cypher
// Business Layer
(Curriculum)-[:HAS_MODULE {order}]->(Module)
(Module)-[:CONTAINS {order}]->(Lesson)
(Curriculum)-[:HAS_LAUNCH]->(LaunchEvent)
(Curriculum)-[:HAS_ASSET]->(Asset)
(Module)-[:HAS_ASSET]->(Asset)
(Lesson)-[:HAS_ASSET]->(Asset)

// Pedagogical Layer (NEW)
(Lesson)-[:HAS_STEP {order}]->(Step)
(Step)-[:HAS_OBSTACLE]->(Obstacle)
(Step)-[:DO_ACTION]->(TrueAction)
(Step)-[:AVOID_ACTION {order}]->(FalseAction)

// References
(Curriculum)-[:DOCUMENTED_IN {doc_type}]->(SourceDocument)
```

---

## Webhook Operations

### Existing Operations (Business Layer)
- `upsert_curriculum` - Create/update curriculum root
- `upsert_module` - Create/update phase module
- `upsert_lesson` - Create/update lesson
- `link_asset` - Attach marketing materials
- `upsert_launch` - Create launch event

### New Operations (Pedagogical Layer)
- `upsert_step` - Add step to lesson
- `upsert_obstacle` - Add obstacle to step
- `upsert_true_action` - Define what to actually do
- `upsert_false_action` - Define what they fear they must do
- `link_source_document` - Reference source of truth

### Query Operations
- `query_curriculum` - Get full structure
- `query_lesson` - Get lesson with steps/obstacles
- `query_step` - Get step details for AI coaching

---

## Access Pattern

**n8n Webhook**: `POST https://72.61.78.89:5678/webhook/ias/v1/manipulate`

**Request Format**:
```json
{
  "operation": "upsert_step",
  "data": {
    "parent_id": "lesson-3-v1",
    "id": "step-3-1",
    "name": "Spot the Story",
    "order": 1,
    "instruction": "...",
    "tagline": "..."
  }
}
```

**HMAC Signature Required**: `X-Dionysus-Signature: sha256=...`

---

## Content Status

### Fully Populated
- **All 9 Lessons**: Basic structure (title, focus, transformation)
  - Phase 1: Breakthrough Mapping, Mosaeic Method, Replay Loop Breaker
  - Phase 2: Conviction Gauntlet, Perspective Matrix, Vision Accelerator
  - Phase 3: Habit Harmonizer, Execution Engine, Growth Anchor

### Pedagogical Framework Complete
- **Lesson 3 (Replay Loop Breaker)**: Full 3 steps with obstacles/actions
  - Step 1: Spot the Story
  - Step 2: Name the Feeling
  - Step 3: Reveal the Prediction

### Pending
- **Lessons 1, 2, 4-9**: Add pedagogical framework (steps, obstacles, actions)
- **All Lessons**: Link to specific assets (worksheets, videos)
- **Launch Event**: Connect to Jan 8 launch

---

## Migration Path

### Phase 1: Extend Schema ✅
- Add Step, Obstacle, TrueAction, FalseAction, SourceDocument node types
- Update n8n workflow with new operations

### Phase 2: Populate Base Content ✅
- Load all 9 lessons from `seed_ias_via_webhook.py`
- Verify Curriculum → Module → Lesson structure exists

### Phase 3: Add Pedagogical Layer (In Progress)
- Add Lesson 3 steps/obstacles/actions
- Test AI coaching queries

### Phase 4: Complete Remaining Lessons
- Add steps/obstacles for Lessons 1, 2, 4-9 as content becomes available

---

## Use Cases

### Marketing/Business Operations
```python
# Query all lessons for landing page
response = requests.post(webhook_url, json={
    "operation": "query_curriculum"
})
# Returns: Curriculum → Modules → Lessons with focus/transformation
```

### AI Coaching Intervention
```python
# User stuck on Lesson 3, Step 1
response = requests.post(webhook_url, json={
    "operation": "query_step",
    "data": {"id": "step-3-1"}
})
# Returns: Step with obstacle, true_action, false_actions
# AI uses obstacle.truth_they_dont_know for intervention
```

### Launch Management
```python
# Check launch deadline
response = requests.post(webhook_url, json={
    "operation": "query_launch",
    "data": {"curriculum_id": "ias-core-v1"}
})
# Returns: LaunchEvent with pricing, deadline, framework
```

---

## Security

**⛔ ABSOLUTE PROHIBITION**: Never access Neo4j directly
**✅ ONLY**: n8n webhook with HMAC signature verification

See `CLAUDE.md` lines 188-259 for complete security protocol.

---

**This merged model preserves all existing business functionality while adding the pedagogical layer needed for AI-powered coaching interventions.**
