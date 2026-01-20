# Plan: Track 068 - Memory Architecture Integrity Audit

**Status**: In Progress

## Phase 1: Observation & Integrity Audit

- [~] **Task 1.1**: Audit Nemori → MemEvolve → Graphiti flow for single-entry routing and schema integrity.
  - Review `api/services/nemori_river_flow.py`, `api/services/memevolve_adapter.py`, `api/services/graphiti_service.py`.
  - Verify Graphiti is the sole Neo4j connector and MemEvolve is the gateway.
  - Identify any direct Graphiti usage that bypasses MemEvolve for critical flows.

- [ ] **Task 1.2**: Observe other agent progress on memory architecture work.
  - Review worktree changes, recent commits, and track plan updates.
  - Summarize any in-flight modifications affecting Nemori/Graphiti/MemEvolve.

- [ ] **Task 1.3**: Report integrity risks and correctness assessment.
  - List confirmed correct usage, deviations, and risk areas.

## Phase 2: Single-Entry Formalization Plan

- [ ] **Task 2.1**: Define a single entrypoint interface for memory architecture access.
- [ ] **Task 2.2**: Propose enforcement steps (deprecations, lint rules, tests).
- [ ] **Task 2.3**: Draft migration plan to route all access through the entrypoint.
