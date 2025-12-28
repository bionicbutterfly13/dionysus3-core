# Tasks: Rollback Safety Net for Agentic Changes

**Input**: spec.md, plan.md

## Phase 1: Checkpointing (P1)
- [x] T001 Implement checkpoint creation (primary file + related files + metadata + optional DB snapshot hook)
- [x] T002 Calculate and store checksums, sizes, retention timestamps

## Phase 2: Rollback (P1)
- [x] T003 Implement rollback restore with status/history recording and duration capture
- [x] T004 Add confirmation/guardrails for destructive actions

## Phase 3: Interfaces (P1)
- [x] T005 Add FastAPI routes: create checkpoint, list, rollback, cleanup expired
- [x] T006 Add smolagent tool/CLI wrapper to trigger checkpoint/rollback

## Phase 4: Retention & Audit (P2)
- [x] T007 Implement retention cleanup respecting active checkpoints
- [x] T008 Provide audit listing with outcomes and timestamps

## Phase 5: Testing (P1)
- [x] T009 Round-trip test: checkpoint → mutate file → rollback → checksum match
- [x] T010 Timeout test: rollback completes <30s in controlled scenario
- [x] T011 Retention cleanup test

## Phase 6: Docs (P3)
- [x] T012 Add usage doc snippet for API/CLI/tool
