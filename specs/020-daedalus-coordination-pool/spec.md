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

**Independent Test**: Call `/api/coordination/metrics` and observe non-zero counts for active coordinations, tasks, and utilization; agent health shows context isolation status.

## Requirements

### Functional Requirements
- **FR-001**: Implement a coordination service that manages smolagent instances with states (`IDLE`, `ANALYZING`, `EXECUTING`, `DEGRADED`) and tracks context_window_id per agent.
- **FR-002**: Provide task assignment with queueing and preferred-agent routing; tasks transition through `PENDING` → `IN_PROGRESS` → `COMPLETED/FAILED/CANCELLED`. Preferred routing logic: tasks are assigned to IDLE agents who have previously completed the same `task_type` with the lowest average latency, falling back to any IDLE agent.
- **FR-003**: Expose APIs (or smolagent tools) to initialize coordination, spawn agents, assign tasks, get status, and gracefully shut down the pool (cleaning up all agents).
- **FR-004**: Emit structured logs for assignments, queue events, health changes, and task lifecycle; include trace IDs for cross-service debugging.
- **FR-005**: Enforce context isolation between agents (no shared mutable state; separate memory/tool sessions) with optional isolation report.
- **FR-006**: Integrate with discovery/migration outputs (Spec 019) and with heartbeat/ingest jobs as a reusable worker pool.

### Constraints
- **CON-001**: Default pool size is 4 agents; maximum pool size is 16 agents.

### Non-Functional Requirements
- **NFR-001**: Task assignment latency (time from submission to agent pickup) must be ≤500ms under normal load.

### Error Handling
- **EH-001**: If an agent crashes mid-task, the task is automatically retried on a different agent up to 3 times; after 3 failed attempts, the task transitions to `FAILED` status.
- **EH-002**: Task queue is capped at 100 pending tasks; new submissions beyond this limit are rejected with HTTP 429 (Too Many Requests).
- **EH-003**: If Spec 019 discovery/migration service is unavailable, the pool degrades gracefully: discovery/migration tasks remain queued while other task types (heartbeat, ingest, research) continue processing.

### Success Criteria
- **SC-001**: With pool size N (default 4, max 16), at least N tasks run in parallel and additional tasks queue without loss.
- **SC-002**: Coordination metrics endpoint returns utilization and task status distribution for at least one active coordination.
- **SC-003**: Context isolation report shows no shared context ids across concurrently running agents.

## Clarifications

### Session 2025-12-27
- Q: What is the default/maximum pool size for the DAEDALUS coordination pool? → A: Default 4, max 16 (balanced for moderate workloads)
- Q: What should happen when an agent fails/crashes while executing a task? → A: Auto-retry up to 3 times on a different agent, then fail
- Q: What is the maximum queue depth before rejecting new tasks? → A: 100 tasks max, reject with 429 after
- Q: What is the target latency for task assignment? → A: ≤500ms (background jobs, moderate latency acceptable)
- Q: How should the coordination pool behave if Spec 019 discovery/migration service is unavailable? → A: Degrade gracefully: queue discovery tasks, process others

## Implementation Notes (Progress)
- In-memory coordination engine at `api/services/coordination_service.py` with task state machine, queueing, preferred-agent routing, isolation collision detection, and avg task duration metrics.
- FastAPI router `api/routers/coordination.py`: spawn/list agents, submit/complete tasks, metrics; mounted in `api/main.py`.
- Smolagent tools: `spawn_coordination_agent`, `submit_coordination_task`, `complete_coordination_task`, `coordination_metrics`.
- Tests in `tests/test_coordination_service.py` cover queue drain, preferred assignment, isolation flags, metrics shape; quickstart doc in `docs/coordination.md`.
