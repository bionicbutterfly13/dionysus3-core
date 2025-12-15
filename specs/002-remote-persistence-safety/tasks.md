# Tasks: Remote Persistence Safety Framework

**Input**: Design documents from `/specs/002-remote-persistence-safety/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: This feature uses **Test-Driven Development (TDD)**. Tests are written FIRST and must FAIL before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- **API**: `api/routers/`, `api/services/`, `api/models/`
- **MCP**: `mcp/tools/`, `mcp/server.py`
- **Tests**: `tests/contract/`, `tests/integration/`, `tests/unit/`
- **Scripts**: `scripts/`
- **n8n**: `n8n-workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and VPS connectivity

- [ ] T001 Install Python dependencies: neo4j, httpx in requirements.txt
- [ ] T002 [P] Add sync environment variables to .env.example (NEO4J_URI, NEO4J_PASSWORD, MEMORY_WEBHOOK_TOKEN, OLLAMA_URL)
- [ ] T003 [P] Create directory structure: api/routers/, api/services/, api/models/, tests/contract/, tests/integration/
- [ ] T004 Create VPS connectivity test script in scripts/test_vps_connectivity.py
- [ ] T005 Initialize Neo4j schema on VPS using contracts/neo4j-schema.cypher
- [ ] T006 Import n8n workflow from contracts/n8n-workflow.json to VPS n8n instance

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundation

- [ ] T007 Integration test for Neo4j connectivity in tests/integration/test_neo4j_connection.py
- [ ] T008 [P] Contract test for HMAC signature validation in tests/contract/test_hmac_validation.py

### Implementation for Foundation

- [ ] T009 Create SyncEvent model in api/models/sync.py (from data-model.md)
- [ ] T010 [P] Create SyncStatus enum in api/models/sync.py
- [ ] T011 [P] Create SyncQueueItem model in api/models/sync.py
- [ ] T012 Add sync_status, synced_at, sync_version columns to memories table in migrations/
- [ ] T013 Create sync_events and sync_queue tables in migrations/
- [ ] T014 Implement HMAC signature validation utility in api/services/hmac_utils.py
- [ ] T015 Create Neo4j connection pool manager in api/services/neo4j_client.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Memory Survives LLM Wipeout (Priority: P1) 🎯 MVP

**Goal**: Sync local memory to remote Neo4j in near-real-time, recover when local state is destroyed

**Independent Test**:
1. Create memory entries locally
2. Verify they appear in remote Neo4j within 30 seconds
3. Destroy local database
4. Trigger recovery
5. Verify all memories restored

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Integration test for Neo4j CRUD operations in tests/integration/test_neo4j_sync.py
- [ ] T017 [P] [US1] Contract test for POST /sync/memory webhook in tests/contract/test_webhook_sync.py
- [ ] T018 [P] [US1] Integration test for n8n workflow end-to-end in tests/integration/test_n8n_workflow.py
- [ ] T019 [US1] Recovery test: destroy local → restore from Neo4j in tests/integration/test_recovery.py

### Implementation for User Story 1

- [ ] T020 [US1] Implement RemoteSyncService with queue management in api/services/remote_sync.py
- [ ] T021 [US1] Implement retry logic with exponential backoff in api/services/remote_sync.py
- [ ] T022 [P] [US1] Create POST /sync/memory webhook endpoint in api/routers/sync.py
- [ ] T023 [P] [US1] Create POST /sync/trigger endpoint in api/routers/sync.py
- [ ] T024 [P] [US1] Create GET /sync/status endpoint in api/routers/sync.py
- [ ] T025 [US1] Implement bootstrap recovery script in scripts/bootstrap_recovery.py
- [ ] T026 [US1] Create POST /recovery/bootstrap endpoint in api/routers/sync.py
- [ ] T027 [US1] Add sync hook to memory creation flow (trigger webhook on new memory)
- [ ] T028 [US1] Implement conflict resolution (last-write-wins) in api/services/remote_sync.py

**Checkpoint**: At this point, memories sync to Neo4j and can be recovered from LLM wipeout

---

## Phase 4: User Story 2 - Cross-Session Context Preservation (Priority: P2)

**Goal**: Query memories from previous coding sessions by session_id and date range

**Independent Test**:
1. Create memories in Session A
2. End Session A
3. Start new Session B
4. Query "What did we discuss about [topic] in previous session?"
5. Verify Session A memories returned with session attribution

### Tests for User Story 2

- [ ] T029 [P] [US2] Integration test for session boundary tracking in tests/integration/test_session_tracking.py
- [ ] T030 [P] [US2] Integration test for cross-session query in tests/integration/test_cross_session_query.py

### Implementation for User Story 2

- [ ] T031 [US2] Implement SessionManager with session_id generation in api/services/session_manager.py
- [ ] T032 [US2] Create .claude-session-id file management (get_or_create, end_session)
- [ ] T033 [US2] Tag memories with session_id on creation in api/services/remote_sync.py
- [ ] T034 [US2] Create GET /api/memory/sessions/{session_id} endpoint in api/routers/memory.py
- [ ] T035 [US2] Add date range filtering to memory queries
- [ ] T036 [US2] Add session attribution to query results

**Checkpoint**: At this point, cross-session context queries work independently

---

## Phase 5: User Story 3 - Cross-Project Memory Sharing (Priority: P2)

**Goal**: Query memories across different projects (dionysus-core, inner-architect-companion, etc.)

**Independent Test**:
1. Create memory in Project A with "API rate limiting pattern" content
2. Switch to Project B context
3. Query "What patterns have we learned?"
4. Verify Project A memory surfaces with project attribution

### Tests for User Story 3

- [ ] T037 [P] [US3] Integration test for cross-project query in tests/integration/test_cross_project_query.py

### Implementation for User Story 3

- [ ] T038 [US3] Tag memories with project_id from current working directory
- [ ] T039 [US3] Implement cross-project query endpoint GET /api/memory/projects in api/routers/memory.py
- [ ] T040 [US3] Add project_id filter and attribution to query results
- [ ] T041 [US3] Create Project nodes in Neo4j for known projects

**Checkpoint**: At this point, cross-project queries work independently

---

## Phase 6: User Story 4 - n8n Workflow Integration (Priority: P3)

**Goal**: n8n workflows automatically process sync, embedding generation, and summarization

**Independent Test**:
1. Create memory locally without embedding
2. Verify n8n workflow triggers
3. Verify Ollama generates embedding
4. Verify memory in Neo4j has embedding vector

### Tests for User Story 4

- [ ] T042 [P] [US4] Integration test for Ollama embedding generation in tests/integration/test_ollama_embedding.py
- [ ] T043 [P] [US4] Integration test for session summary workflow in tests/integration/test_session_summary.py

### Implementation for User Story 4

- [ ] T044 [US4] Deploy memory_sync.json workflow to n8n (contracts/n8n-workflow.json)
- [ ] T045 [US4] Implement session-end detection (30min timeout or explicit command)
- [ ] T046 [US4] Create session_summary.json n8n workflow in n8n-workflows/
- [ ] T047 [US4] Trigger summarization workflow on session end
- [ ] T048 [US4] Store session summaries in Neo4j Session nodes

**Checkpoint**: At this point, n8n automation works independently

---

## Phase 7: User Story 5 - LLM Destruction Detection & Archon Integration (Priority: P3)

**Goal**: Detect rapid delete patterns, alert user, integrate with Archon task context

**Independent Test**:
1. Rapidly delete >10 memories in 60 seconds
2. Verify destruction alert is logged
3. Create Archon task, add memory related to task
4. Query memory by task topic
5. Verify memory is discoverable

### Tests for User Story 5

- [ ] T049 [P] [US5] Chaos test for LLM destruction detection in tests/integration/test_destruction_detection.py
- [ ] T050 [P] [US5] Integration test for Archon task tagging in tests/integration/test_archon_integration.py

### Implementation for User Story 5

- [ ] T051 [US5] Implement destruction detection (>10 deletes/60s threshold) in api/services/destruction_detector.py
- [ ] T052 [US5] Add alert logging and optional n8n webhook for destruction alerts
- [ ] T053 [US5] Tag memories with active Archon task_id when available
- [ ] T054 [US5] Query Archon MCP for current task context on memory creation

**Checkpoint**: At this point, LLM safety and Archon integration work

---

## Phase 8: MCP Tools & Polish

**Purpose**: Expose sync capabilities via MCP tools, final polish

- [ ] T055 [P] Create sync_now MCP tool in mcp/tools/sync.py
- [ ] T056 [P] Create get_sync_status MCP tool in mcp/tools/sync.py
- [ ] T057 Register sync tools in mcp/server.py
- [ ] T058 Add structured logging for all sync operations
- [ ] T059 Run quickstart.md validation end-to-end
- [ ] T060 Update API documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1): No dependencies on other stories - **MVP**
  - US2 (P2): Can start after Foundation, may use US1 sync infra
  - US3 (P2): Can start after Foundation, may use US1 sync infra
  - US4 (P3): Depends on US1 n8n webhook being functional
  - US5 (P3): Can start after Foundation, integrates with US1 sync
- **Polish (Phase 8)**: Depends on US1 at minimum, preferably all stories

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US1 (P1) | Foundation only | Phase 2 complete |
| US2 (P2) | Foundation + US1 sync | Phase 3 complete |
| US3 (P2) | Foundation + US1 sync | Phase 3 complete |
| US4 (P3) | US1 webhook functional | Phase 3 complete |
| US5 (P3) | Foundation + US1 sync | Phase 3 complete |

### Within Each User Story (TDD Order)

1. **Tests FIRST** - Write all tests, verify they FAIL
2. **Models** - Data structures
3. **Services** - Business logic
4. **Endpoints** - API routes
5. **Integration** - Wire components together
6. **Verify** - Run tests, ensure they PASS

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T002 [P] + T003 [P] can run in parallel
```

**Phase 2 (Foundation)**:
```
T007 + T008 [P] tests in parallel
T009 + T010 [P] + T011 [P] models in parallel
```

**Phase 3 (US1)**:
```
T016 [P] + T017 [P] + T018 [P] tests in parallel
T022 [P] + T023 [P] + T024 [P] endpoints in parallel
```

**Phase 4 (US2)**:
```
T029 [P] + T030 [P] tests in parallel
```

**Phase 8 (Polish)**:
```
T055 [P] + T056 [P] MCP tools in parallel
```

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together (TDD - write first, verify fail):
Task T016: "Integration test for Neo4j CRUD in tests/integration/test_neo4j_sync.py"
Task T017: "Contract test for POST /sync/memory in tests/contract/test_webhook_sync.py"
Task T018: "Integration test for n8n workflow in tests/integration/test_n8n_workflow.py"

# Launch all endpoints for US1 together (after services):
Task T022: "Create POST /sync/memory webhook in api/routers/sync.py"
Task T023: "Create POST /sync/trigger endpoint in api/routers/sync.py"
Task T024: "Create GET /sync/status endpoint in api/routers/sync.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 - Memory Survives LLM Wipeout
4. **STOP and VALIDATE**:
   - Create memories locally
   - Verify sync to Neo4j in <30s
   - Destroy local DB
   - Run bootstrap recovery
   - Verify 100% recovery
5. Deploy/demo if ready - **This is your safety net!**

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP - LLM Safety**)
3. Add User Story 2 → Test independently → Cross-session queries work
4. Add User Story 3 → Test independently → Cross-project queries work
5. Add User Story 4 → Test independently → n8n automation works
6. Add User Story 5 → Test independently → Destruction detection + Archon
7. Polish Phase → MCP tools, logging, docs

### TDD Workflow Per Task

```
For each task pair (TEST → IMPL):
1. Write test (e.g., T016)
2. Run test → Verify it FAILS
3. Write implementation (e.g., T020)
4. Run test → Verify it PASSES
5. Commit: "feat(sync): implement Neo4j CRUD with passing tests"
```

---

## Task Summary

| Phase | Purpose | Task Count |
|-------|---------|------------|
| Phase 1 | Setup | 6 |
| Phase 2 | Foundation | 9 |
| Phase 3 | US1 - LLM Wipeout (P1) MVP | 13 |
| Phase 4 | US2 - Cross-Session (P2) | 8 |
| Phase 5 | US3 - Cross-Project (P2) | 5 |
| Phase 6 | US4 - n8n Integration (P3) | 7 |
| Phase 7 | US5 - Destruction/Archon (P3) | 6 |
| Phase 8 | Polish | 6 |
| **Total** | | **60** |

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- **TDD**: All tests must FAIL before implementation begins
- **Integration tests run against live VPS** (neo4j:7687, n8n:5678, ollama:11434)
- Commit after each task or logical TEST→IMPL pair
- Stop at any checkpoint to validate story independently
- MVP (Phase 3) provides core LLM safety protection
