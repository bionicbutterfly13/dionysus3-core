# Tasks: DAEDALUS Coordination Pool (smolagents-backed)

**Input**: spec.md, plan.md

## Phase 1: Core Engine (P1)
- [x] T001 Implement agent model (state, context_window_id, health, performance stats)
- [x] T002 Implement task model/state machine (`PENDING`→`IN_PROGRESS`→`COMPLETED|FAILED|CANCELLED`)
- [x] T003 Implement coordination service with agent registry, queue, assignment, preferred-agent routing

## Phase 2: Context Isolation (P1)
- [ ] T004 Enforce per-agent context isolation (separate tool sessions/memory handles)
- [ ] T005 Add isolation report generation for agents

## Phase 3: Interfaces (P1)
- [x] T006 Add FastAPI router: init coordination, spawn agent, assign task, status, shutdown
- [x] T007 Add smolagent tool to submit tasks and poll status

## Phase 4: Metrics & Logging (P2)
- [ ] T008 Emit structured logs for assignments, queue events, health changes
- [ ] T009 Expose metrics (tasks completed/failed, utilization, latency) for Spec 023

## Phase 5: Testing (P1)
- [x] T010 Concurrency test: N agents consume M>N tasks with queue drain
- [x] T011 Preferred-agent assignment test
- [ ] T012 Metrics shape/values test after workload

## Phase 6: Docs (P3)
- [ ] T013 Usage doc snippet (API + tool)
