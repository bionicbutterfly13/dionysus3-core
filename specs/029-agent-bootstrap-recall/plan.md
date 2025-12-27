# Implementation Plan: Agent Bootstrap Recall

**Branch**: `029-agent-bootstrap-recall` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/029-agent-bootstrap-recall/spec.md`

## Summary

Implement an automated "Bootstrap Recall" mechanism in the `ConsciousnessManager` that intercepts every agent session start. The mechanism will perform a project-scoped hybrid search against Neo4j (using webhook-backed `VectorSearchService` for semantic relevance and `GraphitiService` for temporal trajectories), summarize findings using Claude HAIKU if they exceed token limits, and inject the result into the `initial_context` as a "## Past Context" block.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, smolagents, api.services.claude (Anthropic), Graphiti-core  
**Storage**: Neo4j-only (handled via webhooks and Graphiti)  
**Testing**: pytest  
**Target Platform**: Linux VPS (Docker container)  
**Project Type**: Single API Service  
**Performance Goals**: <2s bootstrap overhead (with 2s hard timeout)  
**Constraints**: 2000 token limit for injected context, mandatory project-scoping  
**Scale/Scope**: Applied to all `ConsciousnessManager.run_ooda_cycle` calls  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Data Integrity First**: All memory is project-scoped to prevent context bleed.
- [x] **II. Test-Driven Development**: Unit tests for retrieval and summarization will be written before integration.
- [x] **III. Memory Safety & Correctness**: Uses Neo4j vector index and temporal graph for grounded recall.
- [x] **IV. Observable Systems**: Structured logging for recall latency, token usage, and hits/misses including trace IDs.
- [x] **V. Versioned Contracts**: Injected context follows a standard Markdown format.

## Project Structure

### Documentation (this feature)

```text
specs/029-agent-bootstrap-recall/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── bootstrap-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
api/
├── services/
│   └── bootstrap_recall_service.py  # NEW
├── agents/
│   └── consciousness_manager.py     # ENHANCE
└── models/
    └── bootstrap.py                 # NEW

tests/
├── unit/
│   └── test_bootstrap_recall.py     # NEW
├── integration/
│   └── test_bootstrap_flow.py       # NEW
└── contract/
    └── test_memory_contract.py      # NEW
```

**Structure Decision**: Single project structure using standard `api/` layout. Enhance `ConsciousnessManager` to call the new `BootstrapRecallService`.

## Complexity Tracking

No Constitution violations detected. All retrieval is Neo4j-only as mandated.