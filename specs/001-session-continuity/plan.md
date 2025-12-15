# Implementation Plan: Session Continuity

**Branch**: `001-session-continuity` | **Date**: 2025-12-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-session-continuity/spec.md`

## Summary

Implement session continuity by creating Journey and JourneyDocument entities that track conversations and artifacts across time. Integrates with existing IAS session storage (currently in-memory) and moves to PostgreSQL persistence via the SessionManager service. Exposes journey operations through MCP tools for AGI self-reference.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, asyncpg, pydantic
**Storage**: PostgreSQL with pgvector (existing dionysus3-core database)
**Testing**: pytest with asyncio support
**Target Platform**: Linux server (via Docker)
**Project Type**: API + MCP server (web application pattern)
**Performance Goals**: <50ms journey creation, <200ms timeline query
**Constraints**: Must integrate with existing IAS session storage, preserve backward compatibility
**Scale/Scope**: 10k journeys, 100 sessions/journey

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Per `.specify/memory/constitution.md`:

- [x] **I. Data Integrity First**: Journey links use FK constraints; session operations are transactional
- [x] **II. Test-Driven Development**: Contract tests for MCP tools, integration tests for journey operations
- [x] **III. Memory Safety & Correctness**: Journey-session links maintain referential integrity; no orphan sessions
- [x] **IV. Observable Systems**: Structured logging for journey create/update, journey health stats via MCP
- [x] **V. Versioned Contracts**: New MCP tools are additive (non-breaking), documented in CHANGELOG

## Project Structure

### Documentation (this feature)

```text
specs/001-session-continuity/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
api/
├── routers/
│   └── ias.py           # Update: integrate SessionManager
├── services/
│   └── session_manager.py  # NEW: Journey operations
└── models/
    └── journey.py       # NEW: Journey, JourneyDocument pydantic models

mcp/
└── tools/
    └── journey.py       # NEW: MCP tools for journey operations

tests/
├── contract/
│   └── test_journey_mcp.py  # NEW: Contract tests for MCP tools
└── integration/
    └── test_session_continuity.py  # NEW: Integration tests
```

**Structure Decision**: Web application pattern - `api/` for FastAPI, `mcp/` for MCP server, `tests/` for all tests.

## Complexity Tracking

> No Constitution violations - all checks pass.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       | N/A        | N/A                                 |
