# Implementation Plan: Critical D3 Bug Fixes

**Branch**: `064-critical-d3-fixes` | **Date**: 2026-01-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/064-critical-d3-fixes/spec.md`

## Summary

Fix 3 critical bugs blocking D3 stability:
1. ~~Undefined variables in `action_executor.py`~~ (COMPLETED)
2. Duplicate endpoint in `monitoring.py` causing trace_id parameter loss
3. Direct Neo4j access in `ias.py` violating architectural constraint

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic v2, Graphiti
**Storage**: Neo4j (via Graphiti service only - no direct access)
**Testing**: pytest with asyncio_mode=auto
**Target Platform**: Linux server (VPS)
**Project Type**: Existing API service (modification only)
**Performance Goals**: N/A (bug fixes, no performance changes)
**Constraints**: Must maintain existing API contracts; no breaking changes
**Scale/Scope**: 3 files, ~30 lines of changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| No direct Neo4j access | VIOLATION (ias.py) | Will be fixed |
| Pydantic v2 only | PASS | No model changes needed |
| Async-first | PASS | All changes maintain async patterns |
| Test coverage | PASS | Existing tests should still pass |

## Project Structure

### Documentation (this feature)

```text
specs/064-critical-d3-fixes/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (files to modify)

```text
api/
├── services/
│   └── action_executor.py    # COMPLETED - undefined vars fixed
└── routers/
    ├── monitoring.py         # Fix: Remove duplicate endpoint
    └── ias.py                 # Fix: Replace direct Neo4j with Graphiti
```

**Structure Decision**: Modifying existing files only. No new files needed.

## Implementation Details

### Fix 1: action_executor.py (COMPLETED)

**Status**: Done
**Change**: Lines 136, 140-141 - replaced undefined `memory_record` and `s` with existing variables `recent_memories_count`, `current_energy`, `heartbeat_count`

### Fix 2: monitoring.py - Remove Duplicate Endpoint

**File**: `api/routers/monitoring.py`
**Lines**: 60-72

**Current State**:
```python
# Line 45-58: First definition (KEEP - has trace_id support)
@router.get("/cognitive", response_model=Dict)
async def get_cognitive_stats(service = Depends(get_monitoring_service_with_trace)):
    ...
    return {..., "trace_id": service.trace_id}

# Line 60-72: Second definition (DELETE - overwrites first, loses trace_id)
@router.get("/cognitive", response_model=Dict)
async def get_cognitive_stats():
    ...
```

**Action**: Delete lines 60-72 (the second duplicate definition)

**Verification**:
- OpenAPI spec shows single `/api/monitoring/cognitive` endpoint
- Endpoint responds with `trace_id` in response

### Fix 3: ias.py - Replace Direct Neo4j Access

**File**: `api/routers/ias.py`
**Lines**: 142-162

**Current State**:
```python
async def update_persistent_session(session_id: str, updates: dict):
    manager = get_session_manager()
    cypher = "MATCH (s:Session {id: $id}) SET "
    # ... builds Cypher dynamically ...
    await manager._driver.execute_query(cypher, params)
```

**Action**: Replace with Graphiti service or n8n webhook call

**Option A (Graphiti Service)**:
```python
async def update_persistent_session(session_id: str, updates: dict):
    from api.services.graphiti_service import get_graphiti_service
    graphiti = await get_graphiti_service()

    # Use Graphiti's entity update method
    await graphiti.update_entity(
        entity_type="Session",
        entity_id=session_id,
        properties=updates
    )
```

**Option B (n8n Webhook)** - Preferred for IAS (high-value business asset):
```python
async def update_persistent_session(session_id: str, updates: dict):
    import httpx
    from api.services.hmac_utils import generate_hmac_signature

    webhook_url = os.getenv("N8N_IAS_SESSION_UPDATE_URL")
    payload = {"session_id": session_id, "updates": updates}
    signature = generate_hmac_signature(payload)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            webhook_url,
            json=payload,
            headers={"X-Signature": signature}
        )
        response.raise_for_status()
```

**Decision**: Use Option A (Graphiti service) as interim solution.
- No existing n8n workflow for IAS session updates
- Graphiti complies with "no direct Neo4j" rule
- Can migrate to n8n webhook when workflow is created
- Avoids blocking fix on n8n workflow creation

**Verification**:
- `grep -r "_driver.execute_query" api/routers/` returns no matches
- Session updates still persist correctly

## Complexity Tracking

No constitution violations require justification - all changes simplify the codebase.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Existing tests fail | Low | Medium | Run full test suite before/after |
| IAS webhook not configured | Medium | High | Add env var validation, fallback to error |
| Breaking API contract | Low | High | Preserve all endpoint signatures |

## Verification Steps

1. `python -m pytest tests/ -v` - all tests pass
2. `uvicorn api.main:app --reload` - server starts without errors
3. `curl localhost:8000/docs` - OpenAPI spec shows single /cognitive endpoint
4. `grep -r "_driver.execute_query" api/routers/` - returns 0 matches
5. `grep -r "from neo4j import" api/routers/` - returns 0 matches
