# Implementation Plan: Thoughtseeds Framework Enhancement

**Branch**: `038-thoughtseeds-framework` | **Date**: 2025-12-30 | **Spec**: [specs/038-thoughtseeds-framework/spec.md]

## Summary
Implement missing components from the Thoughtseeds paper (Kavi et al., 2025) to move Dionysus into a high-fidelity biologically-grounded cognitive model. This includes an EFE-driven decision engine for uncertainty-aware triage, nested Markov blankets for context isolation, evolutionary priors for long-term alignment, and an explicit Inner Screen for serial conscious attention.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: smolagents, litellm, pydantic, numpy, scipy, neo4j (Graphiti)  
**Storage**: Neo4j (Memory Graph)  
**Testing**: pytest  
**Target Platform**: Linux server (VPS)
**Project Type**: Single project (FastAPI cognitive engine)  
**Performance Goals**: EFE calculations < 50ms, Heartbeat OODA loop < 10s (excl. LLM)  
**Constraints**: < 1GB Memory overhead for cognitive math, strictly Neo4j-only persistence.  
**Scale/Scope**: Support for 100+ active ThoughtSeeds per cycle.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] I. Library-First: Components implemented as standalone utility classes (`EFEEngine`, `PriorHierarchy`).
- [x] II. CLI Interface: Exposed via MCP tools and Heartbeat manual trigger.
- [x] III. Test-First: Integration tests for full loop mandatory.
- [x] V. Observability: `efe_score` and `brightness` logged to EpisodicMemory.

## Project Structure

### Documentation (this feature)

```text
specs/038-thoughtseeds-framework/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan
├── research.md          # Phase 0 output (Technical decisions)
├── data-model.md        # Phase 1 output (Entity definitions)
├── quickstart.md        # Phase 1 output (Testing scenarios)
├── contracts/           # Phase 1 output (API definitions)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
api/
├── models/
│   ├── thought.py       # Augmented ThoughtSeed
│   ├── priors.py        # PriorHierarchy models
│   └── workspace.py     # InnerScreen models
├── services/
│   ├── heartbeat_service.py # Integration point
│   └── agent_memory_service.py # Persistence logic
└── utils/
    └── efe_engine.py    # Math engine
```

**Structure Decision**: Single project structure (FastAPI).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |