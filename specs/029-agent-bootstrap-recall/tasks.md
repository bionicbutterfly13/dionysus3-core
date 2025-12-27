# Tasks: Agent Bootstrap Recall

**Input**: Design documents from `/specs/029-agent-bootstrap-recall/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/bootstrap-api.yaml

**Organization**: Tasks are ordered by implementation sequence: Foundation → Design → Implementation → Polish.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel
- **[Story]**: Maps to spec User Story (US1, US2)

---

## Phase 1: Setup & Foundation

**Purpose**: Initialize data models and core service shell.

- [X] T001 Create Pydantic models `BootstrapConfig` and `BootstrapResult` in `api/models/bootstrap.py`
- [X] T002 Initialize `BootstrapRecallService` shell in `api/services/bootstrap_recall_service.py`
- [X] T003 [P] Verify `BootstrapRecallService` logging strategy uses `_log` helper patterns for trace observability

---

## Phase 2: Core Implementation (Test-First)

**Purpose**: Implement retrieval and summarization logic with unit test coverage.

- [X] T004 Write unit tests for `BootstrapRecallService.retrieve_context` (mocking Neo4j webhook and Graphiti services) in `tests/unit/test_bootstrap_recall.py`
- [X] T005 Implement `_fetch_semantic_memories` using `VectorSearchService` (webhook-backed Neo4j recall) in `api/services/bootstrap_recall_service.py`
- [X] T006 Implement `_fetch_temporal_trajectories` using `GraphitiService` (Neo4j temporal graph) in `api/services/bootstrap_recall_service.py`
- [X] T007 Implement Markdown formatting logic for the "## Past Context" block
- [X] T008 [US1] Write unit tests for LLM-based context summarization (mocking `api.services.claude.chat_completion`)
- [X] T009 [US1] Implement `_summarize_if_needed` using `api.services.claude.HAIKU` for token-aware condensation
- [X] T010 [US1] Implement primary `recall_context(query, project_id, config)` method with 2s timeout and error handling
- [X] T010a [US1] Unit test for bootstrap timeout and graceful fallback (mocking slow memory response) in `tests/unit/test_bootstrap_recall.py`

---

## Phase 3: Integration (ConsciousnessManager)

**Purpose**: Inject the recall logic into the agentic OODA loop.

- [X] T011 Update `ConsciousnessManager.__init__` to instantiate `BootstrapRecallService`
- [X] T012 [US1] Update `ConsciousnessManager.run_ooda_cycle` to call bootstrap recall and inject result into `initial_context`
- [X] T013 [US2] Ensure `project_id` is correctly passed through the OODA cycle for scoped retrieval
- [X] T014 Create integration test `test_bootstrap_ooda_flow` in `tests/integration/test_bootstrap_flow.py` verifying context injection

---

## Phase 4: API & Tooling (Optional/Polish)

**Purpose**: Expose configuration and validate against quickstart.

- [X] T015 [P] Add `bootstrap_recall` boolean toggle to `SubmitTaskRequest` in `api/routers/coordination.py`
- [X] T016 Verify `quickstart.md` scenarios manually against the running VPS container
- [X] T017 Final pass: Ensure no breakages in `PerceptionAgent` or `ReasoningAgent` logic due to injected context
