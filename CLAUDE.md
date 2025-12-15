# dionysus3-core Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-13

## Active Technologies
- Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, neo4j-driver, httpx (webhooks), pydantic (002-remote-persistence-safety)
- PostgreSQL (local, existing) + Neo4j 5 (remote VPS 72.61.78.89:7687) (002-remote-persistence-safety)
- Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, pydantic (matches 002-remote-persistence-safety) (001-session-continuity)
- PostgreSQL (local, via DATABASE_URL) (001-session-continuity)

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
- 001-session-continuity: Added Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, pydantic (matches 002-remote-persistence-safety)
- 002-remote-persistence-safety: Added Python 3.11+ (matches existing dionysus3-core) + FastAPI, asyncpg, neo4j-driver, httpx (webhooks), pydantic

- 001-session-continuity: Added Python 3.11+ + FastAPI, asyncpg, pydantic

<!-- MANUAL ADDITIONS START -->

## Git Workflow

- **Commit frequently**: Commit after each logical unit of work
- **Push after feature completion**: Always `git push origin main` after completing a feature
- **Keep remote in sync**: Never leave commits unpushed at end of session
- **Commit message format**: Use conventional commits (feat:, fix:, refactor:, docs:, test:)

## Architecture Constraints

- **Neo4j access**: All Neo4j operations MUST go through n8n webhooks. No direct Neo4j connections from the application. This prevents LLM data destruction.
- **n8n webhook endpoints**:
  - `/webhook/memory/v1/ingest/message` - memory creation
  - `/webhook/memory/v1/recall` - memory queries/recovery
  - `/webhook/memory/v1/entity/upsert` - entity creation
  - `/webhook/memory/v1/entity/revise` - entity updates
  - `/webhook/memory/v1/journey/upsert` - journey tracking
  - `/webhook/memory/v1/journey/resolve` - journey resolution

<!-- MANUAL ADDITIONS END -->
