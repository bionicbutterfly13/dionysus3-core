# Implementation Plan: DAEDALUS Coordination Pool

**Branch**: `020-daedalus-coordination-pool` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/020-daedalus-coordination-pool/spec.md`

## Summary

Port and enhance the existing coordination service to be a fully spec-compliant DAEDALUS coordination pool with pool size limits (default 4, max 16), bounded task queue (100 max with 429 rejection), automatic retry on agent failure (3 attempts), graceful degradation for Spec 019 dependencies, and ≤500ms task assignment latency.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, smolagents, Pydantic v2
**Storage**: In-memory (Dict-based registry) - no persistence required
**Testing**: pytest with existing test infrastructure
**Target Platform**: Linux VPS (Docker container)
**Project Type**: Single API service
**Performance Goals**: ≤500ms task assignment latency under normal load
**Constraints**: Max 16 agents, max 100 queued tasks, 3 retry attempts on agent crash
**Scale/Scope**: Background worker pool for migration, recall, research jobs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Per `.specify/memory/constitution.md`:

- [x] **I. Data Integrity First**: Feature uses in-memory state only; no persistence layer. Task state transitions are atomic within service methods.
- [x] **II. Test-Driven Development**: Test plan included - contract tests for coordination router, integration tests for pool lifecycle.
- [x] **III. Memory Safety & Correctness**: Agent isolation enforced via separate context/tool/memory IDs. Isolation reports available.
- [x] **IV. Observable Systems**: Structured logging for assignments, queue events, health changes. Metrics endpoint exposes utilization.
- [x] **V. Versioned Contracts**: New API endpoints added (non-breaking). Existing `/api/coordination/*` endpoints preserved.

## Project Structure

### Documentation (this feature)

```text
specs/020-daedalus-coordination-pool/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── coordination-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
api/
├── services/
│   └── coordination_service.py  # Enhance existing
├── routers/
│   └── coordination.py          # Enhance existing
└── agents/
    └── tools/
        └── coordination_tools.py  # Enhance existing

tests/
├── unit/
│   └── test_coordination_service.py  # NEW
├── integration/
│   └── test_coordination_pool.py     # NEW
└── contract/
    └── test_coordination_api.py      # NEW
```

**Structure Decision**: Enhance existing files in `api/services/`, `api/routers/`, and `api/agents/tools/`. Add new test files.

## Complexity Tracking

No Constitution violations. Existing architecture supports all requirements.

---

## Phase 0: Research

### Research Tasks

1. **smolagents pool patterns** - How to spawn/manage multiple CodeAgent instances with isolated contexts
2. **asyncio task queue patterns** - Best practices for bounded queues with backpressure (429 rejection)
3. **Retry patterns** - Implementing bounded retry with agent failover

### Findings

See [research.md](./research.md) for detailed findings.
