# Tasks: Migration & Coordination Observability

**Input**: spec.md, plan.md

## Phase 1: Metrics Aggregation (P1)
- [x] T001 Implement pipeline metrics collector (Spec 019 outputs)
- [x] T002 Implement coordination/agent metrics collector (Spec 020)
- [x] T003 Implement rollback metrics collector (Spec 021)

## Phase 2: Performance Metrics (P2)
- [x] T004 Add throughput/latency/error/utilization computations
- [x] T005 Include agent utilization and task assignment latency

## Phase 3: Alerts (P2)
- [x] T006 Add alert generation for high memory/CPU, task failures, queue backlog, rollback failures
- [x] T007 Include timestamps and affected entities in alerts

## Phase 4: Interfaces (P1)
- [x] T008 Add FastAPI routes `/metrics`, `/performance`, `/alerts` returning JSON-serializable models

## Phase 5: Logging/Tracing (P2)
- [x] T009 Correlate responses with trace ids and structured logs

## Phase 6: Testing (P1/P2)
- [x] T010 Contract tests for response shapes and populated fields
- [x] T011 Induced alert test (e.g., simulate high memory agent)

## Phase 7: Docs (P3)
- [x] T012 Add usage doc snippet and example outputs
