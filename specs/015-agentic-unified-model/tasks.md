# Tasks: Agentic Unified Model

**Input**: Design documents from `/specs/015-agentic-unified-model/`
**Prerequisites**: plan.md (required), spec.md (required)

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 [P] Ensure `smolagents` and `graphiti-core` are installed in the environment
- [x] T002 Configure Graphiti service to use separate group_id for aspect history

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 [P] Implement `UnifiedAspectService` in `api/services/aspect_service.py`
- [x] T004 Implement human review queue storage in `api/services/aspect_service.py`
- [x] T005 [P] Create `MarketingAgent` base in `api/agents/marketing_agent.py`
- [x] T006 [P] Create `KnowledgeAgent` base in `api/agents/knowledge_agent.py`

---

## Phase 3: User Story 1 - Unified Agentic Orchestration (Priority: P1) 🎯 MVP

**Goal**: Marketing and KB pillars driven by specialized smolagents.

- [x] T007 [US1] Refactor `MarketingAgent` to generate nurture emails using `CodeAgent`
- [x] T008 [US1] Refactor `MarketingAgent` to generate sales page copy using `CodeAgent`
- [x] T009 [US1] Refactor `KnowledgeAgent` to review manuscripts using `CodeAgent`
- [x] T010 [US1] Implement structured avatar data extraction in `KnowledgeAgent`

---

## Phase 4: User Story 2 - Temporal Aspect Integrity (Priority: P1)

**Goal**: Single source of truth for boardroom aspects with Graphiti history.

- [x] T011 [US2] Implement `upsert_aspect` with Graphiti episode recording in `api/services/aspect_service.py`
- [x] T012 [US2] Implement `remove_aspect` with removal episode recording in `api/services/aspect_service.py`
- [x] T013 [US2] Update `HeartbeatAgent` to use `AspectService` for context construction

---

## Phase 5: User Story 3 - Human-in-the-Loop Review (Priority: P2)

**Goal**: Flag low-confidence outputs for human review.

- [x] T014 [US3] Implement `add_to_human_review` in `api/services/aspect_service.py`
- [x] T015 [US3] Update all agents to catch parsing errors and divert to review queue
- [x] T016 [US3] Create `GET /api/maintenance/review-queue` in `api/routers/maintenance.py`
- [x] T017 [US3] Implement `reinject_reviewed_item` logic for Marketing and KB agent resume patterns

---

## Phase 6: Polish

- [x] T017 Update `GEMINI.md` status to reflect unified agentic architecture
- [x] T018 Run final consistency check across all 3 project pillars
