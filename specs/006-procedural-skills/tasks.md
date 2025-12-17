# Tasks: Procedural Memory as Skills

**Input**: `specs/006-procedural-skills/spec.md`, `specs/006-procedural-skills/plan.md`  
**Prerequisites**: Spec Kit workflow steps completed; sync tasks into Archon for tracking (Constitution VI).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1/US2/US3)

---

## Phase 1: Contracts (Traversal)

- [x] T001 [US1] Add `skill_graph` traversal query contract to `n8n-workflows/memory_v1_traverse.json`
- [x] T002 [US1] Add `TraverseQueryType.SKILL_GRAPH` constant in `api/routers/memory.py`
- [x] T003 [US1] Add contract test for `POST /api/memory/traverse` skill_graph payload in `tests/contract/` (mock n8n response)

## Phase 2: Schema (Neo4j)

- [x] T004 [US1] Add Neo4j schema contract for `(:Skill)` (constraints + indexes) under `specs/006-procedural-skills/contracts/`

## Phase 3: Optional follow-on (Skill learning/upsert)

- [x] T005 [US2] Add n8n workflow template for `Skill` upsert (`/webhook/memory/v1/skill/upsert`)
- [x] T006 [US2] Add n8n workflow template for skill practice updates (`/webhook/memory/v1/skill/practice`)
- [x] T006a [US2] Add optional end-to-end integration test for skill upsert/practice in `tests/integration/test_skill_pipeline.py`

## Phase 4: Docs

- [ ] T007 [US3] Update canonical schema docs to distinguish `ThoughtSeed` (ideation) vs `Skill` (procedural)

## Archon Sync Notes

When syncing to Archon, create tasks with IDs `T001..T007` and link them to the `006-procedural-skills` feature branch so runtime memory tagging can attach `task_id` during development.
