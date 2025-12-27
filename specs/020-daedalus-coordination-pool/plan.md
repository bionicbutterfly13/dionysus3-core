# Implementation Plan: DAEDALUS Coordination Pool (smolagents-backed)

**Branch**: `020-daedalus-coordination-pool` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)

## Summary
Rebuild the D2.0 DAEDALUS coordination service on smolagents: background agent pool with context isolation, task queueing, assignments, and metrics. Expose via API + optional tool hooks.

## Technical Context
- **Language**: Python 3.11+
- **Stack**: smolagents, FastAPI, structlog, asyncio
- **Targets**: `api/services/coordination_service.py`, `api/routers/coordination.py`, smolagent tool wrappers
- **Testing**: pytest; concurrency/queueing scenarios; contract tests for metrics

## Constitution Check
- [x] Data integrity: task state machine tracked and logged
- [x] Observable systems: metrics + structured logs
- [x] Versioned contracts: stable API responses for status/metrics

## Milestones
1) Core coordination engine: agent registry, task queue, assignment, state machine
2) Context isolation: per-agent context IDs, guardrails against shared mutable state
3) Interfaces: API endpoints + tool hooks to init coordination, spawn agents, assign tasks, fetch status
4) Metrics/logging: utilization, task distributions, health; structured logs with trace ids
5) Tests: queue/assignment behaviors; metrics surfaces

## Deliverables
- Coordination service module with agent/task models
- FastAPI router for coordination lifecycle
- Smolagent tool to submit tasks into pool
- Metrics surfacing (ties into Spec 023)
