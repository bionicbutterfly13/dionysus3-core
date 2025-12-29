# Tasks: MOSAEIC Protocol (S.A.E.I.C Windows)

**Input**: spec.md
**Status**: Completed and Verified

## Phase 1: Foundation (P1)
- [x] T001 Implement `MOSAEICWindow` and `MOSAEICCapture` Pydantic models in `api/models/mosaeic.py` (FR-001)
- [x] T002 Implement `MOSAEICService.extract_capture` using LLM for five-window extraction in `api/services/mosaeic_service.py` (FR-002)
- [x] T003 Implement `MOSAEICService.persist_capture` using Graphiti for Neo4j persistence in `api/services/mosaeic_service.py` (FR-003)

## Phase 2: Interfaces (P1)
- [x] T004 Create `mosaeic_capture` smolagent tool in `api/agents/tools/mosaeic_tools.py` (FR-002)
- [x] T005 Register `mosaeic_capture` in MCP server `dionysus_mcp/server.py` (FR-003)
- [x] T006 Implement `POST /api/mosaeic/capture` endpoint in `api/routers/mosaeic.py`

## Phase 3: Integration (P1)
- [x] T007 Integrate MOSAEIC requirement into `PerceptionAgent` description in `api/agents/perception_agent.py` (FR-004)

## Phase 4: Testing & Verification (P1)
- [x] T008 Unit tests for extraction and persistence in `tests/unit/test_mosaeic_service.py`
- [x] T009 Contract tests for API endpoint in `tests/contract/test_mosaeic_api.py`
- [x] T010 Integration test for full flow in `tests/integration/test_mosaeic_flow.py`

## Phase 5: Documentation (P3)
- [x] T011 Update `GEMINI.md` with feature completion status
