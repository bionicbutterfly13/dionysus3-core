# Tasks: Rollback Safety Net for Agentic Changes

**Input**: spec.md, plan.md

## Phase 1: Checkpointing (P1)
- [ ] T001 Implement checkpoint creation (primary file + related files + metadata + optional DB snapshot hook)
- [ ] T002 Calculate and store checksums, sizes, retention timestamps

## Phase 2: Rollback (P1)
- [ ] T003 Implement rollback restore with status/history recording and duration capture
- [ ] T004 Add confirmation/guardrails for destructive actions

## Phase 3: Interfaces (P1)
- [ ] T005 Add FastAPI routes: create checkpoint, list, rollback, cleanup expired
- [ ] T006 Add smolagent tool/CLI wrapper to trigger checkpoint/rollback

## Phase 4: Retention & Audit (P2)
- [ ] T007 Implement retention cleanup respecting active checkpoints
- [ ] T008 Provide audit listing with outcomes and timestamps

## Phase 5: Testing (P1)
- [ ] T009 Round-trip test: checkpoint → mutate file → rollback → checksum match
- [ ] T010 Timeout test: rollback completes <30s in controlled scenario
- [ ] T011 Retention cleanup test

## Phase 6: Docs (P3)
- [ ] T012 Add usage doc snippet for API/CLI/tool
