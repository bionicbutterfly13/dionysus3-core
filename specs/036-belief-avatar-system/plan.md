# Implementation Plan: Belief Avatar System

**Branch**: `036-belief-avatar-system` | **Date**: 2025-12-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/036-belief-avatar-system/spec.md`

## Summary

Implement REST API endpoints exposing BeliefTrackingService (journey creation, belief lifecycle, experiments, replay loops, MOSAEIC, metrics) and create avatar simulation skills for interactive roleplay with Theory of Mind modeling and Shell/Core dynamics tracking for the Analytical Empath archetype.

## Technical Context

**Language/Version**: Python 3.11+ (async/await, Pydantic v2)
**Primary Dependencies**: FastAPI, smolagents, Pydantic v2, Graphiti (Neo4j access)
**Storage**: Neo4j via n8n webhooks (Graphiti for direct access as approved exception)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (VPS via Docker)
**Project Type**: Single API project with external skills-library
**Performance Goals**: <1s for metrics queries, <5s for avatar simulation
**Constraints**: HMAC verification required for webhooks, Neo4j via Graphiti only
**Scale/Scope**: Single participant journeys, course development use case

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Library-First | ✅ PASS | Router uses existing BeliefTrackingService singleton |
| CLI Interface | N/A | REST API feature, CLI not applicable |
| Test-First | ⚠️ PENDING | Tests to be written before implementation |
| Integration Testing | ⚠️ PENDING | Contract tests required for new endpoints |
| Observability | ✅ PASS | Graphiti logging already integrated in service |
| Simplicity | ✅ PASS | Exposing existing service, no new complexity |

**Pre-Design Status**: PASS (pending gates addressed during implementation)

## Project Structure

### Documentation (this feature)

```text
specs/036-belief-avatar-system/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI)
│   └── belief-journey-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
api/
├── models/
│   └── belief_journey.py     # EXISTS - Pydantic models
├── services/
│   └── belief_tracking_service.py  # EXISTS - Core service
├── routers/
│   └── belief_journey.py     # NEW - REST endpoints
└── main.py                   # Update to include router

# External (skills-library)
/Volumes/Asylum/skills-library/personal/bionicbutterfly13/consciousness/
├── avatar-simulation.md      # NEW - Avatar simulation skill
└── response-prediction.md    # NEW - Response prediction skill

tests/
├── integration/
│   └── test_belief_journey_router.py  # NEW
└── unit/
    └── test_belief_tracking_service.py  # NEW
```

**Structure Decision**: Single API project following existing dionysus3-core patterns. Router added to `api/routers/`, tests in `tests/`. Avatar simulation skills stored in external skills-library per project conventions.

## Complexity Tracking

> No violations requiring justification. Feature uses existing patterns.

---

## Phase 0: Research

### Research Tasks

1. **Router Patterns**: Examine existing routers (avatar.py, ias.py) for endpoint conventions
2. **UUID Handling**: FastAPI path parameter patterns for UUID types
3. **Error Handling**: Standard HTTPException patterns in codebase
4. **Skills Format**: Structure and conventions in skills-library

### Findings

See [research.md](./research.md) for detailed findings.

---

## Phase 1: Design

### Data Model

See [data-model.md](./data-model.md) for entity relationships and validation rules.

### API Contracts

See [contracts/belief-journey-api.yaml](./contracts/belief-journey-api.yaml) for OpenAPI specification.

### Quickstart

See [quickstart.md](./quickstart.md) for development setup and usage examples.

---

## Next Steps

After plan approval:
1. Run `/speckit.tasks` to generate implementation tasks
2. Create Archon project with tasks
3. Implement following TDD cycle
