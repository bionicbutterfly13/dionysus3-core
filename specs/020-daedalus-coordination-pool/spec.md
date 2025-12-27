# Feature Specification: DAEDALUS Coordination Pool (smolagents-backed)

**Feature Branch**: `020-daedalus-coordination-pool`  \
**Created**: 2025-12-27  \
**Status**: Draft  \
**Input**: Port the Dionysus 2.0 DAEDALUS distributed agent coordination (background pool, task queue, context isolation, metrics) and make it smolagents-native for Dionysus 3.

## User Scenarios & Testing

### User Story 1 - Background Worker Pool (Priority: P1)
As the system, I want a pool of background smolagents with isolated context windows, so I can run migration, recall, and research jobs concurrently without cross-talk.

**Independent Test**: Spawn N agents, assign tasks; verify queued tasks are picked up when an agent frees and each task logs agent assignment.

### User Story 2 - Task Routing & Queueing (Priority: P1)
As the system, I want tasks to be queued when no agent is free and auto-routed when capacity opens, so no work is dropped.

**Independent Test**: Fill the pool, submit an extra task, then free one agent; verify the queued task starts automatically.

### User Story 3 - Coordination Metrics & Health (Priority: P2)
As an operator, I want coordination metrics (tasks completed/failed, utilization, latency) and agent health (memory/cpu, context switches), so I can debug and scale safely.

**Independent Test**: Call `/api/v1/monitoring/metrics` and observe non-zero counts for active coordinations, tasks, and utilization; agent health shows context isolation status.

## Requirements

### Functional Requirements
- **FR-001**: Implement a coordination service that manages smolagent instances with states (`IDLE`, `ANALYZING`, `EXECUTING`, `DEGRADED`) and tracks context_window_id per agent.
- **FR-002**: Provide task assignment with queueing and preferred-agent routing; tasks transition through `PENDING` → `IN_PROGRESS` → `COMPLETED/FAILED/CANCELLED`.
- **FR-003**: Expose APIs (or smolagent tools) to initialize coordination, spawn agents, assign tasks, get status, and shut down.
- **FR-004**: Emit structured logs for assignments, queue events, health changes, and task lifecycle; include trace IDs for cross-service debugging.
- **FR-005**: Enforce context isolation between agents (no shared mutable state; separate memory/tool sessions) with optional isolation report.
- **FR-006**: Integrate with discovery/migration outputs (Spec 019) and with heartbeat/ingest jobs as a reusable worker pool.

### Success Criteria
- **SC-001**: With pool size N, at least N tasks run in parallel and additional tasks queue without loss.
- **SC-002**: Coordination metrics endpoint returns utilization and task status distribution for at least one active coordination.
- **SC-003**: Context isolation report shows no shared context ids across concurrently running agents.

