# Tasks: Meta-Evolution Workflow

**Input**: Design documents from `/specs/016-meta-evolution-workflow/`
**Prerequisites**: plan.md (required)

## Phase 1: Setup (n8n Workflow)

- [ ] T001 Create `memevolve-evolve.json` workflow in `n8n-workflows/`
- [ ] T002 Implement trajectory performance analysis logic in the workflow

---

## Phase 2: Foundational (API)

- [ ] T003 Add `trigger_evolution` method to `MemEvolveAdapter` in `api/services/memevolve_adapter.py`
- [ ] T004 Create `POST /api/memevolve/evolve` in `api/routers/memevolve.py`

---

## Phase 3: User Story 1 - Strategy Optimization (Priority: P1) 🎯 MVP

- [ ] T005 Implement `RetrievalStrategy` node creation in the n8n workflow
- [ ] T006 Implement strategy selection logic in `VectorSearchService` to always use latest evolved strategy
