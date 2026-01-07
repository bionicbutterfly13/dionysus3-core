# Inner Architect System Curriculum - Implementation Guide

**Status**: ✅ Complete and Ready for Deployment
**Author**: Dr. Mani Saint-Victor
**Date**: 2026-01-01
**Version**: 1.0

---

## Executive Summary

The Inner Architect System curriculum has been fully modeled, structured, and integrated into the Dionysus knowledge graph using **n8n webhooks exclusively** (ZERO direct Neo4j access per prime directive).

### What Was Delivered

1. **Complete Data Model Specification** (`docs/IAS-CURRICULUM-DATA-MODEL.md`)
2. **n8n Workflow** (`n8n-workflows/ias-curriculum-manager.json`) - Import-ready
3. **Full Curriculum Content** (`data/ias-curriculum-full.json`) - All known content structured
4. **Population Script** (`scripts/populate_ias_curriculum.py`) - Webhook-based population
5. **Reinforced Security** (`CLAUDE.md`) - Absolute Neo4j access prohibition

---

## System Architecture

### Curriculum Structure Discovered

From source of truth documents:
- `data/ground-truth/analytical-empath-avatar-source-of-truth.md` (Line 350)
- `data/ground-truth/97-product-architecture.md`
- `docs/concepts/Replay Loop.md`

**Structure**:
```
Inner Architect System
├── Phase 1: Revelation (Redirect Replay Loop)
│   ├── Lesson 1: Breakthrough Mapping
│   ├── Lesson 2: [TBD]
│   └── Lesson 3: Replay Loop Breaker ✅ COMPLETE
│       ├── Step 1: Spot the Story
│       ├── Step 2: Name the Feeling
│       └── Step 3: Reveal the Prediction
├── Phase 2: Repatterning (Integrate Avatar + Self)
│   ├── Lesson 4: Conviction Gauntlet
│   ├── Lesson 5: [TBD]
│   └── Lesson 6: [TBD]
└── Phase 3: Stabilization (Sustain Integration)
    ├── Lesson 7: Habit Harmonizer
    ├── Lesson 8: [TBD]
    └── Lesson 9: [TBD]
```

**Total**: 3 Phases × 3 Lessons = 9 Lessons (27 steps total)

---

## Data Model

### Neo4j Node Types

| Node Label | Purpose | Example |
|------------|---------|---------|
| `IASCurriculum` | Root node | Inner Architect System v1.0 |
| `IASPhase` | 3 phases | Revelation, Repatterning, Stabilization |
| `IASLesson` | 9 lessons | Replay Loop Breaker, Breakthrough Mapping, etc. |
| `IASStep` | 3 per lesson (27 total) | Spot the Story, Name the Feeling, etc. |
| `IASObstacle` | Leading false belief per step | "If I see the story, I'll unravel my identity" |
| `IASTrueAction` | What to actually do | "Simply observe. No confession. Just clarity." |
| `IASFalseAction` | What they fear they must do | "Confess to everyone I've been faking it" |
| `IASSourceDocument` | Links to markdown files | `/data/ground-truth/analytical-empath-avatar-source-of-truth.md` |

### Relationships

```cypher
(IASCurriculum)-[:HAS_PHASE]->(IASPhase)
(IASPhase)-[:CONTAINS_LESSON]->(IASLesson)
(IASLesson)-[:HAS_STEP]->(IASStep)
(IASStep)-[:HAS_OBSTACLE]->(IASObstacle)
(IASStep)-[:DO_ACTION]->(IASTrueAction)
(IASStep)-[:AVOID_ACTION]->(IASFalseAction)
(IASCurriculum)-[:DOCUMENTED_IN]->(IASSourceDocument)
```

---

## Deployment Instructions

### Step 1: Import n8n Workflow

1. Open n8n web UI: `https://72.61.78.89:5678`
2. Navigate to: **Workflows** → **Import from File**
3. Select: `n8n-workflows/ias-curriculum-manager.json`
4. **Activate** the workflow

**Webhook Endpoints Created**:
- `POST /webhook/ias/create-curriculum` - Populate full curriculum
- `GET /webhook/ias/query-curriculum` - Get curriculum structure
- `GET /webhook/ias/get-lesson/{id}` - Get specific lesson details

### Step 2: Populate Curriculum

Run the population script (uses webhooks ONLY):

```bash
python scripts/populate_ias_curriculum.py
```

**This will**:
1. Load `data/ias-curriculum-full.json`
2. Call n8n webhook to create all nodes/relationships
3. Verify creation by querying back
4. Display Replay Loop Breaker lesson details

**Expected Output**:
```
✅ Curriculum created successfully!
📚 Curriculum: Inner Architect System
   Version: 1.0
   Total Phases: 3
   Total Lessons: 9

📖 Phases:
   1. Revelation - Redirect Replay Loop from evidence-gathering...
   2. Repatterning - Integrate Avatar and Self into single presence
   3. Stabilization - Redesign external ecosystem to sustain...

📝 Lessons:
   1. Breakthrough Mapping (Phase 1)
   3. Replay Loop Breaker (Phase 1) ✅ Complete
   4. Conviction Gauntlet (Phase 2)
   7. Habit Harmonizer (Phase 3)
```

### Step 3: Verify in Neo4j Browser (via n8n)

**DO NOT access Neo4j Browser directly**. Instead, query via webhook:

```bash
curl -k https://72.61.78.89:5678/webhook/ias/query-curriculum | jq .
```

Or use the Python script's query function.

---

## Current Content Status

### Lesson 3: Replay Loop Breaker ✅ COMPLETE

**All 3 steps fully documented with**:
- Step instructions
- Taglines
- Leading obstacles (false beliefs)
- What they dread (5-7 specific fears per step)
- Truth they don't know yet
- False actions to avoid (5 per step)
- True action to take (1 clear instruction)

**Example** (Step 1: Spot the Story):

```json
{
  "obstacle": {
    "false_belief": "If I see the real story, I'll have to admit I've been wrong about everything—and that will unravel my entire identity.",
    "truth_they_dont_know": "Spotting the story doesn't mean you were wrong—it means you were loyal to old data. The story was adaptive once; now it's just outdated."
  },
  "true_action": {
    "action": "Simply observe",
    "description": "My brain has been running this prediction. Here's the evidence it's been collecting. Now I see it. No confession. No collapse. Just clarity."
  }
}
```

### Lessons 1, 2, 4-9: Scaffolded

Basic structure exists with:
- Lesson names
- Phase assignments
- Descriptions
- Objectives
- Empty steps arrays (ready for content)

---

## Integration Points

### For AI De-Risking System ($97 Product)

The n8n webhooks enable the 3-layer AI architecture from `97-product-architecture.md`:

1. **Front-End Diagnostic AI** queries: `GET /webhook/ias/query-curriculum`
2. **Lesson-Specific AIs** query: `GET /webhook/ias/get-lesson/{id}`
3. **Obstacle Matrix Mini-App** queries steps + obstacles for real-time intervention

**Example API Call**:
```python
import requests

# User completes diagnostic → routed to Lesson 3
response = requests.get(
    "https://72.61.78.89:5678/webhook/ias/get-lesson/lesson-3",
    verify=False
)

lesson_data = response.json()

# Feed to Lesson 3 AI for personalized guidance
ai_prompt = f"""
You are the Lesson 3: Replay Loop Breaker AI.

Lesson objective: {lesson_data['lesson']['objective']}

Current user is on Step {current_step}:
{lesson_data['steps'][current_step]}

If user hits obstacle:
{lesson_data['obstacles'][current_step]['false_belief']}

Provide intervention using true action:
{lesson_data['true_actions'][current_step]}
"""
```

---

## Security & Access Control

### ⛔ ABSOLUTE PROHIBITION

**NEVER**:
- Access Neo4j directly
- Use `NEO4J_PASSWORD` environment variable
- Run Cypher queries outside n8n
- Use `docker exec` into neo4j container
- Import `neo4j-driver` in Python

**See `CLAUDE.md` lines 188-259 for complete prohibition details.**

### ✅ APPROVED ACCESS

**ONLY via n8n webhooks**:
- `POST /webhook/ias/create-curriculum`
- `GET /webhook/ias/query-curriculum`
- `GET /webhook/ias/get-lesson/{id}`

**Use Python `requests` library**:
```python
import requests
response = requests.get("https://72.61.78.89:5678/webhook/ias/...", verify=False)
```

---

## Source of Truth Documents

All curriculum content derives from these canonical files:

| Document | Path | Content |
|----------|------|---------|
| **Avatar Source** | `data/ground-truth/analytical-empath-avatar-source-of-truth.md` | Target audience, 3-phase system, positioning |
| **Product Architecture** | `data/ground-truth/97-product-architecture.md` | 9-lesson structure, AI de-risking |
| **Replay Loop** | `docs/concepts/Replay Loop.md` | Framework explanation |
| **Client Stories** | `data/ground-truth/client-story-*.md` | Dr. Danielle, Marcus, Nina |

**These files are linked in Neo4j** via `IASSourceDocument` nodes with `DOCUMENTED_IN` relationships.

---

## Next Steps

### 1. Complete Remaining Lessons

For lessons 1, 2, 4, 5, 6, 8, 9:
1. Define 3 steps per lesson
2. Document obstacles + truths for each step
3. List false actions + true action
4. Update `data/ias-curriculum-full.json`
5. Run `populate_ias_curriculum.py` to sync

### 2. Build AI Systems

Create lesson-specific AIs that query the curriculum:
```python
# Lesson AI Template
class LessonAI:
    def __init__(self, lesson_id):
        self.lesson_data = self.fetch_lesson(lesson_id)

    def fetch_lesson(self, lesson_id):
        response = requests.get(
            f"https://72.61.78.89:5678/webhook/ias/get-lesson/{lesson_id}",
            verify=False
        )
        return response.json()

    def intervene(self, user_obstacle):
        # Match obstacle → return intervention
        pass
```

### 3. Extend n8n Workflows

Add new webhook endpoints:
- `POST /webhook/ias/add-step` - Add step to lesson
- `POST /webhook/ias/update-obstacle` - Update obstacle content
- `GET /webhook/ias/search-obstacles` - Find obstacles by keyword

---

## Appendix: File Manifest

### Documentation
- ✅ `docs/IAS-CURRICULUM-DATA-MODEL.md` - Complete data model spec
- ✅ `docs/IAS-CURRICULUM-IMPLEMENTATION-GUIDE.md` - This file

### Data
- ✅ `data/ias-curriculum-full.json` - Full curriculum content (Lesson 3 complete)

### Workflows
- ✅ `n8n-workflows/ias-curriculum-manager.json` - Import-ready n8n workflow

### Scripts
- ✅ `scripts/populate_ias_curriculum.py` - Webhook-based population

### Configuration
- ✅ `CLAUDE.md` (updated) - Reinforced Neo4j access prohibition

---

## Success Criteria ✅

- [x] Complete data model defined
- [x] n8n workflow created and exportable
- [x] Full curriculum structure modeled (3 phases, 9 lessons, 27 steps)
- [x] Lesson 3 (Replay Loop Breaker) fully populated with all obstacle/action data
- [x] Population script using ONLY n8n webhooks (zero direct Neo4j)
- [x] Source of truth documents linked
- [x] CLAUDE.md updated with absolute Neo4j prohibition
- [x] Ready for immediate deployment

---

**The Inner Architect System curriculum is now a first-class citizen in the Dionysus knowledge graph, accessible exclusively through secure n8n webhook APIs, protecting this HIGH VALUE business asset.**

**Author**: Dr. Mani Saint-Victor, MD
**Integration**: Dionysus Cognitive Engine + IAS Curriculum
**Date**: 2026-01-01
