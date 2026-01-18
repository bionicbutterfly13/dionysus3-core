# Tasks: Thoughtseeds Framework Enhancement

**Input**: Design documents from `/specs/038-thoughtseeds-framework/`
**Feature Branch**: `038-thoughtseeds-framework`

## Phase 1: EFE-Driven Decision Engine (US1) - P1

**Goal**: Implement the mathematical core for active inference decision making.

- [ ] T001 Create `api/utils/efe_engine.py` with `EFEEngine` class
- [ ] T002 Implement `calculate_entropy` using `scipy.stats.entropy`
- [ ] T003 Implement `calculate_goal_divergence` (Cosine Distance)
- [ ] T004 Integrate `EFEEngine` into `HeartbeatService._make_decision`
- [ ] T005 [P] Verify EFE calculations with unit tests in `tests/unit/test_efe_engine.py`

## Phase 2: Evolutionary Priors (US1) - P1

**Goal**: Establish the hierarchy of identity and safety constraints.

- [ ] T006 Create `api/models/priors.py` with `PriorLevel` enum and `PriorHierarchy` model
- [ ] T007 Implement `prior_constraint_check` utility
- [ ] T008 Seed "Basal Priors" in Neo4j (Identity, Data Integrity)
- [ ] T009 Update `ConsciousnessManager` to check Priors before committing to a plan

## Phase 3: Nested Markov Blankets (US1) - P1

**Goal**: Isolate agent context and prevent information flooding.

- [ ] T010 Update `ThoughtSeed` model in `api/models/thought.py` with `MarkovBlanket` properties
- [ ] T011 Implement `blanket_isolation` logic in `AgentMemoryService`
- [ ] T012 Refactor `PerceptionAgent` to map inputs strictly to the "Sensory" blanket surface

## Phase 4: Inner Screen (US1) - P2

**Goal**: Provide a formal data structure for serial conscious attention.

- [ ] T013 Create `api/models/workspace.py` with `InnerScreen` model
- [ ] T014 Implement `attentional_spotlight` logic (weighting mechanism)
- [ ] T015 Update `ConsciousnessManager` to use `InnerScreen` as the primary reasoning state
- [ ] T016 [P] Add visualization tool for `InnerScreen` in `dionysus_mcp/server.py`

## Phase 5: Verification & Polish

- [ ] T017 Run "Thoughtseeds" paper ingestion task
- [ ] T018 Verify "Affordances" mapping (FR-030-003)
- [ ] T019 Final system-wide integration test for OODA + EFE + Screen
