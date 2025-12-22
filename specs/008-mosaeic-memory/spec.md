# Feature 008: MOSAEIC Dual Memory Architecture

**Status**: Planned
**Created**: 2025-12-22
**Dependencies**: 001-session-continuity, 005-mental-models, 007-memory-consolidation
**Input**: MOSAEIC Dual Memory Architecture specification based on cognitive neuroscience of episodic and semantic memory systems
**Source**: Existing implementations from Dionysus-2.0 and active-inference-core

## Overview

Implement opposing management protocols for episodic and semantic memory: **time-based decay** for episodic memories (efficiency protocol) and **confidence-based preservation** for semantic memories (accuracy protocol). This mirrors the biological dual memory system where the hippocampus handles recent autobiographical events and the neocortex stores verified knowledge.

### Problem Statement

Current architecture treats all memories uniformly. This causes:
1. **Storage bloat**: Trivial episodic memories (daily logs) accumulate indefinitely
2. **Senility risk**: Important semantic facts may decay inappropriately
3. **No emotional exemptions**: High-significance events get pruned like mundane ones
4. **Static beliefs**: Maladaptive patterns persist despite repeated prediction errors

### Value Proposition

Dual management protocols enable Dionysus to:
- **Forget efficiently**: Prune old, mundane episodic memories automatically
- **Remember accurately**: Preserve well-verified semantic knowledge indefinitely
- **Honor turning points**: Exempt emotionally significant episodes from decay
- **Learn from errors**: Update beliefs when predictions consistently fail

---

## Architecture

### The Two Wings

```
+-------------------------------------------------------------------------+
|                        MOSAEIC DUAL MEMORY                               |
+--------------------------------+----------------------------------------+
|     EPISODIC WING              |         SEMANTIC WING                   |
|     "Daily Logs"               |         "Reference Collection"          |
+--------------------------------+----------------------------------------+
| Storage: PostgreSQL            | Storage: Neo4j                          |
| Content: What/Where/When       | Content: Facts/Concepts/Models          |
| Governed by: TIME              | Governed by: CONFIDENCE                 |
| Decay: Recency-based           | Decay: Doubt-based                      |
| Exception: Turning Points      | Exception: Prediction Error Accumulation|
+--------------------------------+----------------------------------------+
```

### Storage Layer Mapping

| MOSAEIC Layer | dionysus3-core | Purpose |
|---------------|----------------|---------|
| Hippocampal buffer | PostgreSQL | Recent episodic captures, working memory |
| Neocortical store | Neo4j | Consolidated semantic knowledge |
| Systems consolidation | 007-memory-consolidation | PostgreSQL -> Neo4j migration |

---

## Existing Pattern References

### From Dionysus-2.0: CognitionPattern

```python
# Source: Dionysus-2.0/backend/src/models/cognition_base.py

class CognitionPattern(BaseModel):
    pattern_id: str
    pattern_name: str
    description: str
    pattern_type: PatternType  # STRUCTURAL, BEHAVIORAL, EMERGENT, RECURSIVE, etc.

    # Quality metrics
    success_rate: float        # Historical success rate
    confidence: float          # Pattern confidence level
    reliability_score: float   # Pattern reliability

    # Usage and learning
    usage_count: int
    last_used: datetime

    # Evolution
    parent_patterns: List[str]
    child_patterns: List[str]
    evolution_history: List[Dict[str, Any]]

    # Consciousness
    consciousness_contribution: float
    emergence_markers: List[str]
```

### From active-inference-core: BasinInfluenceType

```python
# Source: active-inference-core/src/caicore/dynamics/attractor_basin_manager.py

class BasinInfluenceType(Enum):
    REINFORCEMENT = "reinforcement"  # New thoughtseed strengthens existing basin
    COMPETITION = "competition"      # New thoughtseed competes with existing basin
    SYNTHESIS = "synthesis"          # New thoughtseed merges with existing basin
    EMERGENCE = "emergence"          # New thoughtseed creates entirely new basin
```

### From infomarket: PatternEvolutionTracker

```python
# Source: infomarket/src/consciousness/pattern_evolution.py

class PatternEvolutionTracker:
    def __init__(self):
        self.patterns: Dict[str, KnowledgePattern] = {}
        self.validation_thresholds = {
            'min_success_rate': 0.7,
            'min_projects': 2
        }

    def validate_pattern(self, pattern: KnowledgePattern) -> bool:
        return (
            pattern.generalized and
            pattern.success_rate >= self.validation_thresholds['min_success_rate'] and
            len(pattern.projects_used) >= self.validation_thresholds['min_projects']
        )

    def evolve_pattern(self, base_pattern_id: str, new_pattern_id: str) -> KnowledgePattern:
        # Create evolved pattern with slight regression initially
        pass
```

---

## Episodic Memory - Time-Based Decay

### FiveWindowCapture Entity

Episodic memory stores context-rich autobiographical snapshots across five experiential dimensions:

```python
class ExperientialDimension(str, Enum):
    MENTAL = "mental"           # Thoughts, cognitions
    OBSERVATION = "observation" # Perceptions, what was noticed
    SENSES = "senses"           # Sensory details (visual, auditory, etc.)
    ACTIONS = "actions"         # Behavioral responses, what was done
    EMOTIONS = "emotions"       # Affective states, feelings

class FiveWindowCapture(BaseModel):
    id: UUID
    session_id: UUID

    # Five experiential windows
    mental: str | None          # "I was thinking about the deadline"
    observation: str | None     # "User seemed stressed"
    senses: str | None          # "Tense voice, rapid typing"
    actions: str | None         # "Offered to help prioritize"
    emotions: str | None        # "Empathy, slight concern"

    # Temporal context
    timestamp: datetime
    context: dict[str, Any]     # Surrounding conversation state

    # Intensity and preservation
    emotional_intensity: float = Field(ge=0.0, le=10.0)
    preserve_indefinitely: bool = False  # Turning Point flag

    created_at: datetime
```

### Decay Protocol

```python
# Time-based decay rules
EPISODIC_DECAY_THRESHOLD_DAYS = 180  # 6 months default

async def apply_episodic_decay():
    cutoff = datetime.utcnow() - timedelta(days=EPISODIC_DECAY_THRESHOLD_DAYS)

    # Delete old captures UNLESS marked as Turning Point
    await db.execute("""
        DELETE FROM five_window_captures
        WHERE created_at < :cutoff
        AND preserve_indefinitely = false
    """, {"cutoff": cutoff})
```

### Differential Decay Rates

Based on cognitive research, peripheral details decay faster than central gist:

```python
class DecayRate(BaseModel):
    dimension: ExperientialDimension
    half_life_days: int

DECAY_RATES = [
    DecayRate(dimension=ExperientialDimension.SENSES, half_life_days=7),
    DecayRate(dimension=ExperientialDimension.OBSERVATION, half_life_days=14),
    DecayRate(dimension=ExperientialDimension.EMOTIONS, half_life_days=21),
    DecayRate(dimension=ExperientialDimension.ACTIONS, half_life_days=60),
    DecayRate(dimension=ExperientialDimension.MENTAL, half_life_days=90),
]
```

---

## Turning Points (Flashbulb Memory Exception)

### Detection Criteria

A memory becomes a Turning Point when:

1. **High emotional intensity**: `emotional_intensity >= 8.0`
2. **High surprise**: Unexpected prediction error (large `error_magnitude`)
3. **High consequentiality**: Linked to MaladaptivePattern with `severity_score >= 0.7`
4. **Explicit marking**: User or system flags as significant

### TurningPoint Entity

```python
class TurningPointTrigger(str, Enum):
    HIGH_EMOTION = "high_emotion"
    SURPRISE = "surprise"
    CONSEQUENCE = "consequence"
    MANUAL = "manual"

class TurningPoint(BaseModel):
    id: UUID
    capture_id: UUID  # FK to FiveWindowCapture

    # Trigger criteria
    trigger_type: TurningPointTrigger
    trigger_description: str

    # Autobiographical linking (from 005-mental-models spec)
    narrative_thread_id: UUID | None
    life_chapter_id: UUID | None

    # Metadata
    vividness_score: float  # Subjective confidence in recall
    created_at: datetime
```

### Detection Logic

```python
async def detect_turning_point(capture: FiveWindowCapture) -> bool:
    # Criterion 1: High emotional intensity
    if capture.emotional_intensity >= 8.0:
        return True

    # Criterion 2: High surprise (large prediction error)
    recent_errors = await get_recent_prediction_errors(capture.session_id)
    if any(e.error_magnitude > 0.8 for e in recent_errors):
        return True

    # Criterion 3: Linked to severe maladaptive pattern
    linked_patterns = await get_linked_patterns(capture.id)
    if any(p.severity_score >= 0.7 for p in linked_patterns):
        return True

    return False
```

---

## Semantic Memory - Confidence-Based Preservation

### BeliefRewrite Entity

Semantic beliefs are indexed by confidence/adaptiveness, not age. Integrates with existing `CognitionPattern` structure:

```python
class BeliefRewrite(BaseModel):
    id: UUID

    # Belief content
    old_belief_id: UUID | None  # Link to replaced belief
    new_belief: str
    domain: ModelDomain  # user, self, world, task_specific

    # Confidence scoring (maps to CognitionPattern.confidence)
    adaptiveness_score: float = Field(ge=0.0, le=1.0)
    evidence_count: int = 0
    last_verified: datetime | None

    # Prediction tracking (maps to CognitionPattern.success_rate)
    prediction_success_count: int = 0
    prediction_failure_count: int = 0

    # Evolution tracking (maps to CognitionPattern.evolution_history)
    evolution_trigger: BasinInfluenceType | None  # REINFORCEMENT, SYNTHESIS, etc.

    created_at: datetime
    updated_at: datetime

    @property
    def accuracy(self) -> float:
        total = self.prediction_success_count + self.prediction_failure_count
        if total == 0:
            return 0.5  # Prior
        return self.prediction_success_count / total
```

### MaladaptivePattern Entity

Tracks recurring negative patterns for intervention:

```python
class PatternSeverity(str, Enum):
    LOW = "low"           # Minor inconvenience
    MODERATE = "moderate" # Noticeable impact
    HIGH = "high"         # Significant impairment
    CRITICAL = "critical" # Requires immediate intervention

class MaladaptivePattern(BaseModel):
    id: UUID

    # Pattern identification
    belief_content: str
    domain: ModelDomain

    # Severity metrics
    severity_score: float = Field(ge=0.0, le=1.0)
    severity_level: PatternSeverity
    recurrence_count: int = 0

    # Intervention status
    intervention_triggered: bool = False
    last_intervention: datetime | None

    # Links
    linked_capture_ids: list[UUID] = []
    linked_model_ids: list[UUID] = []

    created_at: datetime
    updated_at: datetime
```

### Confidence Protocol

```python
# Confidence-based preservation rules
CONFIDENCE_ARCHIVE_THRESHOLD = 0.3  # Below this, consider archiving
ACCESS_STALE_THRESHOLD_DAYS = 365   # 1 year without access

async def apply_semantic_pruning():
    # Archive (not delete) low-confidence, unaccessed beliefs
    cutoff = datetime.utcnow() - timedelta(days=ACCESS_STALE_THRESHOLD_DAYS)

    await db.execute("""
        UPDATE belief_rewrites
        SET archived = true
        WHERE adaptiveness_score < :threshold
        AND last_verified < :cutoff
        AND archived = false
    """, {"threshold": CONFIDENCE_ARCHIVE_THRESHOLD, "cutoff": cutoff})

    # NEVER delete high-confidence beliefs
    # They are "printed in indelible ink"
```

### Prediction Error Updating

Uses `PatternEvolutionTracker` validation thresholds:

```python
REVISION_ERROR_THRESHOLD = 0.5  # 50% accuracy triggers revision (from PatternEvolutionTracker)

async def update_belief_confidence(belief_id: UUID, prediction_correct: bool):
    belief = await get_belief(belief_id)

    if prediction_correct:
        belief.prediction_success_count += 1
    else:
        belief.prediction_failure_count += 1

    # Recalculate adaptiveness
    belief.adaptiveness_score = belief.accuracy
    belief.last_verified = datetime.utcnow()

    await save_belief(belief)

    # Flag for revision if accuracy dropped below threshold
    if belief.accuracy < REVISION_ERROR_THRESHOLD:
        await flag_for_revision(belief_id)
```

---

## Basin Reorganization Dynamics

When new beliefs or patterns emerge, basins reorganize according to `BasinInfluenceType`:

```python
class BasinReorganizationService:
    """Manages attractor basin dynamics during belief updates"""

    async def integrate_new_belief(
        self,
        belief: BeliefRewrite,
        context_basins: list[UUID]
    ) -> BasinInfluenceType:
        """Determine how new belief affects existing basins"""

        similarities = await self.calculate_similarities(belief, context_basins)

        max_similarity = max(similarities.values()) if similarities else 0.0

        # High similarity -> reinforcement or synthesis
        if max_similarity > 0.8:
            target_basin = max(similarities, key=similarities.get)
            basin_strength = await self.get_basin_strength(target_basin)

            if basin_strength > 1.5:
                return BasinInfluenceType.REINFORCEMENT
            else:
                return BasinInfluenceType.SYNTHESIS

        # Medium similarity -> competition or synthesis
        elif max_similarity > 0.5:
            return BasinInfluenceType.COMPETITION

        # Low similarity -> emergence (new basin)
        else:
            return BasinInfluenceType.EMERGENCE
```

---

## VerificationEncounter Entity

Logs when beliefs are tested against reality (MOSAEIC Phase 5):

```python
class VerificationEncounter(BaseModel):
    id: UUID

    # What was tested
    belief_id: UUID
    prediction_id: UUID

    # Outcome
    prediction_content: dict[str, Any]
    observation: dict[str, Any]
    belief_activated: str  # "old" or "new"
    prediction_error: float

    # Context
    session_id: UUID
    timestamp: datetime

    created_at: datetime
```

---

## Schema-Mediated Integration

### Episodic -> Semantic (Schema Extraction)

During consolidation (007), repeated episodic patterns become semantic beliefs:

```python
async def extract_schema_from_episodes(session_ids: list[UUID]) -> BeliefRewrite | None:
    """
    When multiple similar episodic captures occur, extract the semantic pattern.
    Example: 3 rejection episodes -> "I am often rejected" belief
    """
    captures = await get_captures_for_sessions(session_ids)

    # Cluster by similarity
    clusters = await cluster_captures(captures)

    for cluster in clusters:
        if len(cluster) >= 3:  # Pattern threshold from PatternEvolutionTracker
            # Extract semantic belief
            belief_content = await llm_summarize_pattern(cluster)

            return BeliefRewrite(
                new_belief=belief_content,
                domain=infer_domain(cluster),
                adaptiveness_score=0.5,  # Initial neutral confidence
                evidence_count=len(cluster),
                evolution_trigger=BasinInfluenceType.EMERGENCE
            )

    return None
```

### Semantic -> Episodic (Verification)

Updated semantic beliefs are tested during new episodic encounters:

```python
async def verify_belief_in_session(belief_id: UUID, session_id: UUID):
    """
    During MOSAEIC Phase 5 (Verification), test if updated beliefs
    activate correctly in new episodic contexts.
    """
    belief = await get_belief(belief_id)

    # Generate prediction from belief
    prediction = await generate_prediction_from_belief(belief, session_id)

    # Log verification encounter
    await create_verification_encounter(
        belief_id=belief_id,
        prediction_id=prediction.id,
        session_id=session_id
    )
```

---

## Heartbeat Integration

### OBSERVE Phase
- Generate `FiveWindowCapture` from current context
- Detect potential Turning Points
- Load relevant semantic beliefs for prediction

### ORIENT Phase
- Resolve predictions against observations
- Update belief confidence scores
- Log `VerificationEncounter` records

### DECIDE Phase
- Check if any beliefs need revision (`accuracy < 50%`)
- Add `REVISE_BELIEF` action if needed
- Schedule episodic decay job if threshold reached

### ACT Phase
- Execute `REVISE_BELIEF` with belief update handler
- Execute `PRUNE_EPISODIC` with decay service
- Execute `ARCHIVE_SEMANTIC` for low-confidence beliefs

### New Actions

```python
class ReviseBeliefAction(Action):
    type: str = "REVISE_BELIEF"
    cost: int = 3
    belief_id: UUID
    trigger: BasinInfluenceType  # REINFORCEMENT, COMPETITION, SYNTHESIS, EMERGENCE

class PruneEpisodicAction(Action):
    type: str = "PRUNE_EPISODIC"
    cost: int = 2
    threshold_days: int = 180

class ArchiveSemanticAction(Action):
    type: str = "ARCHIVE_SEMANTIC"
    cost: int = 1
    confidence_threshold: float = 0.3
```

---

## Configuration

```python
# api/config/mosaeic.py

# Episodic decay
EPISODIC_DECAY_THRESHOLD_DAYS = 180  # 6 months
EMOTIONAL_INTENSITY_TURNING_POINT = 8.0  # Out of 10

# Semantic preservation
CONFIDENCE_ARCHIVE_THRESHOLD = 0.3
ACCESS_STALE_THRESHOLD_DAYS = 365
REVISION_ERROR_THRESHOLD = 0.5  # From PatternEvolutionTracker

# Pattern detection
PATTERN_RECURRENCE_THRESHOLD = 3  # Min episodes to extract schema
SEVERITY_INTERVENTION_THRESHOLD = 0.7

# Verification
VERIFICATION_WINDOW_HOURS = 24
MAX_PENDING_VERIFICATIONS = 10

# Basin dynamics
BASIN_REINFORCEMENT_THRESHOLD = 0.8
BASIN_COMPETITION_THRESHOLD = 0.5
```

---

## User Stories

### US1: Episodic Decay (P1)
As the system, I automatically prune old episodic memories after 6 months, freeing storage while preserving recent context.

### US2: Turning Point Preservation (P1)
As the system, I detect and preserve emotionally significant memories indefinitely, regardless of age.

### US3: Confidence-Based Semantic Retention (P1)
As the system, I preserve high-confidence beliefs indefinitely and archive low-confidence, unverified beliefs after 1 year.

### US4: Prediction Error Learning (P2)
As the system, when a belief's predictions consistently fail (>50% error), I flag it for revision.

### US5: Pattern Detection (P2)
As the system, I detect recurring maladaptive patterns across episodic memories and create intervention opportunities.

### US6: Verification Encounters (P2)
As the system, I track when updated beliefs are tested against new experiences and log outcomes.

### US7: Basin Reorganization (P3)
As the system, I reorganize attractor basins when new beliefs emerge, using REINFORCEMENT, COMPETITION, SYNTHESIS, or EMERGENCE dynamics.

---

## Files to Create

```
api/models/
  mosaeic.py              # FiveWindowCapture, TurningPoint, BeliefRewrite,
                          # MaladaptivePattern, VerificationEncounter

api/services/
  episodic_decay_service.py    # Time-based decay logic
  semantic_archive_service.py  # Confidence-based archival
  turning_point_service.py     # Detection and preservation
  pattern_detection_service.py # MaladaptivePattern tracking
  verification_service.py      # Belief testing logic
  basin_reorganization.py      # Basin dynamics (from active-inference-core)

api/routers/
  mosaeic.py              # REST endpoints for MOSAEIC operations

tests/
  unit/
    test_episodic_decay.py
    test_turning_points.py
    test_semantic_archive.py
    test_pattern_detection.py
    test_verification.py
    test_basin_reorganization.py
  integration/
    test_mosaeic_flow.py
```

---

## Database Schema

### PostgreSQL Tables

```sql
-- Five-window episodic captures
CREATE TABLE five_window_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),

    mental TEXT,
    observation TEXT,
    senses TEXT,
    actions TEXT,
    emotions TEXT,

    emotional_intensity FLOAT CHECK (emotional_intensity >= 0 AND emotional_intensity <= 10),
    preserve_indefinitely BOOLEAN DEFAULT false,
    context JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_captures_decay ON five_window_captures (created_at, preserve_indefinitely);

-- Turning points
CREATE TABLE turning_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    capture_id UUID NOT NULL REFERENCES five_window_captures(id) ON DELETE CASCADE,

    trigger_type VARCHAR(50) NOT NULL,
    trigger_description TEXT,

    narrative_thread_id UUID,
    life_chapter_id UUID,
    vividness_score FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Belief rewrites
CREATE TABLE belief_rewrites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    old_belief_id UUID REFERENCES belief_rewrites(id),

    new_belief TEXT NOT NULL,
    domain VARCHAR(50) NOT NULL,

    adaptiveness_score FLOAT DEFAULT 0.5,
    evidence_count INT DEFAULT 0,
    last_verified TIMESTAMPTZ,

    prediction_success_count INT DEFAULT 0,
    prediction_failure_count INT DEFAULT 0,

    evolution_trigger VARCHAR(50),  -- REINFORCEMENT, COMPETITION, SYNTHESIS, EMERGENCE

    archived BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_beliefs_archive ON belief_rewrites (archived, adaptiveness_score, last_verified);

-- Maladaptive patterns
CREATE TABLE maladaptive_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    belief_content TEXT NOT NULL,
    domain VARCHAR(50) NOT NULL,

    severity_score FLOAT DEFAULT 0.0,
    severity_level VARCHAR(20) DEFAULT 'low',
    recurrence_count INT DEFAULT 0,

    intervention_triggered BOOLEAN DEFAULT false,
    last_intervention TIMESTAMPTZ,

    linked_capture_ids UUID[] DEFAULT '{}',
    linked_model_ids UUID[] DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Verification encounters
CREATE TABLE verification_encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    belief_id UUID NOT NULL REFERENCES belief_rewrites(id),
    prediction_id UUID NOT NULL,

    prediction_content JSONB NOT NULL,
    observation JSONB,
    belief_activated VARCHAR(10),
    prediction_error FLOAT,

    session_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Episodic storage growth | < 10% per month after decay |
| Turning point detection accuracy | > 90% |
| Semantic belief retention (high-confidence) | 100% |
| Belief revision trigger accuracy | > 80% |
| Pattern detection precision | > 75% |

---

## Phases

### Phase 1: Data Models
- Create `mosaeic.py` with all Pydantic models
- Create database migration for new tables

### Phase 2: Episodic Decay
- Implement `episodic_decay_service.py`
- Add decay trigger to consolidation service
- Unit tests

### Phase 3: Turning Points
- Implement `turning_point_service.py`
- Detection criteria logic
- Integration with capture creation

### Phase 4: Semantic Archive
- Implement `semantic_archive_service.py`
- Confidence scoring logic
- Archive (not delete) flow

### Phase 5: Pattern Detection
- Implement `pattern_detection_service.py`
- Recurrence tracking
- Severity scoring

### Phase 6: Basin Reorganization
- Port `BasinInfluenceType` logic from active-inference-core
- Implement `basin_reorganization.py`
- Integration with belief updates

### Phase 7: Verification
- Implement `verification_service.py`
- Integration with heartbeat ORIENT phase
- Encounter logging

### Phase 8: Heartbeat Integration
- Add new action types
- DECIDE phase triggers
- ACT phase handlers

### Phase 9: Testing
- Unit tests for all services
- Integration test for full MOSAEIC flow
- Performance benchmarks
