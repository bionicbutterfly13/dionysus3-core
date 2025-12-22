# Research: Local PostgreSQL Cleanup & VPS Consolidation

**Date**: 2025-12-21
**Feature**: 008-local-db-cleanup

## Research Summary

This feature is infrastructure cleanup with established patterns. No external research required - all decisions are based on existing codebase knowledge and VPS deployment status.

## Decisions

### D1: Data Migration Approach

**Decision**: Manual audit → conditional export → import to VPS
**Rationale**: Local database may or may not contain useful data. Audit first to determine if migration is needed.
**Alternatives considered**:
- Automatic migration (rejected: may import garbage data)
- Skip migration entirely (rejected: risk of data loss)

### D2: Localhost Fallback Removal

**Decision**: Require DATABASE_URL environment variable with no fallback
**Rationale**: Silent fallbacks cause confusion about which database is being used. Explicit failure is better than wrong connection.
**Alternatives considered**:
- Keep fallback but log warning (rejected: still causes confusion)
- Auto-detect environment (rejected: too complex for the problem)

### D3: Test Database Strategy

**Decision**: Preserve docker-compose.test.yml with ephemeral DB on port 5434
**Rationale**: Tests need isolated database. Using VPS for tests would pollute production data and require network access.
**Alternatives considered**:
- Create test database on VPS (rejected: network dependency, data pollution risk)
- Mock all database calls (rejected: loses integration test value)

### D4: SSH Tunnel for Development

**Decision**: Use SSH tunnel (port 5432) for local development against VPS
**Rationale**: Standard pattern, works with existing DATABASE_URL format, secure.
**Alternatives considered**:
- Direct VPS connection (rejected: exposes database port)
- VPN (rejected: more complex setup)

### D5: VPS Deployment Workflow

**Decision**: Manual git pull + docker compose rebuild
**Rationale**: Simple, explicit, and sufficient for current team size. CI/CD can be added later.
**Alternatives considered**:
- GitHub Actions (rejected: adds complexity, can add later)
- rsync (rejected: bypasses version control)

## Files Identified for Modification

Based on grep search for localhost database references:

| File | Line | Current Pattern | Action |
|------|------|-----------------|--------|
| `api/services/session_manager.py` | 43 | `localhost:5432` fallback | Remove fallback |
| `api/services/db.py` | 21 | `getenv("DATABASE_URL")` | Add required check |
| `dionysus_mcp/server.py` | 31 | `localhost:5433/agi_memory` | Remove fallback |
| `tests/conftest.py` | 23 | `localhost:5432` fallback | Use env var only |
| `tests/integration/test_session_continuity.py` | 31 | `localhost:5432` fallback | Use env var only |

## No Further Research Needed

All technical decisions are straightforward infrastructure patterns with no unknowns.
