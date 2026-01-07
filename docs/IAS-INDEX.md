# Inner Architect System - Documentation Index

**Navigation Hub**: Complete IAS curriculum documentation and implementation guides

**Created**: 2026-01-02
**Author**: Dr. Mani Saint-Victor, MD
**Status**: Production-Ready

---

## 📚 Core Documentation

### Data Models & Architecture

**[IAS-MERGED-DATA-MODEL.md](./IAS-MERGED-DATA-MODEL.md)** - Unified curriculum model
- Business layer (Curriculum → Module → Lesson)
- Pedagogical layer (Lesson → Step → Obstacle/Actions)
- 10 node types with full schemas
- Webhook operations reference
- Use case examples (marketing + AI coaching)

**[IAS-CURRICULUM-DATA-MODEL.md](./IAS-CURRICULUM-DATA-MODEL.md)** - Original pedagogical model
- 8 node types focused on teaching framework
- Step-level granularity with obstacles
- Source of truth document linking
- Neo4j access protocol

**[IAS-CURRICULUM-IMPLEMENTATION-GUIDE.md](./IAS-CURRICULUM-IMPLEMENTATION-GUIDE.md)** - Deployment guide
- Complete deployment instructions
- Security & access control
- Integration points with $97 product
- Success criteria checklist

---

## 🔧 Implementation Files

### n8n Workflows

**n8n-workflows/ias-unified-manager.json** - Production workflow
- 10 operation types (5 business + 5 pedagogical)
- HMAC signature verification
- Single endpoint: `/webhook/ias/v1/manipulate`
- Operations:
  - Business: `upsert_curriculum`, `upsert_module`, `upsert_lesson`, `link_asset`, `upsert_launch`
  - Pedagogical: `upsert_step`, `upsert_obstacle`, `upsert_true_action`, `upsert_false_action`, `link_source_document`

**n8n-workflows/ias-curriculum-manager.json** - Pedagogical-only workflow
- Original 3-endpoint approach
- Query operations for curriculum structure
- Lesson detail retrieval

**n8n-workflows/ias_curriculum_manipulation.json** - Generic business workflow
- 5 operation types
- Asset linking support
- Launch event management

### Population Scripts

**scripts/populate_ias_unified.py** ⭐ **RECOMMENDED**
- Complete unified population
- All 9 lessons + Lesson 3 pedagogical framework
- Source document linking
- HMAC signature support

**scripts/populate_ias_curriculum.py** - Pedagogical-only population
- 3 phases, 9 lessons (scaffolded)
- Lesson 3 fully detailed
- 3-endpoint webhook approach

**scripts/seed_ias_via_webhook.py** - Business-only population
- Full 9-lesson structure
- Focus areas, transformations
- Action steps as assets

---

## 📖 Curriculum Structure

### 3 Phases × 9 Lessons = 27 Steps

#### Phase 1: REVELATION
**Theme**: Predictive Self-Mapping
**Promise**: Expose the hidden sabotage loop that quietly drives every setback
**Goal**: From Hidden Patterns to Clear Insights

1. **Breakthrough Mapping** (Focus: Self-Awareness)
   - From unknowingly held back to consciously aware of patterns

2. **Mosaeic Method** (Focus: Mental Agility)
   - From performance anxiety to self-regulated clarity in high-pressure situations

3. **Replay Loop Breaker** (Focus: Emotional Clarity & Self-Regulation) ✅ **COMPLETE**
   - From drowning in mental replays to skillful loop breaking
   - **Step 1**: Spot the Story
   - **Step 2**: Name the Feeling
   - **Step 3**: Reveal the Prediction

#### Phase 2: REPATTERNING
**Theme**: Reconsolidation Design
**Promise**: Recode that loop fast—spark the new identity in real time
**Goal**: From Internal Conflict to Sustained Clarity

4. **Conviction Gauntlet** (Focus: Hope)
   - From belief disruption to integrating new, empowering convictions

5. **Perspective Matrix** (Focus: Insight)
   - From rigid certainty to flexible, multi-perspective awareness

6. **Vision Accelerator** (Focus: Inspiration)
   - From playing small to envisioning and owning an authentic future

#### Phase 3: STABILIZATION
**Theme**: Identity–Action Synchronization
**Promise**: Embed the identity so actions, habits, and results stay congruent
**Goal**: From Fragile to Fortified Growth

7. **Habit Harmonizer** (Focus: Conviction)
   - From relapse fear to anchoring new beliefs

8. **Execution Engine** (Focus: Momentum)
   - From stalled motivation to consistent, value-aligned action

9. **Growth Anchor** (Focus: Perseverance)
   - From isolated progress to embedded, resilient growth

---

## 🎯 Lesson 3: Replay Loop Breaker (Complete Framework)

### Step 1: Spot the Story
**Instruction**: Identify the narrative your brain is trying to prove right now
**Tagline**: Observe the prediction. Don't collapse your life.

**Obstacle**:
- **False Belief**: "If I see the real story, I'll have to admit I've been wrong about everything"
- **What They Dread**:
  - Exposing themselves as a fraud or failure
  - Dismantling competence and starting over
  - Blowing up their life (quit job, leave relationship)
  - Confirming worst fear: wasted years building wrong life
- **Truth**: "Spotting the story doesn't mean you were wrong—it means you were loyal to old data"

**False Actions** (what they fear they must do):
1. Confess to everyone that they've been 'faking it'
2. Quit their job or relationship
3. Relive every moment they 'got it wrong'
4. Justify or defend the old story
5. Generate a perfect replacement narrative in the same breath

**True Action**: Simply observe
- "My brain has been running this prediction. Here's the evidence it's been collecting. Now I see it. No confession. No collapse. Just clarity."

### Step 2: Name the Feeling
**Instruction**: Label the emotion fueling the spiral: shame, fear, guilt, or inadequacy
**Tagline**: Name it. Don't become it.

**Obstacle**:
- **False Belief**: "If I name the feeling, it will consume me"
- **What They Dread**:
  - That naming shame means becoming it
  - That the emotion will be bottomless
  - That naming it makes it 'real' in a way that can't be undone
  - That emotions prove weakness
  - That the floodgates will open and they'll lose composure
- **Truth**: "Naming the feeling de-fuses you from it. 'I AM ashamed' becomes 'Shame is present.' Reduces hijack by 40-60%."

**False Actions**:
1. Sit with the feeling for hours in painful excavation
2. Cry or 'release' it in performative cathartic way
3. Trace it back to childhood wounds
4. Justify why they feel this way
5. Fix or eliminate the feeling immediately

**True Action**: Label it in one sentence
- "The feeling fueling this loop right now is [shame/fear/inadequacy/guilt]. That's it. Label it. Move on."

### Step 3: Reveal the Prediction
**Instruction**: Uncover what outcome the replay is trying to protect you from
**Tagline**: See the prediction. Test it against reality.

**Obstacle**:
- **False Belief**: "If I uncover what I'm really afraid of, I'll have to face that it's true"
- **What They Dread**:
  - That the prediction is accurate and inevitable
  - "If I'm afraid of rejection, I'm actually unlovable"
  - "If I'm afraid of failing, I don't have what it takes"
  - That the fear is rational, not paranoid
  - That they'll realize how fragile their life structure is
  - That the prediction sounds 'small' and they'll be embarrassed
  - That revealing it means having to immediately fix it
- **Truth**: "The prediction is your nervous system's best guess based on old data—not a prophecy. Seeing it makes it testable."

**False Actions**:
1. Prove the prediction wrong immediately
2. Analyze every past instance where the fear 'came true'
3. Defend themselves against the prediction
4. Build an airtight case for why the fear is irrational
5. Eliminate the fear before moving forward

**True Action**: Complete this sentence
- "The outcome this replay is trying to protect me from is: [losing respect/being exposed/being abandoned/failing publicly]."

---

## 🔐 Security & Access

### ⛔ ABSOLUTE PROHIBITION
**NEVER**:
- Access Neo4j directly via Cypher queries
- Use `neo4j-driver` connections
- Run `cypher-shell` commands
- Use `docker exec` into neo4j container
- Read `NEO4J_PASSWORD` environment variable

### ✅ APPROVED ACCESS
**ONLY via n8n webhooks**:
- `POST https://72.61.78.89:5678/webhook/ias/v1/manipulate`
- Use Python `requests` library
- Include HMAC signature: `X-Dionysus-Signature: sha256=...`

---

## 📂 Source of Truth Documents

| Document | Path | Content |
|----------|------|---------|
| **Avatar Source** | `data/ground-truth/analytical-empath-avatar-source-of-truth.md` | Target audience, 3-phase system, positioning |
| **Product Architecture** | `data/ground-truth/97-product-architecture.md` | 9-lesson structure, AI de-risking |
| **Replay Loop** | `docs/concepts/Replay Loop.md` | Framework explanation |
| **Client Stories** | `data/ground-truth/client-story-*.md` | Dr. Danielle, Marcus, Nina |

---

## 🚀 Quick Start

### 1. Import n8n Workflow
```bash
# In n8n UI:
# Workflows → Import from File → n8n-workflows/ias-unified-manager.json
# Activate the workflow
```

### 2. Set Environment
```bash
export MEMEVOLVE_HMAC_SECRET="your-secret-here"
```

### 3. Populate Curriculum
```bash
python scripts/populate_ias_unified.py
```

### 4. Query via Webhook
```python
import requests
response = requests.post(
    "https://72.61.78.89:5678/webhook/ias/v1/manipulate",
    json={"operation": "query_curriculum"}
)
```

---

## 🎯 Use Cases

### Marketing Operations
- Query all lessons for landing page content
- Display phase promises and transformations
- Link to launch events with pricing

### AI Coaching Interventions
- Detect user stuck on specific step
- Retrieve obstacle + truth for intervention
- Present true action vs false actions
- Track progress through steps

### Content Development
- Add new lessons as content becomes available
- Extend pedagogical framework to remaining lessons
- Link worksheets, videos, and resources

---

## 📊 Status Summary

**Business Layer**: ✅ Complete (all 9 lessons)
**Pedagogical Layer**: 🔄 Partial (Lesson 3 complete, 8 lessons pending)
**n8n Workflows**: ✅ Production-ready
**Security**: ✅ HMAC + webhook-only access enforced
**Documentation**: ✅ Comprehensive

---

## 🔄 Next Steps

1. **Complete Pedagogical Framework**: Add steps/obstacles for Lessons 1, 2, 4-9
2. **Link Assets**: Connect worksheets, videos, and resources to lessons
3. **Deploy to Production**: Import workflow, populate curriculum
4. **Build AI Coaching**: Integrate with $97 AI de-risking product
5. **Track Launch**: Connect to Jan 8 launch event

---

**This is a HIGH VALUE business asset. All access MUST use n8n webhooks exclusively.**

**Last Updated**: 2026-01-02
**Status**: Production-Ready
**Integration**: Dionysus Cognitive Engine + IAS Curriculum
