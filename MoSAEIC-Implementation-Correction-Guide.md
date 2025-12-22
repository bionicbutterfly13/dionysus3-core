# MoSAEIC Implementation Correction Guide

**Status**: CRITICAL - Codebase Schema Mismatch
**Date**: 2025-12-22
**Priority**: P0 - Blocks all further development until corrected

## Problem Statement

The current codebase implements an **incorrect 5-window structure** that does not match the canonical MoSAEIC specification:

### Current (INCORRECT) Implementation
```
Database table: fivewindowcaptures
- mental
- observation
- senses
- actions
- emotions
```

### Canonical Specification (CORRECT)
```
MoSAEIC = Mindful Observation of:
1. Senses (interoceptive & exteroceptive sensations, body state, environment)
2. Actions (executed behaviors, motor output, what user did)
3. Emotions (feelings, affective tone, valence)
4. Impulses (urges, behavioral drives, what user wanted to do)
5. Cognitions (thoughts, interpretations, meanings, automatic appraisals, predictions)
```

## Impact Analysis

### Affected Components

| Component | Files | Changes Required |
|-----------|-------|------------------|
| **Database Schema** | `migrations/012_mosaeic_memory.sql` | Rename/restructure `fivewindowcaptures` columns |
| **Models** | `api/models/mosaeic.py` (FiveWindowCapture) | Update all attributes and docstrings |
| **Services** | `api/services/episodicdecayservice.py`, `patterndetectionservice.py`, `semanticarchiveservice.py` | Update field references and decay logic |
| **API Routes** | `api/routers/mosaeic.py` | Update request/response schemas |
| **Tests** | `tests/integration/test_mosaeic_flow.py` | Update all test fixtures and assertions |
| **Documentation** | All docstrings and comments | Update to reference correct window names |

---

## Migration Plan

### Phase 1: Database Migration (CRITICAL - Do First)

**File**: `migrations/013_correct_mosaeic_windows.sql`

```sql
-- Step 1: Create new table with correct schema
CREATE TABLE fivewindowcaptures_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sessionid UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    senses JSONB NOT NULL,
    actions JSONB NOT NULL,
    emotions JSONB NOT NULL,
    impulses JSONB NOT NULL,
    cognitions JSONB NOT NULL,
    context JSONB,
    emotionalintensity NUMERIC(3,1) CHECK (emotionalintensity >= 0 AND emotionalintensity <= 10),
    turningpoint BOOLEAN DEFAULT FALSE,
    preserveindefinitely BOOLEAN DEFAULT FALSE,
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Migrate data (if any existing data exists)
-- WARNING: This is a lossy migration - old schema cannot map 1:1 to new schema
-- Manual review of existing captures required
INSERT INTO fivewindowcaptures_new (
    id, sessionid, senses, actions, emotions, context, 
    emotionalintensity, turningpoint, preserveindefinitely, createdat
)
SELECT 
    id, 
    sessionid,
    JSONB_BUILD_OBJECT('content', senses) as senses,
    JSONB_BUILD_OBJECT('content', actions) as actions,
    JSONB_BUILD_OBJECT('content', emotions) as emotions,
    JSONB_BUILD_OBJECT('content', observation) as context,
    emotionalintensity,
    turningpoint,
    preserveindefinitely,
    createdat
FROM fivewindowcaptures
WHERE domain LIKE 'test%' IS FALSE;
-- NOTE: This loses 'mental' field - determine if this should be part of cognitions

-- Step 3: Drop old table and rename new
DROP TABLE fivewindowcaptures CASCADE;
ALTER TABLE fivewindowcaptures_new RENAME TO fivewindowcaptures;

-- Step 4: Recreate indexes and constraints
CREATE INDEX idx_fivewindowcaptures_sessionid 
    ON fivewindowcaptures(sessionid);
CREATE INDEX idx_fivewindowcaptures_createdat 
    ON fivewindowcaptures(createdat);
CREATE INDEX idx_fivewindowcaptures_turningpoint 
    ON fivewindowcaptures(turningpoint);
```

---

### Phase 2: Update Python Models

**File**: `api/models/mosaeic.py`

Replace the `FiveWindowCapture` model:

```python
class FiveWindowCapture(BaseModel):
    """
    Capture of a moment in time across the 5 MoSAEIC dimensions.
    
    MoSAEIC = Mindful Observation of Senses, Actions, Emotions, Impulses, Cognitions
    
    Each window captures a distinct aspect of an experience.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique capture ID")
    sessionid: UUID = Field(description="Session this capture belongs to")
    
    # The 5 MoSAEIC Windows
    senses: dict = Field(
        description="Interoceptive & exteroceptive sensations, body state, environmental stimuli"
    )
    actions: dict = Field(
        description="Executed behaviors, motor output, what user actually did"
    )
    emotions: dict = Field(
        description="Feelings, affective tone, valence (safe/unsafe, good/bad)"
    )
    impulses: dict = Field(
        description="Urges, action tendencies, behavioral drives (what user wanted to do)"
    )
    cognitions: dict = Field(
        description="Thoughts, interpretations, meanings, automatic appraisals, predictions"
    )
    
    # Metadata
    context: Optional[dict] = Field(None, description="Trigger context and environmental context")
    emotionalintensity: float = Field(
        ge=0, le=10,
        description="Overall emotional intensity rating (0-10 scale)"
    )
    turningpoint: bool = Field(
        False,
        description="Whether this capture is a turning point (high emotional significance)"
    )
    preserveindefinitely: bool = Field(
        False,
        description="If True, exempt from time-based decay"
    )
    createdat: datetime = Field(default_factory=datetime.utcnow)
    updatedat: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
```

---

### Phase 3: Update Services

**File**: `api/services/episodicdecayservice.py`

Update dimension references:

```python
# OLD (INCORRECT)
DECAY_RATES = {
    "mental": 0.3,
    "observation": 0.4,
    "senses": 0.5,
    "actions": 0.6,
    "emotions": 0.7,
}

# NEW (CORRECT)
DECAY_RATES = {
    "senses": 0.5,          # Concrete sensory details decay fastest
    "actions": 0.6,         # Behavioral details decay moderately fast
    "emotions": 0.7,        # Emotions persist longer
    "impulses": 0.65,       # Urges decay similarly to emotions
    "cognitions": 0.3,      # Thoughts/beliefs persist longest (consolidate to semantic)
}
```

Update all column references from `mental`, `observation` to the 5 MoSAEIC windows:

```python
# When querying captures, use these columns:
sql = """
    SELECT id, sessionid, senses, actions, emotions, impulses, cognitions,
           emotionalintensity, turningpoint, createdat
    FROM fivewindowcaptures
    WHERE sessionid = $1 AND createdat < NOW() - INTERVAL '7 days'
"""
```

**File**: `api/services/patterndetectionservice.py`

Update pattern matching logic to extract beliefs from **cognitions** window specifically:

```python
async def createpattern(self, beliefcontent: str, domain: str, captureid: UUID):
    """
    Extract core belief from cognitions window of a capture.
    
    Note: Core belief is the semantic content from the Cognitions window
    (thoughts, interpretations, automatic appraisals, predictions).
    """
    # Pattern detection should analyze cognitions window
    capture = await self.get_capture(captureid)
    extracted_belief = extract_core_belief_from_cognitions(
        capture.cognitions
    )
    # ... rest of implementation
```

---

### Phase 4: Update API Routes

**File**: `api/routers/mosaeic.py`

Update request/response schemas:

```python
class CaptureRequest(BaseModel):
    """Request to create a 5-window capture"""
    senses: dict
    actions: dict
    emotions: dict
    impulses: dict
    cognitions: dict
    context: Optional[dict] = None
    emotionalintensity: float = Field(ge=0, le=10)
    turningpoint: Optional[bool] = False

class CaptureResponse(BaseModel):
    """Response containing created capture"""
    id: UUID
    sessionid: UUID
    senses: dict
    actions: dict
    emotions: dict
    impulses: dict
    cognitions: dict
    emotionalintensity: float
    createdat: datetime

@router.post("/captures")
async def create_capture(
    sessionid: UUID,
    request: CaptureRequest,
    db: Database = Depends(get_database)
) -> CaptureResponse:
    """Create a new 5-window MoSAEIC capture"""
    # Use correct column names in insert
    query = """
        INSERT INTO fivewindowcaptures 
        (sessionid, senses, actions, emotions, impulses, cognitions, 
         context, emotionalintensity, turningpoint)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    """
    # ... implementation
```

---

### Phase 5: Update Tests

**File**: `tests/integration/test_mosaeic_flow.py`

Update all test fixtures and assertions:

```python
# OLD (INCORRECT)
INSERT INTO fivewindowcaptures 
    (id, sessionid, mental, observation, senses, actions, emotions, context, emotionalintensity)
VALUES (...)

# NEW (CORRECT)
INSERT INTO fivewindowcaptures 
    (id, sessionid, senses, actions, emotions, impulses, cognitions, context, emotionalintensity)
VALUES (
    '...', sessionid,
    '{"content": "Test senses - hearing keyboard clicks"}',
    '{"content": "Test actions - writing integration tests"}',
    '{"content": "Test emotions - satisfaction with progress"}',
    '{"content": "Test impulses - wanting to continue coding"}',
    '{"content": "Test cognitions - this test is important"}',
    '{"type": "integration_test"}',
    7.0
)
```

---

## Checklist for Re-engineering

### Database Layer
- [ ] Create migration `013_correct_mosaeic_windows.sql`
- [ ] Test migration on dev/test database
- [ ] Verify all indexes created
- [ ] Document any data loss from migration (mental field)
- [ ] Back up production database before migration

### Application Layer
- [ ] Update `FiveWindowCapture` model with correct 5 windows
- [ ] Update all service files with correct column references
- [ ] Update decay rates in `EpisodicDecayService`
- [ ] Update pattern extraction in `PatternDetectionService` (from cognitions)
- [ ] Update semantic archiving logic

### API Layer
- [ ] Update request schemas to accept 5 windows
- [ ] Update response schemas to return 5 windows
- [ ] Update all endpoint docstrings
- [ ] Update example payloads in OpenAPI schema

### Testing
- [ ] Update all test fixtures (database inserts)
- [ ] Update all assertions checking window values
- [ ] Add validation tests for 5-window structure
- [ ] Integration tests for full MOSAEIC flow with correct windows
- [ ] Test decay calculations with correct window names

### Documentation
- [ ] Update all docstrings
- [ ] Update API documentation
- [ ] Update architecture diagrams if any reference field names
- [ ] Create migration guide for other developers

---

## Critical Notes

1. **Data Loss Risk**: The "mental" field in the current schema has no direct equivalent in the correct schema. Determine:
   - Should "mental" content map to "cognitions"?
   - Should it be discarded?
   - Should it be archived separately?

2. **Decay Rate Changes**: The corrected windows have different semantic meanings, so decay rates should be revisited based on neuroscience principles.

3. **Turning Points**: The "observation" field was previously used for context. Now use the "context" field explicitly.

4. **Rollback Plan**: Have a rollback migration ready in case issues arise during production migration.

5. **Timeline**: This is blocking all further MoSAEIC development. Prioritize accordingly.

---

## Affected Tasks

- T008: REST endpoints for MOSAEIC (needs schema update)
- T009: Integration tests for full MOSAEIC flow (needs window updates)
- Any future MoSAEIC development (all blocked until corrected)

## Next Steps

1. Confirm the fate of the "mental" field
2. Create migration 013 and test on dev database
3. Update models, services, routes, tests in that order
4. Run full integration test suite
5. Deploy to production with careful monitoring
