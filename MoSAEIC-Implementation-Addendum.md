# MoSAEIC Protocol - Implementation Reference Addendum

**Parent Document**: MoSAEIC-Protocol-Spec.md (Feature 009)
**Status**: DRAFT - Reflects target state after correction
**Date**: 2025-12-22
**Critical Note**: Current codebase does NOT match this specification. See `MoSAEIC-Implementation-Correction-Guide.md` for migration instructions.

---

## Purpose

This addendum provides technical implementation details for the MoSAEIC Protocol specification. It documents the database schema, API contracts, and service architecture that implement the 5-phase intervention system.

**⚠️ IMPORTANT**: The current codebase (as of 2025-12-22) uses an incorrect schema with fields `mental`, `observation`, `senses`, `actions`, `emotions`. This addendum describes the **correct target state** after migration to the canonical 5-window structure: `Senses`, `Actions`, `Emotions`, `Impulses`, `Cognitions`.

---

## Database Schema (PostgreSQL)

### Core Tables

#### `fivewindowcaptures`
Stores Phase 2 episodic memory captures across the 5 MoSAEIC dimensions.

```sql
CREATE TABLE fivewindowcaptures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sessionid UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- The 5 MoSAEIC Windows (JSONB for flexible content)
    senses JSONB NOT NULL,          -- Interoceptive & exteroceptive sensations, body state
    actions JSONB NOT NULL,         -- Executed behaviors, motor output
    emotions JSONB NOT NULL,        -- Feelings, affective tone, valence
    impulses JSONB NOT NULL,        -- Urges, action tendencies, behavioral drives
    cognitions JSONB NOT NULL,      -- Thoughts, interpretations, predictions (core belief source)
    
    -- Metadata
    context JSONB,                  -- Trigger context, environmental context
    emotionalintensity NUMERIC(3,1) CHECK (emotionalintensity >= 0 AND emotionalintensity <= 10),
    turningpoint BOOLEAN DEFAULT FALSE,
    preserveindefinitely BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fivewindowcaptures_sessionid ON fivewindowcaptures(sessionid);
CREATE INDEX idx_fivewindowcaptures_createdat ON fivewindowcaptures(createdat);
CREATE INDEX idx_fivewindowcaptures_turningpoint ON fivewindowcaptures(turningpoint);
CREATE INDEX idx_fivewindowcaptures_emotionalintensity ON fivewindowcaptures(emotionalintensity);
```

**JSONB Structure Examples**:
```json
{
  "senses": {
    "interoceptive": "Heart racing, tension in shoulders, shallow breathing",
    "exteroceptive": "Fluorescent lighting, quiet office, cold temperature",
    "bodyState": "Fatigued, tense, alert"
  },
  "actions": {
    "executed": "Checked email repeatedly, avoided starting task",
    "motorOutput": "Hunched posture, fidgeting with pen"
  },
  "emotions": {
    "primary": "Anxiety",
    "secondary": ["Frustration", "Self-doubt"],
    "valence": "negative",
    "arousal": "high"
  },
  "impulses": {
    "urges": "Want to leave the room, desire to check phone",
    "avoidance": "Avoiding difficult conversation",
    "approach": "None active"
  },
  "cognitions": {
    "automaticThoughts": "I'm going to fail at this",
    "interpretations": "This means I'm not competent",
    "predictions": "If I try, I'll mess it up and people will judge me",
    "coreBelief": "I am incompetent" // <-- Extracted in Phase 3
  }
}
```

---

#### `maladaptivepatterns`
Stores Phase 1 detected recurring maladaptive patterns.

```sql
CREATE TABLE maladaptivepatterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Pattern Content
    beliefcontent TEXT NOT NULL,                    -- Core maladaptive belief
    domain VARCHAR(50) NOT NULL,                    -- Life domain (self, relationships, work, etc.)
    triggercontext JSONB,                           -- Common trigger contexts
    
    -- Pattern Tracking
    recurrencecount INTEGER DEFAULT 1,
    linkedcaptureids UUID[] DEFAULT '{}',           -- Array of capture IDs exhibiting pattern
    lastoccurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    firstdetected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Severity & Intervention Status
    severityscore NUMERIC(3,2) CHECK (severityscore >= 0 AND severityscore <= 1),
    interventionstatus VARCHAR(20) DEFAULT 'detected',  -- detected, queued, active, resolved
    
    -- Timestamps
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_maladaptivepatterns_domain ON maladaptivepatterns(domain);
CREATE INDEX idx_maladaptivepatterns_interventionstatus ON maladaptivepatterns(interventionstatus);
CREATE INDEX idx_maladaptivepatterns_severityscore ON maladaptivepatterns(severityscore DESC);
```

---

#### `beliefrewrites`
Stores Phase 4 rewritten beliefs (the new adaptive beliefs).

```sql
CREATE TABLE beliefrewrites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Belief Content
    newbelief TEXT NOT NULL,                        -- The rewritten adaptive belief
    oldbeliefid UUID REFERENCES maladaptivepatterns(id),  -- Link to original pattern
    domain VARCHAR(50) NOT NULL,                    -- Life domain
    
    -- Confidence Tracking
    adaptivenessscore NUMERIC(3,2) CHECK (adaptivenessscore >= 0 AND adaptivenessscore <= 1),
    predictioncount INTEGER DEFAULT 0,              -- How many times belief made prediction
    successcount INTEGER DEFAULT 0,                 -- How many predictions were correct
    failurecount INTEGER DEFAULT 0,                 -- How many predictions were incorrect
    
    -- Timestamps
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_beliefrewrites_domain ON beliefrewrites(domain);
CREATE INDEX idx_beliefrewrites_adaptivenessscore ON beliefrewrites(adaptivenessscore);
CREATE INDEX idx_beliefrewrites_oldbeliefid ON beliefrewrites(oldbeliefid);
```

---

#### `verificationencounters`
Stores Phase 5 verification of which belief activated (old vs new).

```sql
CREATE TABLE verificationencounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Links
    beliefid UUID NOT NULL REFERENCES beliefrewrites(id),
    sessionid UUID NOT NULL REFERENCES sessions(id),
    
    -- Encounter Details
    triggeroccurredat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    predictioncontent TEXT,                         -- What belief predicted would happen
    observedoutcome TEXT,                           -- What actually happened
    predictioncorrect BOOLEAN,                      -- Did prediction match reality?
    beliefactivated VARCHAR(10),                    -- 'old' or 'new'
    
    -- Context
    contextnotes JSONB,
    
    -- Timestamps
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_verificationencounters_beliefid ON verificationencounters(beliefid);
CREATE INDEX idx_verificationencounters_sessionid ON verificationencounters(sessionid);
CREATE INDEX idx_verificationencounters_triggeroccurredat ON verificationencounters(triggeroccurredat);
```

---

## Service Architecture

### Service Layer Components

| Service | Responsibility | Key Methods |
|---------|---------------|-------------|
| **EpisodicDecayService** | Manages time-based decay of episodic captures | `get_decay_candidates()`, `preview_decay()`, `apply_decay()` |
| **TurningPointService** | Detects and preserves high-significance memories | `detect_turning_point()`, `mark_as_turning_point()` |
| **SemanticArchiveService** | Manages confidence-based semantic belief archival | `get_archive_candidates()`, `update_confidence()` |
| **PatternDetectionService** | Identifies recurring maladaptive patterns | `detect_pattern()`, `create_pattern()`, `update_recurrence()` |
| **VerificationService** | Tracks belief activation and success rates | `create_verification()`, `resolve_verification()` |
| **ActionExecutor** | Orchestrates MoSAEIC intervention flow | `execute_intervention()`, `phase_transition()` |

---

### Decay Rates by Window (EpisodicDecayService)

Based on neuroscience principles of memory consolidation:

| Window | Decay Rate | Half-Life | Rationale |
|--------|-----------|-----------|-----------|
| **Senses** | 0.5 | ~7 days | Concrete sensory details decay fastest; consolidated to gist |
| **Actions** | 0.6 | ~10 days | Behavioral details decay moderately; action gist persists |
| **Emotions** | 0.7 | ~14 days | Emotional tone persists longer; amygdala consolidation |
| **Impulses** | 0.65 | ~12 days | Action tendencies decay similarly to emotions |
| **Cognitions** | 0.3 | ~30 days | Thoughts/beliefs persist longest; consolidate to semantic memory |

**Implementation Note**: `Cognitions` window has slowest decay because it contains the semantic belief content that transitions to long-term memory via systems consolidation.

---

## REST API Endpoints

**Base Route**: `/api/mosaeic/*`

### Phase 2: Capture Endpoints

#### `POST /api/mosaeic/captures`
Create a new 5-window episodic capture.

**Request**:
```json
{
  "sessionid": "uuid",
  "senses": {
    "interoceptive": "string",
    "exteroceptive": "string",
    "bodyState": "string"
  },
  "actions": {
    "executed": "string",
    "motorOutput": "string"
  },
  "emotions": {
    "primary": "string",
    "secondary": ["string"],
    "valence": "positive|negative|neutral",
    "arousal": "high|medium|low"
  },
  "impulses": {
    "urges": "string",
    "avoidance": "string",
    "approach": "string"
  },
  "cognitions": {
    "automaticThoughts": "string",
    "interpretations": "string",
    "predictions": "string",
    "coreBelief": "string"
  },
  "context": {},
  "emotionalintensity": 7.5
}
```

**Response**: `201 Created` with capture object

---

#### `GET /api/mosaeic/captures/{captureId}`
Retrieve a specific capture.

**Response**:
```json
{
  "id": "uuid",
  "sessionid": "uuid",
  "senses": {...},
  "actions": {...},
  "emotions": {...},
  "impulses": {...},
  "cognitions": {...},
  "emotionalintensity": 7.5,
  "turningpoint": false,
  "createdat": "timestamp"
}
```

---

### Phase 1 & 3: Pattern Endpoints

#### `POST /api/mosaeic/patterns`
Create or detect a maladaptive pattern.

**Request**:
```json
{
  "beliefcontent": "I am incompetent",
  "domain": "self",
  "captureid": "uuid",
  "triggercontext": {}
}
```

**Response**: Pattern object with recurrence count

---

#### `GET /api/mosaeic/patterns?domain={domain}&status={status}`
List detected patterns filtered by domain/status.

---

### Phase 4: Rewrite Endpoints

#### `POST /api/mosaeic/rewrites`
Create a belief rewrite.

**Request**:
```json
{
  "oldbeliefid": "uuid",
  "newbelief": "I am learning and growing; competence comes with practice",
  "domain": "self",
  "adaptivenessscore": 0.7
}
```

---

### Phase 5: Verification Endpoints

#### `POST /api/mosaeic/verifications`
Create a verification encounter.

**Request**:
```json
{
  "beliefid": "uuid",
  "sessionid": "uuid",
  "predictioncontent": "I will feel competent after practicing",
  "observedoutcome": "Felt more confident after practice session",
  "predictioncorrect": true,
  "beliefactivated": "new"
}
```

---

#### `GET /api/mosaeic/rewrites/{beliefId}/verification-history`
Get verification history for a belief (success rate calculation).

**Response**:
```json
{
  "beliefid": "uuid",
  "totalencounters": 5,
  "successcount": 4,
  "failurecount": 1,
  "successrate": 0.8,
  "newbeliefactivationrate": 0.8
}
```

---

## Integration Points

### Dependencies (from spec)

| System | Integration Point | Purpose |
|--------|------------------|---------|
| **Mental Models (005)** | Belief representation schema | Shared belief structure between systems |
| **Memory Consolidation (007)** | Reconsolidation window tracking | Protein-synthesis window enforcement |
| **Heartbeat/Active Inference** | Pattern monitoring | Real-time detection of maladaptive activation |
| **Neo4j (Long-term Memory)** | Graph storage via n8n | Belief networks and trigger contexts |
| **PostgreSQL (Working Memory)** | Relational storage | Episodic captures, intervention state |

---

## Data Flow Example: Complete Intervention

```
1. USER ACTION
   ↓ (exhibits maladaptive pattern 3rd time)

2. PATTERN DETECTION SERVICE
   - Queries: SELECT * FROM fivewindowcaptures WHERE cognitions->>'coreBelief' LIKE '%incompetent%'
   - Detects recurrence >= 3
   - INSERT INTO maladaptivepatterns
   ↓

3. INTERVENTION ORCHESTRATOR (Phase 1: Interrupt)
   - Checks user readiness
   - Initiates intervention
   ↓

4. ACTION EXECUTOR (Phase 2: 5-Window Capture)
   - Prompts user for: Senses, Actions, Emotions, Impulses, Cognitions
   - INSERT INTO fivewindowcaptures (all 5 windows)
   ↓

5. PATTERN DETECTION SERVICE (Phase 3: Prediction Error)
   - Extracts core belief from cognitions window
   - Compares to observed outcome (from senses/actions)
   - Calculates prediction error magnitude
   - Opens reconsolidation window (timestamp)
   ↓

6. ACTION EXECUTOR (Phase 4: Rewrite)
   - Presents old belief
   - Collects alternative interpretations
   - Evaluates adaptiveness
   - INSERT INTO beliefrewrites
   ↓

7. VERIFICATION SERVICE (Phase 5: Verification)
   - On future trigger encounters:
   - INSERT INTO verificationencounters
   - Updates beliefid success/failure counts
   - Calculates success rate
   ↓

8. META-LEARNING LAYER
   - If success rate >= 70%: Mark pattern resolved
   - If success rate < 70%: Queue follow-up intervention
```

---

## Current State vs. Target State

### ⚠️ Critical Discrepancy

| Aspect | Current Codebase (INCORRECT) | Target State (CORRECT) |
|--------|------------------------------|------------------------|
| **Table columns** | `mental`, `observation`, `senses`, `actions`, `emotions` | `senses`, `actions`, `emotions`, `impulses`, `cognitions` |
| **Window count** | 5 fields but wrong names | 5 fields with correct MoSAEIC names |
| **Belief source** | Unclear (mental? cognitions?) | Explicitly `cognitions` window |
| **Decay logic** | References non-existent windows | Decay rates for correct 5 windows |
| **Migration status** | Not migrated | Requires migration 013 |

**Action Required**: Execute `MoSAEIC-Implementation-Correction-Guide.md` migration plan before using this addendum as implementation reference.

---

## Notes for Future Developers

1. **Always extract core beliefs from the `cognitions` window** - This is where thoughts, interpretations, and predictions live.

2. **Context vs. Windows** - The `context` field stores environmental/trigger context, NOT content from the 5 windows.

3. **Turning Points** - High emotional intensity (>8.5) should auto-flag captures as potential turning points.

4. **Decay vs. Archive** - Episodic captures decay over time; semantic beliefs archive based on low confidence (<40%).

5. **Reconsolidation Window** - Default 4 hours; enforce via `windowexpiresat` timestamp in `predictionerror` table (not shown in this schema - may need to add).

6. **Success Rate Calculation** - Use `(successcount / (successcount + failurecount))` from `beliefrewrites` table, updated by `verificationencounters`.

---

## Appendix: Migration Checklist Reference

See `MoSAEIC-Implementation-Correction-Guide.md` for full migration instructions. Key milestones:

- [ ] Database migration 013 executed
- [ ] Models updated with correct 5 windows
- [ ] Services updated with correct field references
- [ ] API schemas updated with correct request/response
- [ ] Tests updated with correct fixtures
- [ ] Full integration test passing
- [ ] This addendum validated against live implementation

---

**Document Version**: 1.0 (Target State)
**Last Updated**: 2025-12-22
**Status**: DRAFT - Awaiting codebase correction
