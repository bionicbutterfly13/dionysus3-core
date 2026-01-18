# Track Plan: Thoughtseeds Framework Enhancement

**Track ID**: 038-thoughtseeds-framework
**Status**: In Progress (0%)

## Phase 1: EFE-Driven Decision Engine (US1) - P1

**Goal**: Implement the mathematical core for active inference decision making.

- [ ] **Task 1.1**: Create `api/utils/efe_engine.py` with `EFEEngine` class
- [ ] **Task 1.2**: Implement `calculate_entropy` using `scipy.stats.entropy`
- [ ] **Task 1.3**: Implement `calculate_goal_divergence` (Cosine Distance)
- [ ] **Task 1.4**: Integrate `EFEEngine` into `HeartbeatService._make_decision`
- [ ] **Task 1.5**: [TDD] Write unit tests in `tests/unit/test_efe_engine.py`

## Phase 2: Evolutionary Priors (US3) - P1

**Goal**: Establish the hierarchy of identity and safety constraints.

- [ ] **Task 2.1**: Create `api/models/priors.py` with `PriorLevel` enum and `PriorHierarchy` model
- [ ] **Task 2.2**: Implement `prior_constraint_check` utility
- [ ] **Task 2.3**: Seed "Basal Priors" in Neo4j (Identity, Data Integrity)
- [ ] **Task 2.4**: Update `ConsciousnessManager` to check Priors before committing to a plan

## Phase 3: Nested Markov Blankets (US2) - P1

**Goal**: Isolate agent context and prevent information flooding.

- [ ] **Task 3.1**: Update `ThoughtSeed` model in `api/models/thought.py` with `MarkovBlanket` properties
- [ ] **Task 3.2**: Implement `blanket_isolation` logic in `AgentMemoryService`
- [ ] **Task 3.3**: Refactor `PerceptionAgent` to map inputs strictly to the "Sensory" blanket surface

## Phase 4: Inner Screen (US4) - P2

**Goal**: Provide a formal data structure for serial conscious attention.

- [ ] **Task 4.1**: Create `api/models/workspace.py` with `InnerScreen` model
- [ ] **Task 4.2**: Implement `attentional_spotlight` logic (weighting mechanism)
- [ ] **Task 4.3**: Update `ConsciousnessManager` to use `InnerScreen` as the primary reasoning state
- [ ] **Task 4.4**: [TDD] Add visualization tool for `InnerScreen` in `dionysus_mcp/server.py`

## Phase 5: Verification & Polish (US5)

**Goal**: Full integration testing and validation.

- [ ] **Task 5.1**: Run "Thoughtseeds" paper ingestion task
- [ ] **Task 5.2**: Verify "Affordances" mapping (FR-030-003)
- [ ] **Task 5.3**: Final system-wide integration test for OODA + EFE + Screen
