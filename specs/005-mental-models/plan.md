# Implementation Plan: Mental Model Architecture

**Branch**: `005-mental-models` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-mental-models/spec.md`

## Summary

Implement a mental model layer that combines existing memory basins into structured representations capable of generating predictions, tracking accuracy, and self-revising based on prediction errors. This extends Dionysus from situational awareness (pattern matching) to situational understanding (model-based prediction).

**Technical Approach**: Add three new PostgreSQL tables (`mental_models`, `model_predictions`, `model_revisions`), integrate with the existing heartbeat OODA loop for prediction generation during OBSERVE and error checking during ORIENT, and expose models via MCP tools and REST API.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing dionysus3-core)
**Primary Dependencies**: FastAPI, asyncpg, pydantic, anthropic (for LLM prediction generation)
**Storage**: PostgreSQL (local, existing schema) - adds 3 tables + 1 ALTER
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux server (VPS) / macOS local dev
**Project Type**: Single project (backend only)
**Performance Goals**: Prediction generation <500ms per model; supports 100+ active models
**Constraints**: <200ms p95 for model retrieval; model accuracy queries real-time
**Scale/Scope**: Single user initially; ~10-50 active models typical

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Per `.specify/memory/constitution.md`:

- [x] **I. Data Integrity First**: Feature does not risk data loss or corruption
  - All operations use transactions
  - New tables have proper constraints and cascading deletes
  - No modification of existing memory data
- [x] **II. Test-Driven Development**: Test plan included for memory operations
  - Unit tests for SQL functions
  - Integration tests for heartbeat integration
  - Contract tests for MCP tools
- [x] **III. Memory Safety & Correctness**: Safety implications documented
  - Models can be deprecated, not deleted
  - Revision history preserves all changes
  - Prediction timeout prevents stale predictions
- [x] **IV. Observable Systems**: Observability hooks planned
  - Structured logging for model CRUD, predictions, revisions
  - `active_models_summary` view for health monitoring
  - `models_needing_revision` view for alerts
- [x] **V. Versioned Contracts**: Contract impact assessed (breaking vs non-breaking)
  - New MCP tools (non-breaking addition)
  - New REST endpoints (non-breaking addition)
  - ALTER to active_inference_states adds optional column (non-breaking)

## Project Structure

### Documentation (this feature)

```text
specs/005-mental-models/
├── plan.md              # This file
├── research.md          # Existing - Yufik paper analysis
├── design.md            # Existing - Technical schema & code
├── data-model.md        # Entity definitions
├── quickstart.md        # Getting started guide
├── contracts/           # API contracts
│   ├── mcp-tools.md     # MCP tool schemas
│   └── rest-api.yaml    # OpenAPI spec
└── tasks.md             # Task list (via /speckit.tasks)
```

### Source Code (repository root)

```text
api/
├── models/
│   └── mental_model.py      # Pydantic models for mental models
├── services/
│   └── model_service.py     # ModelService business logic
└── routers/
    └── models.py            # REST API endpoints

dionysus_mcp/
└── tools/
    └── models.py            # MCP tool implementations

migrations/
└── 008_create_mental_models.sql  # Schema migration

tests/
├── contract/
│   └── test_model_mcp_tools.py
├── integration/
│   ├── test_heartbeat_models.py
│   └── test_model_revision_lifecycle.py
└── unit/
    └── test_model_functions.py
```

**Structure Decision**: Uses existing single-project structure. Adds to `api/services/` for business logic, `api/routers/` for REST, `dionysus_mcp/tools/` for MCP integration. Tests follow existing contract/integration/unit split.

## Phase 0: Research Summary

Research completed in [research.md](./research.md). Key decisions:

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Theoretical Basis | Yufik's neuronal packet theory (2019, 2021) | Maps directly to existing basin architecture |
| Model Granularity | Medium - one model per domain/concept area | Balance between specificity and manageability |
| Creation Mode | Manual creation for MVP; auto-generation later | Allows bootstrapping with known-useful models |
| Model Competition | Confidence-weighted selection; multiple models can contribute | Avoids single point of failure |
| Deprecated Models | Archive (set status='deprecated'), never delete | Preserves audit trail and allows reactivation |
| Cross-User Transfer | Out of scope for MVP | Privacy and personalization concerns |

### Open Questions Resolved

1. **Model Granularity**: Medium granularity - models represent coherent domains (e.g., "user emotional patterns", "career transition dynamics") rather than single facts or entire knowledge areas.

2. **Automatic vs Manual**: MVP uses manual creation via API/MCP. Phase 2 can add heuristic-based auto-generation from basin co-activation patterns.

3. **Model Competition**: Multiple models can fire predictions for same context. Predictions are ranked by model confidence × relevance score. No winner-take-all.

4. **Forgetting**: Models are never deleted. Status transitions: draft → active → deprecated. Deprecated models excluded from prediction generation but retained for history.

5. **Transfer**: Out of scope. Each user/instance has isolated models. Shared model templates may be a future feature.

## Phase 1: Design Artifacts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Core Entities**:
- `MentalModel`: Combines basins into prediction-generating structure
- `ModelPrediction`: Individual prediction with resolution tracking
- `ModelRevision`: Change history for audit and rollback

### API Contracts

See [contracts/](./contracts/) for complete specifications.

**MCP Tools** (non-breaking additions):
- `create_model` - Create model from basins
- `list_models` - List models by domain/status
- `get_model` - Get model details
- `revise_model` - Trigger manual revision

**REST Endpoints** (non-breaking additions):
- `POST /api/models` - Create model
- `GET /api/models` - List models
- `GET /api/models/{id}` - Get model
- `PUT /api/models/{id}` - Update model
- `GET /api/models/{id}/predictions` - List predictions
- `GET /api/models/{id}/revisions` - List revisions

### Integration Points

1. **Heartbeat OBSERVE**: After base observation, retrieve relevant models and generate predictions
2. **Heartbeat ORIENT**: Check unresolved predictions against current observations, calculate errors
3. **Heartbeat DECIDE**: If high-error models detected, add REVISE_MODEL to action candidates
4. **Energy System**: REVISE_MODEL costs 3 energy; BUILD_MODEL costs 4 energy

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `memory_clusters` table | Exists | Source of constituent basins |
| `active_inference_states` table | Exists | Links predictions to inference state |
| Heartbeat system | Exists | OODA loop for integration |
| Energy service | Exists | Action cost enforcement |
| LLM integration | Exists | For prediction generation & error calculation |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM latency affects heartbeat | Medium | Medium | Async prediction generation; timeout with fallback |
| Model accuracy never improves | Low | High | Structured revision prompts; A/B test revision strategies |
| Basin deletion breaks models | Low | Medium | Mark models as "degraded" when basins missing |
| Too many predictions per context | Medium | Low | Configurable max models per context (default: 5) |

## Complexity Tracking

No Constitution violations requiring justification. All additions are incremental extensions to existing patterns.
