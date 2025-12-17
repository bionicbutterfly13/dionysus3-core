# dionysus3-core Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-13

## Active Technologies
- Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, neo4j-driver, httpx (webhooks), pydantic (002-remote-persistence-safety)
- PostgreSQL (local, existing) + Neo4j 5 (remote VPS 72.61.78.89:7687) (002-remote-persistence-safety)
- Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, pydantic (matches 002-remote-persistence-safety) (001-session-continuity)
- PostgreSQL (local, via DATABASE_URL) (001-session-continuity)
- Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, pydantic, anthropic (for LLM prediction generation) (005-mental-models)
- PostgreSQL (local, existing schema) - adds 3 tables + 1 ALTER (005-mental-models)

- Python 3.11+ + FastAPI, asyncpg, pydantic (001-session-continuity)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 005-mental-models: Added Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, pydantic, anthropic (for LLM prediction generation)
- 001-session-continuity: Added Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, pydantic (matches 002-remote-persistence-safety)
- 002-remote-persistence-safety: Added Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, neo4j-driver, httpx (webhooks), pydantic


<!-- MANUAL ADDITIONS START -->

## Engineering Practices

This project follows practices prescribed by Context-Engineering:
- Reference: `/Volumes/Asylum/repos/Context-Engineering`
- **SpecKit**: Use `/speckit.*` commands for specification-driven development
- **Serena MCP**: Semantic code analysis (preferred over Explore agent)
- **Archon MCP**: Task management (no TodoWrite)
- **Neo4j access**: Only via n8n webhooks (never direct)

## Feature: Mental Models (005-mental-models)

Mental Models are structured combinations of memory basins (attractor basins) that generate
predictions about user behavior, self-state, world state, or tasks. Based on Yufik's
neuronal packet theory.

### Key Concepts

- **ModelDomain**: `user`, `self`, `world`, `task_specific`
- **ModelStatus**: `draft` → `active` → `deprecated`
- **Predictions**: Generated from templates or domain defaults, tracked with confidence scores
- **Revisions**: Models auto-flagged for revision when prediction accuracy drops below 50%

### REST API Endpoints (`/api/models`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/models/` | Create mental model |
| GET | `/api/models/` | List models (filter by domain, status) |
| GET | `/api/models/{id}` | Get model details |
| PUT | `/api/models/{id}` | Update model |
| DELETE | `/api/models/{id}` | Deprecate model (soft-delete) |
| GET | `/api/models/{id}/predictions` | Get model predictions |
| POST | `/api/models/{id}/revisions` | Create model revision |
| GET | `/api/models/{id}/revisions` | Get revision history |

### MCP Tools

- `create_mental_model` - Create model from constituent basins
- `get_mental_model` - Get model by ID
- `list_mental_models` - List/filter models
- `generate_prediction` - Generate prediction from model + context
- `resolve_prediction` - Resolve prediction with observation
- `flag_for_revision` - Flag model for revision
- `apply_revision` - Apply basin changes to model

### Heartbeat Integration

- **OBSERVE**: Generates predictions from relevant active models
- **ORIENT**: Resolves predictions against observations
- **DECIDE**: Flags models for revision if accuracy < 50%, adds REVISE_MODEL action
- **ACT**: Executes REVISE_MODEL with ReviseModelHandler (cost: 3 energy)

### Configuration

```python
MAX_MODELS_PER_CONTEXT = 5      # Max models per prediction context
PREDICTION_TTL_HOURS = 24       # TTL for unresolved predictions
REVISION_ERROR_THRESHOLD = 0.5  # Accuracy threshold for revision flagging
```

### Service Methods

```python
from api.services.model_service import get_model_service

service = get_model_service()

# CRUD
model = await service.create_model(request)
model = await service.get_model(model_id)
models = await service.list_models(domain=ModelDomain.USER, status=ModelStatus.ACTIVE)
model = await service.update_model(model_id, request)
model = await service.deprecate_model(model_id)

# Predictions
relevant = await service.get_relevant_models(context)
prediction = await service.generate_prediction(model, context)
prediction = await service.resolve_prediction(prediction_id, observation)
unresolved = await service.get_unresolved_predictions(model_id)
stale = await service.get_stale_predictions(ttl_hours=24)
count = await service.expire_stale_predictions()

# Revisions
revision = await service.flag_for_revision(model_id, trigger, description)
revision = await service.apply_revision(model_id, request)
needing_revision = await service.get_models_needing_revision()

# Health
is_healthy, missing = await service.check_model_health(model_id)
degraded = await service.get_degraded_models()
deprecated_ids = await service.deprecate_degraded_models()
```

## Git Workflow

- **Commit frequently**: Commit after each logical unit of work
- **Push after feature completion**: Always `git push origin main` after completing a feature
- **Keep remote in sync**: Never leave commits unpushed at end of session
- **Commit message format**: Use conventional commits (feat:, fix:, refactor:, docs:, test:)

## Architecture Constraints

### Data Architecture
- **Neo4j = Source of Truth**: Neo4j is the authoritative store for all memory and graph data
- **PostgreSQL = Working Memory**: PostgreSQL handles only transactional/working data (predictions, sync queue, session state) - minimal footprint
- **NEVER contact Neo4j directly**: All Neo4j reads/writes MUST go through n8n webhooks. No direct Cypher, no neo4j-driver connections from the application. This is non-negotiable.
- **Context Engineering**: Follow Context Engineering best practices in `/Volumes/Asylum/repos/Context-Engineering` for all prompts, tool contracts, and context assembly.

### Why n8n-only Neo4j access?
1. **Safety**: Prevents LLM-driven data destruction
2. **Central control**: All graph mutations auditable in one place
3. **Consistency**: Single point of schema enforcement
4. **Recovery**: n8n workflows can implement retry/rollback logic

### Files that violate this constraint (need removal):
- Any file importing `neo4j` driver directly (not allowed)

### n8n webhook endpoints:
  - `/webhook/memory/v1/ingest/message` - memory creation
  - `/webhook/memory/v1/recall` - memory queries/recovery
  - `/webhook/memory/v1/traverse` - vetted graph traversal queries
  - `/webhook/memory/v1/entity/upsert` - entity creation
  - `/webhook/memory/v1/entity/revise` - entity updates
  - `/webhook/memory/v1/journey/upsert` - journey tracking
  - `/webhook/memory/v1/journey/resolve` - journey resolution
  - `/webhook/neo4j/v1/cypher` - cypher execution (must be gated/validated in n8n)

<!-- MANUAL ADDITIONS END -->
