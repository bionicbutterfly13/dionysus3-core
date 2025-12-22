# Tasks: MOSAEIC Dual Memory Architecture

## Phase 1: Data Models

### T001: Create MOSAEIC Pydantic models
**Priority**: P1
**Estimate**: 2h
**Dependencies**: None

Create `api/models/mosaeic.py` with:
- ExperientialDimension enum
- TurningPointTrigger enum
- PatternSeverity enum
- BasinInfluenceType enum (port from active-inference-core)
- FiveWindowCapture model
- TurningPoint model
- BeliefRewrite model
- MaladaptivePattern model
- VerificationEncounter model
- Request/Response schemas

### T002: Create database migration
**Priority**: P1
**Estimate**: 1h
**Dependencies**: T001

Create Alembic migration for:
- five_window_captures table
- turning_points table
- belief_rewrites table
- maladaptive_patterns table
- verification_encounters table
- Required indexes

---

## Phase 2: Episodic Decay

### T003: Implement EpisodicDecayService
**Priority**: P1
**Estimate**: 2h
**Dependencies**: T002

Create `api/services/episodic_decay_service.py`:
- `apply_decay()` - Delete old captures respecting preserve_indefinitely
- `get_decay_candidates()` - Query captures older than threshold
- `calculate_dimension_decay()` - Differential decay by dimension
- Configuration for thresholds

### T004: Add decay to consolidation service
**Priority**: P1
**Estimate**: 1h
**Dependencies**: T003, 007-memory-consolidation

Integrate decay into consolidation cycle:
- Add `should_decay()` check
- Call `apply_decay()` during consolidation
- Log decay metrics

### T005: Unit tests for episodic decay
**Priority**: P1
**Estimate**: 1.5h
**Dependencies**: T003

Create `tests/unit/test_episodic_decay.py`:
- Test decay threshold logic
- Test preserve_indefinitely exemption
- Test differential decay rates
- Test edge cases

---

## Phase 3: Turning Points

### T006: Implement TurningPointService
**Priority**: P1
**Estimate**: 2h
**Dependencies**: T002

Create `api/services/turning_point_service.py`:
- `detect_turning_point()` - Apply detection criteria
- `mark_as_turning_point()` - Set preserve_indefinitely flag
- `link_to_narrative()` - Connect to autobiographical layer
- `get_turning_points()` - Query with filters

### T007: Integrate with capture creation
**Priority**: P1
**Estimate**: 1h
**Dependencies**: T006

Add turning point detection to capture flow:
- Check criteria after each FiveWindowCapture
- Automatically mark when detected
- Link to recent prediction errors

### T008: Unit tests for turning points
**Priority**: P1
**Estimate**: 1.5h
**Dependencies**: T006

Create `tests/unit/test_turning_points.py`:
- Test HIGH_EMOTION trigger
- Test SURPRISE trigger
- Test CONSEQUENCE trigger
- Test MANUAL trigger

---

## Phase 4: Semantic Archive

### T009: Implement SemanticArchiveService
**Priority**: P1
**Estimate**: 2h
**Dependencies**: T002

Create `api/services/semantic_archive_service.py`:
- `apply_archival()` - Archive low-confidence beliefs
- `get_archive_candidates()` - Query beliefs below threshold
- `restore_from_archive()` - Unarchive if accessed
- Never delete high-confidence beliefs

### T010: Implement confidence scoring
**Priority**: P1
**Estimate**: 1.5h
**Dependencies**: T009

Add confidence update logic:
- `update_confidence()` - Adjust on prediction result
- `calculate_accuracy()` - Success/failure ratio
- `flag_for_revision()` - Trigger when accuracy < 50%

### T011: Unit tests for semantic archive
**Priority**: P1
**Estimate**: 1.5h
**Dependencies**: T009, T010

Create `tests/unit/test_semantic_archive.py`:
- Test archival threshold logic
- Test confidence calculation
- Test high-confidence preservation
- Test revision flagging

---

## Phase 5: Pattern Detection

### T012: Implement PatternDetectionService
**Priority**: P2
**Estimate**: 2.5h
**Dependencies**: T002

Create `api/services/pattern_detection_service.py`:
- `detect_pattern()` - Identify recurring themes
- `update_recurrence()` - Increment count on detection
- `assess_severity()` - Calculate severity score
- `trigger_intervention()` - Flag for intervention

### T013: Port PatternEvolutionTracker
**Priority**: P2
**Estimate**: 1h
**Dependencies**: None

Port from infomarket to dionysus3-core:
- Copy pattern_evolution.py logic
- Adapt to dionysus3 conventions
- Add validation thresholds

### T014: Unit tests for pattern detection
**Priority**: P2
**Estimate**: 1.5h
**Dependencies**: T012

Create `tests/unit/test_pattern_detection.py`:
- Test pattern detection
- Test recurrence counting
- Test severity assessment
- Test intervention triggering

---

## Phase 6: Basin Reorganization

### T015: Port BasinInfluenceType logic
**Priority**: P2
**Estimate**: 2h
**Dependencies**: T001

Port from active-inference-core:
- Copy attractor_basin_manager.py concepts
- Implement `calculate_influence()` method
- Implement `apply_reorganization()` method

### T016: Implement BasinReorganizationService
**Priority**: P2
**Estimate**: 2.5h
**Dependencies**: T015

Create `api/services/basin_reorganization.py`:
- `integrate_new_belief()` - Determine influence type
- `apply_reinforcement()` - Strengthen existing basin
- `apply_competition()` - Manage competing basins
- `apply_synthesis()` - Merge basins
- `apply_emergence()` - Create new basin

### T017: Unit tests for basin reorganization
**Priority**: P2
**Estimate**: 1.5h
**Dependencies**: T016

Create `tests/unit/test_basin_reorganization.py`:
- Test REINFORCEMENT dynamics
- Test COMPETITION dynamics
- Test SYNTHESIS dynamics
- Test EMERGENCE dynamics

---

## Phase 7: Verification

### T018: Implement VerificationService
**Priority**: P2
**Estimate**: 2h
**Dependencies**: T002

Create `api/services/verification_service.py`:
- `create_verification()` - Log encounter
- `resolve_verification()` - Record outcome
- `get_pending_verifications()` - Query unresolved
- `expire_stale_verifications()` - Handle TTL

### T019: Integrate with heartbeat ORIENT
**Priority**: P2
**Estimate**: 1.5h
**Dependencies**: T018, 004-heartbeat-system

Add verification to ORIENT phase:
- Check for pending predictions
- Resolve against observations
- Update belief confidence

### T020: Unit tests for verification
**Priority**: P2
**Estimate**: 1.5h
**Dependencies**: T018

Create `tests/unit/test_verification.py`:
- Test encounter creation
- Test resolution logic
- Test TTL expiration

---

## Phase 8: Heartbeat Integration

### T021: Add MOSAEIC actions to taxonomy
**Priority**: P2
**Estimate**: 1.5h
**Dependencies**: 004-heartbeat-system

Add to action taxonomy:
- `ReviseBeliefAction` (cost: 3)
- `PruneEpisodicAction` (cost: 2)
- `ArchiveSemanticAction` (cost: 1)

### T022: Implement action handlers
**Priority**: P2
**Estimate**: 2h
**Dependencies**: T021

Create handlers for:
- `ReviseBeliefHandler` - Apply belief revision
- `PruneEpisodicHandler` - Execute decay
- `ArchiveSemanticHandler` - Execute archival

### T023: Add DECIDE phase triggers
**Priority**: P2
**Estimate**: 1.5h
**Dependencies**: T021, T022

Add to DECIDE phase:
- Check if should_decay()
- Check if should_archive()
- Check if should_revise()

---

## Phase 9: Testing

### T024: Integration test for MOSAEIC flow
**Priority**: P1
**Estimate**: 3h
**Dependencies**: All previous

Create `tests/integration/test_mosaeic_flow.py`:
- Full episodic capture -> decay flow
- Turning point detection flow
- Belief creation -> verification -> revision flow
- Pattern detection -> intervention flow

### T025: Create REST endpoints
**Priority**: P2
**Estimate**: 2h
**Dependencies**: T001-T022

Create `api/routers/mosaeic.py`:
- GET/POST /captures
- GET/POST /turning-points
- GET/POST /beliefs
- GET/POST /patterns
- GET/POST /verifications

### T026: Performance benchmarks
**Priority**: P3
**Estimate**: 2h
**Dependencies**: T024

Benchmark:
- Decay performance at scale
- Verification throughput
- Pattern detection latency

---

## Summary

| Phase | Tasks | Priority | Total Estimate |
|-------|-------|----------|----------------|
| 1: Data Models | T001-T002 | P1 | 3h |
| 2: Episodic Decay | T003-T005 | P1 | 4.5h |
| 3: Turning Points | T006-T008 | P1 | 4.5h |
| 4: Semantic Archive | T009-T011 | P1 | 5h |
| 5: Pattern Detection | T012-T014 | P2 | 5h |
| 6: Basin Reorganization | T015-T017 | P2 | 6h |
| 7: Verification | T018-T020 | P2 | 5h |
| 8: Heartbeat Integration | T021-T023 | P2 | 5h |
| 9: Testing | T024-T026 | P1-P3 | 7h |
| **Total** | **26 tasks** | | **45h** |
