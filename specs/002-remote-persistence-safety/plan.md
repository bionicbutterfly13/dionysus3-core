# Implementation Plan: Remote Persistence Safety Framework

**Branch**: `002-remote-persistence-safety` | **Date**: 2025-12-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-remote-persistence-safety/spec.md`

## Summary

Build a remote persistence layer using the VPS-hosted Neo4j/n8n/Ollama infrastructure to protect against LLM-caused data loss. The system syncs local memory to remote Neo4j in near-real-time, enables bootstrap recovery when local state is destroyed, and provides cross-session/cross-project memory queries. All development follows test-first TDD with integration tests against live VPS services.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing dionysus3-core)
**Primary Dependencies**: FastAPI, asyncpg, neo4j-driver, httpx (webhooks), pydantic
**Storage**: PostgreSQL (local, existing) + Neo4j 5 (remote VPS 72.61.78.89:7687)
**Testing**: pytest + pytest-asyncio, integration tests against live VPS
**Target Platform**: Linux server (local dev + remote VPS)
**Project Type**: Web application (backend API extension)
**Performance Goals**: Sync within 30 seconds, recovery <60s for 1000 memories
**Constraints**: Must degrade gracefully when VPS unreachable, no data loss on sync failure
**Scale/Scope**: Single developer, <10K memories, 5 phases of implementation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Per `.specify/memory/constitution.md`:

- [x] **I. Data Integrity First**: Feature explicitly protects against data loss; sync is additive, recovery is non-destructive; queue ensures no data lost during outages
- [x] **II. Test-Driven Development**: TDD methodology embedded in spec; 20 tasks in TEST→IMPL order; integration tests against live VPS (not mocks)
- [x] **III. Memory Safety & Correctness**: Sync operations are idempotent; conflict resolution is last-write-wins with audit log; bootstrap recovery validated before activation
- [x] **IV. Observable Systems**: FR-008 requires logging all sync operations; SyncEvent entity tracks audit trail; health check for sync status planned
- [x] **V. Versioned Contracts**: New webhook endpoints documented; n8n workflow contracts defined; no breaking changes to existing MCP tools

**Gate Status**: PASSED - All constitution principles addressed in spec

## Project Structure

### Documentation (this feature)

```text
specs/002-remote-persistence-safety/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── webhook-sync.yaml
│   ├── neo4j-schema.cypher
│   └── n8n-workflow.json
├── checklists/
│   └── requirements.md  # Spec validation (complete)
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (repository root)

```text
# Backend API extension
api/
├── routers/
│   └── sync.py              # NEW: /api/sync/* endpoints
├── services/
│   └── remote_sync.py       # NEW: RemoteSyncService
└── models/
    └── sync.py              # NEW: SyncEvent, SyncStatus models

# MCP Server extension
mcp/
├── tools/
│   └── sync.py              # NEW: sync_now, get_sync_status tools
└── server.py                # MODIFY: register sync tools

# Tests (TDD - written first)
tests/
├── contract/
│   └── test_webhook_sync.py # NEW: webhook contract tests
├── integration/
│   ├── test_neo4j_sync.py   # NEW: Neo4j integration tests
│   ├── test_n8n_workflow.py # NEW: n8n workflow tests
│   └── test_recovery.py     # NEW: bootstrap recovery tests
└── unit/
    └── test_remote_sync.py  # NEW: RemoteSyncService unit tests

# Scripts
scripts/
├── bootstrap_recovery.py    # NEW: Recovery from Neo4j
└── test_vps_connectivity.py # NEW: VPS health check

# n8n workflows (deployed to VPS)
n8n-workflows/
├── memory_sync.json         # NEW: Sync workflow
└── session_summary.json     # NEW: Summary workflow
```

**Structure Decision**: Extends existing dionysus3-core backend structure. New sync capabilities added as separate router/service. n8n workflows maintained in repo but deployed to remote VPS.

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Summary

### Research Topics

1. **Neo4j Python Driver Best Practices** - Async patterns, connection pooling for remote access
2. **n8n Webhook Integration** - Authentication, payload validation, retry handling
3. **Ollama Embedding Generation** - API format, batch processing, fallback strategy
4. **Cross-Session Identity** - How to generate/track session_id consistently
5. **LLM Destruction Detection** - Patterns to detect (rapid deletes, schema drops)

*Detailed findings in [research.md](./research.md)*

## Phase 1: Design Artifacts

### Data Model

*Detailed in [data-model.md](./data-model.md)*

- **SyncEvent**: Audit record for sync operations
- **SyncStatus**: Enum for sync state (pending, synced, failed, queued)
- **Neo4j Memory Node**: Graph representation of memory with project/session tags

### API Contracts

*Detailed in [contracts/](./contracts/)*

- `POST /api/sync/memory` - Webhook endpoint for n8n
- `POST /api/sync/trigger` - Manual sync trigger
- `GET /api/sync/status` - Sync health check
- `POST /api/recovery/bootstrap` - Trigger recovery from Neo4j

### n8n Workflows

- `memory_sync.json` - Webhook → Validate → Embed (Ollama) → Persist (Neo4j)
- `session_summary.json` - Session end trigger → Summarize → Store

## Phase 2: Task Breakdown

*Generated by `/speckit.tasks` command - See [tasks.md](./tasks.md)*
