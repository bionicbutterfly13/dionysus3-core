# Tasks: Neuronal Packet Mental Models

**Input**: Design documents from `/specs/030-neuronal-packet-mental-models/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cognitive-upgrade-api.yaml

**Organization**: Tasks are grouped by implementation phase and mapped to user stories (US1-US4) to enable parallel development of core engines and schema.

## Format: `[ID] [P?] [Story?] Description`
- **[P]**: Can run in parallel
- **[Story]**: Maps to spec User Story (US1, US2, US3, US4)

---

## Phase 1: Setup & Data Foundation

**Purpose**: Prepare the data models and Neo4j schema for Energy-Well stability.

- [X] T001 Create Pydantic models for `NeuronalPacket` and `EFE` results in `api/models/cognitive.py`
- [X] T002 [P] Augment `MentalModel` and `MemoryCluster` schemas with energy properties in `api/models/mental_model.py`
- [X] T003 [P] [US1] Create Neo4j migration script to add `boundary_energy`, `stability`, and `cohesion_ratio` to existing clusters in `scripts/migrate_energy_wells.py`
- [X] T004 [P] Update `Trajectory` model to support `type` (EPISODIC/STRUCTURAL) in `api/models/journey.py`

---

## Phase 2: Foundational Engines (Parallel [P])

**Purpose**: Implement the mathematical core for EFE and Metaplasticity.

- [X] T005 [P] [US2] Implement `EFEEngine` class with entropy and goal divergence calculation in `api/services/efe_engine.py`
- [X] T006 [P] [US3] Implement `MetaplasticityController` with sigmoid scaling logic in `api/services/metaplasticity_service.py`
- [X] T007 [P] [US2] Unit test for EFE vector distance formulas in `tests/unit/test_efe_engine.py`
- [X] T008 [P] [US3] Unit test for surprise-to-learning-rate mapping in `tests/unit/test_metaplasticity.py`

---

## Phase 3: User Story 1 - Energy-Well Stability (Priority: P1)

**Goal**: Stable mental models and prevention of context bleed via boundary energy.

- [X] T009 [US1] Update `ModelService` to fetch and respect `boundary_energy` when selecting active basins in `api/services/model_service.py`
- [X] T010 [X] [US1] Implement `NeuronalPacket` logic to enforce mutual constraints between grouped ThoughtSeeds in `api/services/model_service.py`
- [X] T011 [US1] [FR-030-008] Map Avatar Mental Model (Analytical Empath) to the new Energy Well properties in Neo4j (Run one-time migration script `scripts/migrate_avatar_basins.py`)
- [X] T012 [US1] Contract test for n8n-backed energy property updates in `tests/contract/test_neo4j_schema.py`

---

## Phase 4: User Story 2 & 4 - EFE Competition & Explorer Agent (Priority: P1)

**Goal**: Autonomous curiosity and context pollution prevention.

- [X] T013 [US2] Integrate `EFEEngine` into the `ThoughtSeed` network competition logic in `api/services/model_service.py`
- [X] T014 [US4] Implement `ContextExplorerTool` using the Context-Engineering `/research.agent` protocol in `api/agents/tools/cognitive_tools.py`
- [X] T015 [US4] Update `ConsciousnessManager` to use `ContextExplorerTool` for initial graph pruning in `api/agents/consciousness_manager.py`
- [X] T016 [US2] Add `cognitive_check` smolagent tool for autonomous EFE self-reflection in `api/agents/tools/cognitive_tools.py`

---

## Phase 5: User Story 3 - Metaplasticity Integration (Priority: P2)

**Goal**: Second-order adaptation controlling agent learning rates.

- [X] T017 [US3] Add OODA cycle "Surprise" monitoring to `ConsciousnessManager.run_ooda_cycle` in `api/agents/consciousness_manager.py`
- [X] T018 [US3] Wire `MetaplasticityController` to adjust `max_steps` and `learning_rate` of specialized agents in `api/agents/consciousness_manager.py`
- [X] T019 [US3] Implement typed trajectory logging for structural model revisions in `api/services/reconstruction_service.py`

---

## Phase 6: Polish & Verification

**Purpose**: System-wide validation and regression testing.

- [X] T020 [P] Implement `GET /api/v1/monitoring/cognitive` endpoint for real-time EFE/Stability tracking in `api/routers/monitoring.py`
- [X] T021 Run final integration test `tests/integration/test_cognitive_upgrade.py` verifying EFE-driven research behavior
- [X] T022 Verify `quickstart.md` scenarios on VPS and update documentation
- [X] T023 [P] Benchmark EFE calculation latency to ensure NFR-030-001 compliance (<50ms per seed)