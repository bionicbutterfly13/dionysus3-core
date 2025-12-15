# Feature Specification: Remote Persistence Safety Framework

**Feature Branch**: `002-remote-persistence-safety`
**Created**: 2025-12-14
**Status**: Draft
**Input**: User description: "Organize remaining persistence tasks into a coherent narrative and find missing elements for a cross-project cross-session persistence framework using the current remotely hosted n8n, neo4j, ollama setup for safety against wipeout by LLMs including claude, codex, gemini"

## Problem Statement

When working with AI coding assistants (Claude Code, GitHub Codex, Gemini), there is significant risk of accidental data loss:
- LLMs may overwrite configuration files, databases, or critical state
- Local development environments can be wiped during aggressive refactoring
- Session context is lost between conversations
- Project context is lost across different coding sessions
- No recovery mechanism exists when local persistence is destroyed

**Current State**: dionysus3-core uses PostgreSQL locally, but has no remote backup or cross-session persistence. The remote VPS (72.61.78.89) has n8n, Neo4j, and Ollama running but disconnected from the main application.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Memory Survives LLM Wipeout (Priority: P1)

As a developer working with AI coding assistants, I want my critical project memory persisted to a remote location so that when an LLM accidentally destroys local state, I can recover without losing context.

**Why this priority**: This is the core safety requirement - without it, the entire feature has no value.

**Independent Test**: Can be fully tested by: (1) creating memory entries, (2) simulating local data loss, (3) verifying recovery from remote Neo4j.

**Acceptance Scenarios**:

1. **Given** memory entries exist locally, **When** local database is destroyed, **Then** all memory can be recovered from remote Neo4j within 60 seconds
2. **Given** remote sync is enabled, **When** new memory is created locally, **Then** it appears in remote Neo4j within 30 seconds
3. **Given** remote Neo4j contains memory, **When** local system starts fresh, **Then** bootstrap recovery restores full context

---

### User Story 2 - Cross-Session Context Preservation (Priority: P2)

As an AI-assisted developer, I want to query "What did we discuss in the last session about [topic]?" and receive accurate context from previous coding sessions.

**Why this priority**: Enables continuity across Claude Code conversations, which is critical for long-running projects.

**Independent Test**: Can be tested by creating memories in Session A, starting new Session B, and querying for Session A context.

**Acceptance Scenarios**:

1. **Given** Session A created 5 memories about "authentication", **When** Session B queries "What did we discuss about authentication?", **Then** returns all 5 memories with session attribution
2. **Given** multiple sessions exist, **When** querying by date range, **Then** returns memories from sessions within that range
3. **Given** a session ended 7 days ago, **When** querying for that session's context, **Then** retrieves full session history

---

### User Story 3 - Cross-Project Memory Sharing (Priority: P2)

As a developer managing multiple related projects (IAS App, dionysus-memory, sales pages), I want shared learnings and patterns to be accessible across all projects.

**Why this priority**: Prevents rediscovering solutions already found in sibling projects.

**Independent Test**: Can be tested by creating memory in Project A and querying it from Project B context.

**Acceptance Scenarios**:

1. **Given** "API rate limiting pattern" learned in Project A, **When** working on Project B with similar needs, **Then** relevant memory surfaces during queries
2. **Given** multiple projects share a common dependency, **When** that dependency has a known issue, **Then** all projects can access the troubleshooting memory
3. **Given** user works on Project B, **When** querying "what patterns have we learned?", **Then** returns cross-project insights tagged by source project

---

### User Story 4 - n8n Workflow Integration (Priority: P3)

As a developer, I want n8n workflows to automatically process memory operations so that sync, summarization, and embedding generation happen without manual intervention.

**Why this priority**: Automation ensures reliability - manual sync will be forgotten.

**Independent Test**: Can be tested by triggering a memory event and verifying n8n workflow execution completes.

**Acceptance Scenarios**:

1. **Given** memory is created locally, **When** webhook fires, **Then** n8n workflow syncs to Neo4j within 10 seconds
2. **Given** n8n workflow is triggered, **When** Ollama embedding is generated, **Then** memory includes vector for semantic search
3. **Given** session ends, **When** summarization workflow runs, **Then** session summary is created and persisted

---

### User Story 5 - Archon Task Persistence Integration (Priority: P3)

As a developer using Archon MCP for task management, I want task context and project decisions persisted alongside memory so that task history survives LLM wipeout.

**Why this priority**: Archon already handles task management - integrating it completes the persistence picture.

**Independent Test**: Can be tested by creating Archon tasks, wiping local context, and verifying tasks persist in Archon's database.

**Acceptance Scenarios**:

1. **Given** Archon task is created, **When** local Claude Code context is lost, **Then** task remains accessible via Archon MCP
2. **Given** task is marked complete with learnings, **When** querying memory for that task's topic, **Then** learnings are discoverable
3. **Given** project has 50 tasks with notes, **When** new session starts, **Then** Archon provides full task context without local state

---

### Edge Cases

- What happens when remote Neo4j is unreachable? (Graceful degradation: queue locally, sync when available)
- What happens when local and remote memory conflict? (Last-write-wins with conflict log)
- What happens when Ollama embedding service is down? (Fallback to cached embeddings or skip embedding)
- How do we handle memory that shouldn't be shared cross-project? (Project-scoped vs global tags)
- What happens when an LLM is actively destroying data during a sync? (Pause sync, alert user, require manual intervention)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST sync all memory entries to remote Neo4j within 30 seconds of creation
- **FR-002**: System MUST recover full memory state from remote Neo4j on bootstrap when local state is empty
- **FR-003**: System MUST track session boundaries with unique session IDs and timestamps
- **FR-004**: System MUST tag memories with source project identifier for cross-project queries
- **FR-005**: System MUST expose webhook endpoints for n8n workflow integration
- **FR-006**: System MUST generate vector embeddings via Ollama for semantic search
- **FR-007**: System MUST maintain sync queue when remote services are unavailable
- **FR-008**: System MUST log all sync operations for audit and debugging
- **FR-009**: System MUST support querying memories by session, project, date range, or semantic similarity
- **FR-010**: System MUST integrate with Archon MCP for task/project context preservation
- **FR-011**: System MUST provide manual "sync now" command for immediate backup
- **FR-012**: System MUST detect and alert on data destruction patterns (rapid deletes, schema drops)

### Key Entities

- **Memory**: Core unit of knowledge (episodic, semantic, procedural, strategic) with embedding, project_id, session_id
- **Session**: Bounded conversation/work period with start_time, end_time, summary, project_id
- **Project**: Namespace for related memories (dionysus-core, inner-architect-companion, etc.)
- **SyncEvent**: Audit record of sync operations (timestamp, direction, record_count, status)
- **Journey**: Collection of sessions for a user/purpose over time (spans multiple projects if needed)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Recovery from complete local data loss completes in under 60 seconds for 1000 memory entries
- **SC-002**: 99.9% of memory entries are successfully synced to remote within 30 seconds under normal conditions
- **SC-003**: Cross-session queries return relevant context with 85%+ accuracy (measured by user relevance rating)
- **SC-004**: Cross-project queries surface relevant learnings for 70%+ of applicable situations
- **SC-005**: Zero data loss events due to LLM actions when sync is operational (measured over 90-day period)
- **SC-006**: Bootstrap recovery works correctly 100% of the time when remote contains valid data
- **SC-007**: System degrades gracefully (local-only mode) when remote is unreachable, with full sync on reconnect

## Architecture Overview

### Remote Infrastructure (VPS 72.61.78.89)

| Service | Purpose | Port |
|---------|---------|------|
| Neo4j   | Graph database for memory persistence, relationships, cross-project queries | 7474, 7687 |
| n8n     | Workflow automation for sync, summarization, embedding generation | 5678 |
| Ollama  | Local LLM embeddings (nomic-embed-text or similar) | 11434 |

### Integration Points

1. **Local → Remote Sync**: Webhook from dionysus-core triggers n8n workflow
2. **Remote → Local Recovery**: Bootstrap script queries Neo4j and hydrates local DB
3. **Embedding Pipeline**: n8n calls Ollama for vector generation
4. **Archon Bridge**: Memory tagged with Archon task_id for bidirectional context

### Data Flow

```
Local Memory Created
       |
       v
Webhook fires to n8n (http://72.61.78.89:5678/webhook/memory-sync)
       |
       v
n8n Workflow:
  1. Validate payload
  2. Call Ollama for embedding if needed
  3. Write to Neo4j with project_id, session_id
  4. Return success/failure
       |
       v
Local marks as synced (sync_status: 'synced', synced_at: timestamp)
```

## Relationship to Existing Tasks

### Archon Persistence Tasks (dionysus-memory project)

| Phase   | Task | Relationship to This Feature |
|---------|------|------------------------------|
| Phase 1 | Wire consciousness persistence into Node 6 | **Extend**: Add remote sync hook after local persist |
| Phase 4 | Configure automated memory tiering scheduler | **Integrate**: Include remote sync in tier migration |
| Phase 5 | Create SessionManager service | **Core**: SessionManager must track session_id for remote tagging |
| Phase 5 | Connect AutobiographicalJourney to document pipeline | **Core**: Journey is the cross-session container |
| Phase 5 | Test Phase 5: session continuity | **Extend**: Add remote recovery test cases |

### New Tasks Required (Test-First Order)

**Phase A: Foundation (Neo4j + Webhook)**
1. **TEST: Neo4j connectivity and CRUD** - Integration test against VPS Neo4j
2. **IMPL: Neo4j schema for dionysus memory** - Graph model matching local PostgreSQL
3. **TEST: Webhook contract validation** - Contract test for memory-sync webhook
4. **IMPL: Webhook endpoint in dionysus-core** - POST /api/sync/memory

**Phase B: Sync Pipeline (n8n + RemoteSyncService)**
5. **TEST: n8n workflow end-to-end** - Integration test: webhook → neo4j
6. **IMPL: n8n Memory Sync Workflow** - Webhook → validate → embed → persist
7. **TEST: RemoteSyncService queue/retry** - Unit tests for queue and retry logic
8. **IMPL: RemoteSyncService** - Handles webhook calls, queue management, retry
9. **IMPL: Add sync_status columns** - Track sync state per memory record

**Phase C: Recovery (Bootstrap + Session)**
10. **TEST: Bootstrap recovery scenario** - Recovery test: destroy local → restore from Neo4j
11. **IMPL: Bootstrap Recovery Script** - Queries Neo4j, hydrates local DB
12. **TEST: Session boundary tracking** - Integration test for session_id tagging
13. **IMPL: SessionManager with session_id** - Extend existing SessionManager design

**Phase D: Cross-Session + Safety**
14. **TEST: Cross-session query accuracy** - Integration test for context retrieval
15. **IMPL: Cross-session query API** - GET /api/memory/sessions/{session_id}
16. **TEST: LLM destruction detection** - Chaos test for rapid delete detection
17. **IMPL: LLM Destruction Detection** - Monitor and alert on destructive patterns
18. **IMPL: Integrate with Archon task context** - Tag memories with active task_id

**Phase E: Automation**
19. **TEST: Session summary workflow** - Integration test for auto-summarization
20. **IMPL: n8n Session Summary Workflow** - Triggered on session end

## Assumptions

- Remote VPS (72.61.78.89) has stable network connectivity from development environment
- Neo4j, n8n, and Ollama services remain running (monitored externally)
- Ollama has sufficient model loaded for embedding generation
- n8n workflows can be version-controlled and restored if lost
- Archon MCP server is available for task context queries
- Session boundaries are definable (explicit start/end or timeout-based)

## Dependencies

- Existing: PostgreSQL schema (schema.sql), Memory services, IAS API
- External: Neo4j 5 on VPS, n8n on VPS, Ollama on VPS
- Integration: Archon MCP server for task persistence
- Design: specs/001-session-continuity (session/journey data model)

## Development Methodology: Test-First TDD

**MANDATORY**: All implementation follows test-driven, test-first development with integrated testing.

### Test-First Workflow

For each feature/task:
1. **Write failing integration test** - Define expected behavior against real remote services
2. **Write failing unit tests** - Define component behavior in isolation
3. **Implement minimum code** - Make tests pass
4. **Refactor** - Clean up while tests stay green
5. **Integration verification** - Run full integration suite against VPS

### Test Categories

| Category | Purpose | Target |
|----------|---------|--------|
| **Contract Tests** | Verify API/webhook contracts | n8n webhooks, Neo4j queries |
| **Integration Tests** | End-to-end against real services | VPS (neo4j, n8n, ollama) |
| **Unit Tests** | Component logic in isolation | RemoteSyncService, SessionManager |
| **Recovery Tests** | Disaster recovery scenarios | Bootstrap from Neo4j, queue replay |
| **Chaos Tests** | Failure mode handling | Network drops, service unavailable |

### Test Infrastructure Requirements

- **FR-TEST-001**: Integration tests MUST run against live VPS services (not mocks)
- **FR-TEST-002**: Each acceptance scenario MUST have a corresponding test before implementation
- **FR-TEST-003**: Tests MUST be runnable in CI and locally
- **FR-TEST-004**: Recovery tests MUST actually destroy and restore data
- **FR-TEST-005**: Test suite MUST complete in under 5 minutes for fast feedback

### Test-First Task Ordering

Each implementation task is paired with its test task (test comes first):

| Order | Task | Type |
|-------|------|------|
| 1 | Test: Neo4j connectivity and basic CRUD | Integration |
| 2 | Implement: Neo4j schema for dionysus memory | Implementation |
| 3 | Test: Webhook receives and validates payload | Contract |
| 4 | Implement: Webhook endpoint in dionysus-core | Implementation |
| 5 | Test: n8n workflow processes memory sync | Integration |
| 6 | Implement: n8n Memory Sync Workflow | Implementation |
| 7 | Test: RemoteSyncService queues and retries | Unit |
| 8 | Implement: RemoteSyncService | Implementation |
| 9 | Test: Bootstrap recovery restores from Neo4j | Recovery |
| 10 | Implement: Bootstrap Recovery Script | Implementation |
| 11 | Test: Session boundaries tracked correctly | Integration |
| 12 | Implement: SessionManager with session_id tagging | Implementation |
| 13 | Test: Cross-session query returns correct context | Integration |
| 14 | Implement: Cross-session query API | Implementation |
| 15 | Test: LLM destruction detection triggers alert | Chaos |
| 16 | Implement: LLM Destruction Detection | Implementation |

### Success Criteria for Tests

- **SC-TEST-001**: 100% of acceptance scenarios have passing tests before feature is marked complete
- **SC-TEST-002**: Zero implementations merged without corresponding test coverage
- **SC-TEST-003**: Integration tests pass against live VPS on every PR
- **SC-TEST-004**: Recovery test successfully restores 1000 memories from Neo4j backup

## Out of Scope

- Real-time collaborative editing between multiple developers
- Automatic conflict resolution (last-write-wins is sufficient)
- Mobile/offline support
- Multi-tenant (single developer use case)
- Encryption at rest for remote storage (trusted VPS)
