# Tasks: Context Engineering Upgrades

**Input**: Design documents from `/specs/037-context-engineering-upgrades/`
**Prerequisites**: plan.md (required), specs (required for user stories)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup & Foundational

**Purpose**: Shared infrastructure and validation helpers

- [X] T001 Create `api/utils/callbacks.py` for CallbackRegistry if needed
- [X] T002 Create `api/utils/schema_context.py` scaffolding
- [X] T003 Install `jsonschema` if not present in environment (check requirements.txt)

---

## Phase 2: User Story 1 - Reliable Heartbeat Decisions (Priority: P1)

**Goal**: Eliminate prompt drift in Heartbeat decisions using SchemaContext.

**Independent Test**: Trigger a heartbeat with a mock LLM that returns slightly malformed JSON; verify `SchemaContext` retries and recovers.

### Tests for User Story 1

- [X] T004 [P] [US1] Create unit test `tests/unit/test_schema_context.py` verifying validation retry logic and timeout handling
- [X] T005 [P] [US1] Create integration test `tests/integration/test_heartbeat_reliability.py` with mock LLM failure

### Implementation for User Story 1

- [X] T006 [P] [US1] Implement `SchemaContext` class in `api/utils/schema_context.py`
- [X] T007 [P] [US1] Define `HeartbeatDecisionSchema` in `api/models/action.py` using Pydantic `model_json_schema`
- [X] T008 [US1] Update `HeartbeatService._make_decision` in `api/services/heartbeat_service.py` to use `SchemaContext.query()`
- [X] T009 [US1] Update `HeartbeatService` retry configuration to use 5s timeout

**Checkpoint**: Heartbeat service should now be robust against JSON errors.

---

## Phase 3: User Story 2 - Neural Field Metrics (Priority: P2)

**Goal**: Monitor cognitive flow efficiency (compression/resonance).

**Independent Test**: Feed `ContextStreamService` verbose repetitive text (expect low compression) vs concise summary (expect high compression).

### Tests for User Story 2

- [ ] T010 [P] [US2] Create unit test `tests/unit/test_neural_metrics.py` for compression/resonance calculations

### Implementation for User Story 2

- [ ] T011 [P] [US2] Update `ContextStreamService` in `api/services/context_stream.py` to calculate `compression` (tokens_in/tokens_out)
- [ ] T012 [P] [US2] Update `ContextStreamService` to calculate `resonance` using `sentence-transformers`
- [ ] T013 [US2] Update `FlowState` enum in `api/models/cognitive.py` to include new metric thresholds

**Checkpoint**: `ContextStreamService` now reports rich flow metrics.

---

## Phase 4: User Story 3 - Fractal Metacognition (Priority: P2)

**Goal**: Enable recursive thought structures.

**Independent Test**: Create a parent thought containing a child thought ID; verify persistence and retrieval.

### Tests for User Story 3

- [ ] T014 [P] [US3] Create integration test `tests/integration/test_fractal_persistence.py`

### Implementation for User Story 3

- [ ] T015 [P] [US3] Update `ThoughtSeed` model in `api/models/thought.py` with `child_thought_ids` field
- [ ] T016 [US3] Update `MetacognitionAgent` prompt in `api/agents/metacognition_agent.py` to output recursive structures
- [ ] T017 [US3] Verify `AgentMemoryService` persists child IDs correctly

**Checkpoint**: Thoughts can now reference other thoughts hierarchically.

---

## Phase 5: User Story 4 - Native Callback Registry (Priority: P3)

**Goal**: Standardize agent hook registration.

**Independent Test**: Register a dummy callback; verify it fires on agent step.

### Tests for User Story 4

- [ ] T018 [P] [US4] Verify audit logs continue to populate in `tests/integration/test_audit.py` (or manual check)

### Implementation for User Story 4

- [ ] T019 [P] [US4] Refactor `ConsciousnessManager` in `api/agents/consciousness_manager.py` to use `CallbackRegistry.register`
- [ ] T020 [US4] Update `MoSAEIC` capture hooks to match `(step, **kwargs)` signature if needed

**Checkpoint**: Agent internals are cleaner and more stable.

---

## Phase 6: Polish & Verification

- [ ] T021 Run full Heartbeat integration test suite
- [ ] T022 Verify observability metrics in `dionysus_mcp`

---

## Dependencies & Execution Order

1. **Setup (Phase 1)**: Can start immediately.
2. **US1 (SchemaContext)**: Critical path for reliability.
3. **US2 & US3**: Can run in parallel after Setup.
4. **US4 (Callbacks)**: Independent refactor, can happen anytime (recommended early to keep logs stable).

## Implementation Strategy

1. **Setup**: Get the helpers in place.
2. **Reliability First**: Implement US1 to stop heartbeat crashes.
3. **Intelligence/Efficiency**: Implement US2/US3 in parallel.
4. **Stability**: Refactor US4.