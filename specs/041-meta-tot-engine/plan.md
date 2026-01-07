# Implementation Plan: Meta-ToT Engine Integration

**Branch**: `041-meta-tot-engine` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/041-meta-tot-engine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a Meta-ToT reasoning engine with active inference scoring, CPA domain phases, and trace storage. Add a thresholded decision mechanism to activate Meta-ToT only for complex or uncertain tasks, and expose a callable tool for agent workflows. Provide deterministic fallbacks when LLM access is unavailable.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Pydantic, smolagents, numpy, scipy, graphiti-core, neo4j  
**Storage**: Neo4j (via existing webhook driver and Graphiti)  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Linux server (local + VPS)  
**Project Type**: single (API + MCP tooling)  
**Performance Goals**: Default Meta-ToT run within configurable time budget (target <= 5s)  
**Constraints**: No new external services; degrade gracefully without LLM credentials; avoid new heavy dependencies  
**Scale/Scope**: Per-request reasoning engine; traces retained for analysis

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Constitution template contains placeholders and no enforced principles in `.specify/memory/constitution.md`.
- No explicit gates to evaluate; proceed with standard quality expectations.

## Project Structure

### Documentation (this feature)

```text
specs/041-meta-tot-engine/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
api/
├── agents/
│   ├── tools/
│   │   └── meta_tot_tools.py
│   └── consciousness_manager.py
├── models/
│   └── meta_tot.py
├── routers/
│   └── meta_tot.py
└── services/
    ├── meta_tot_engine.py
    ├── meta_tot_decision.py
    └── meta_tot_trace_service.py

dionysus_mcp/
└── tools/
    └── meta_tot.py

tests/
└── unit/
    ├── test_meta_tot_decision.py
    └── test_meta_tot_engine.py
```

**Structure Decision**: Extend the existing `api/` service/tool pattern with Meta-ToT engine, decision, and trace storage. Add an optional MCP tool for broader agent access. Provide unit tests for deterministic decision and engine behavior.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution gates defined.
