# Implementation Plan: Local PostgreSQL Cleanup & VPS Consolidation

**Branch**: `008-local-db-cleanup` | **Date**: 2025-12-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-local-db-cleanup/spec.md`

## Summary

Remove local PostgreSQL infrastructure from dionysus3-core and consolidate to VPS (72.61.78.89:5432) as single source of truth. This involves: (1) auditing/migrating local data, (2) removing obsolete Docker/script files, (3) updating code to require DATABASE_URL without localhost fallbacks, (4) preserving ephemeral test database, and (5) documenting VPS deployment workflow.

## Technical Context

**Language/Version**: Python 3.11+ (existing codebase)
**Primary Dependencies**: asyncpg, FastAPI (existing - no new dependencies)
**Storage**: PostgreSQL on VPS (72.61.78.89:5432) - single source of truth
**Testing**: pytest with docker-compose.test.yml (ephemeral DB on port 5434)
**Target Platform**: Linux server (VPS), macOS (development via SSH tunnel)
**Project Type**: Single project (API backend)
**Performance Goals**: N/A - infrastructure cleanup, no performance changes
**Constraints**: Must not affect Archon MCP, must preserve test infrastructure
**Scale/Scope**: File deletions + code modifications across ~10 files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Per `.specify/memory/constitution.md`:

- [x] **I. Data Integrity First**: Feature explicitly includes data audit and migration before any destructive operations. Backup created before removal.
- [x] **II. Test-Driven Development**: Test infrastructure (docker-compose.test.yml) explicitly preserved. Existing tests will run against VPS via SSH tunnel.
- [x] **III. Memory Safety & Correctness**: No memory operations affected - this is infrastructure cleanup only.
- [x] **IV. Observable Systems**: DATABASE_URL requirement will make connection failures explicit rather than silent fallbacks.
- [x] **V. Versioned Contracts**: No MCP tool changes - infrastructure only.

## Project Structure

### Documentation (this feature)

```text
specs/008-local-db-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output (execution guide)
├── checklists/
│   └── requirements.md  # Validation checklist
└── tasks.md             # Phase 2 output
```

### Source Code Changes

```text
# Files to REMOVE
docker-compose.local.yml     # Local PostgreSQL container
db-manage.sh                 # Local DB management script
wait-for-db.sh               # Local DB wait script
test.py                      # Old agi_memory test file

# Files to MODIFY
api/services/session_manager.py    # Remove localhost fallback
api/services/db.py                 # Require DATABASE_URL
dionysus_mcp/server.py             # Remove localhost fallback
tests/conftest.py                  # Use env var only
tests/integration/test_session_continuity.py  # Use env var only
.env.example                       # Update with VPS instructions
CLAUDE.md                          # Remove local DB references

# Files to PRESERVE
docker-compose.test.yml      # Ephemeral test DB on port 5434
```

**Structure Decision**: This is an infrastructure cleanup feature, not new source code. Changes are file deletions and targeted edits to existing files.

## Complexity Tracking

No constitution violations requiring justification.

## Phases

### Phase 1: Data Audit & Migration

1. Start local PostgreSQL (if not running)
2. Audit tables and row counts
3. Export data if useful content exists
4. Import to VPS with verification
5. Document migration results

### Phase 2: Code Modifications

1. Update code to require DATABASE_URL (no fallbacks)
2. Remove localhost references from production code
3. Update tests to use environment variable
4. Update .env.example with VPS instructions
5. Update CLAUDE.md

### Phase 3: File Cleanup

1. Remove docker-compose.local.yml
2. Remove db-manage.sh
3. Remove wait-for-db.sh
4. Remove test.py

### Phase 4: Verification & Documentation

1. Verify application works with VPS via SSH tunnel
2. Verify tests pass with ephemeral test DB
3. Document VPS deployment workflow
4. Commit and push changes
