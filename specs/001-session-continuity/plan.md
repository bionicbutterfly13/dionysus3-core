# Implementation Plan: Session Continuity

**Branch**: `001-session-continuity` | **Date**: 2025-12-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-session-continuity/spec.md`

## Summary

Implement journey tracking system that links multiple conversation sessions into a coherent timeline per device. Users and Dionysus can query past conversations ("What did we discuss?"), and documents can be linked to journeys. Storage is local PostgreSQL with optional Neo4j sync via 002.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing dionysus3-core)
**Primary Dependencies**: FastAPI, asyncpg, pydantic (matches 002-remote-persistence-safety)
**Storage**: PostgreSQL (local, via DATABASE_URL)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux server / macOS development
**Project Type**: API backend (extends existing FastAPI app)
**Performance Goals**: <50ms journey creation (SC-001), <200ms timeline query (SC-002)
**Constraints**: Referential integrity enforced, zero data loss on session linking
**Scale/Scope**: 100+ sessions per journey, multiple concurrent sessions allowed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Per `.specify/memory/constitution.md`:

- [x] **I. Data Integrity First**: Referential integrity via FK constraints; cascade delete for orphan cleanup
- [x] **II. Test-Driven Development**: Contract tests for MCP tools, integration tests for journey operations
- [x] **III. Memory Safety & Correctness**: Sessions linked to exactly one journey; concurrent sessions allowed; delete cascades documented
- [x] **IV. Observable Systems**: Structured logging for journey CRUD operations; query latency metrics
- [x] **V. Versioned Contracts**: MCP tools follow existing patterns; new tools are additive (non-breaking)
- [x] **VI. Formal Specification Workflow**: Following speckit workflow (clarify → plan → tasks → implement)

## Project Structure

### Documentation (this feature)

```text
specs/001-session-continuity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
api/
├── models/
│   └── journey.py       # Journey, Session, JourneyDocument models
├── services/
│   └── journey_service.py  # Journey business logic
├── routers/
│   └── journey.py       # REST endpoints for journey operations
└── migrations/
    └── 002_journey_tables.sql  # PostgreSQL schema

mcp/
└── tools/
    └── journey.py       # MCP tools: get_journey, query_journey_history, add_document

tests/
├── contract/
│   └── test_journey_mcp.py  # MCP tool contract tests
├── integration/
│   └── test_journey_service.py  # Journey service integration tests
└── unit/
    └── test_journey_models.py  # Model unit tests
```

**Structure Decision**: Extends existing api/ structure from 002. MCP tools in mcp/tools/ for AGI self-reference (FR-006).

## Complexity Tracking

> No Constitution violations. Standard patterns used.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | - | - |

## Edge Case: Database Unavailability

*Deferred from clarification phase*

**Decision**: On database unavailability during journey retrieval:
- Return cached journey data if available (future enhancement)
- For MVP: Return error with retry guidance
- Log failure for observability

## Phase Dependencies

| Phase | Depends On | Output |
|-------|------------|--------|
| Phase 0: Research | Spec complete | research.md |
| Phase 1: Design | Phase 0 | data-model.md, contracts/, quickstart.md |
| Phase 2: Tasks | Phase 1 | tasks.md (via /speckit.tasks) |
| Phase 3: Implement | Phase 2 | Source code |
