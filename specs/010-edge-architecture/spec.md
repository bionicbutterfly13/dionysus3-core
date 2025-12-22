# Feature Specification: Hybrid Edge Architecture

**Feature Branch**: `010-edge-architecture`
**Created**: 2025-12-22
**Status**: Draft
**Input**: Distributed system with lightweight edge agent + VPS backend for scalability and offline capability

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Edge Agent Installation (Priority: P1) 🎯 MVP

A new user downloads and installs the Dionysus edge agent on their device. The agent is lightweight (~50MB) and provides immediate value with local memory operations.

**Why this priority**: Without installation, no other features work. This is the entry point for all users.

**Independent Test**: User can install agent, authenticate with VPS, and perform basic memory ingest/recall locally.

**Acceptance Scenarios**:

1. **Given** a user with no Dionysus installation, **When** they download and run the installer, **Then** the agent starts within 30 seconds and prompts for VPS authentication
2. **Given** a freshly installed agent, **When** the user provides VPS credentials, **Then** the agent authenticates and pulls identity baseline from VPS
3. **Given** an authenticated agent, **When** the user ingests a memory offline, **Then** the memory is stored locally and queued for sync

---

### User Story 2 - Offline Memory Operations (Priority: P1) 🎯 MVP

A user can ingest and recall memories even without internet connectivity. All writes go to local SQLite, background sync handles VPS propagation.

**Why this priority**: Core value proposition - cognitive assistant works anywhere, anytime.

**Independent Test**: User can create memories, recall them, and verify they persist locally without network.

**Acceptance Scenarios**:

1. **Given** an authenticated agent with no network, **When** the user ingests a memory, **Then** the memory is stored in local SQLite and marked for sync
2. **Given** memories in local cache, **When** the user queries for recall, **Then** relevant memories are returned from local store within 100ms
3. **Given** queued sync items, **When** network becomes available, **Then** items are synced to VPS within 60 seconds

---

### User Story 3 - Background Sync (Priority: P2)

The edge agent continuously syncs local changes to VPS and pulls updates from VPS to local cache, providing seamless data consistency.

**Why this priority**: Enables multi-device usage and ensures data durability beyond the edge device.

**Independent Test**: Create memory on Device A, verify it appears on Device B after sync.

**Acceptance Scenarios**:

1. **Given** a memory created locally, **When** sync runs, **Then** memory appears on VPS within 60 seconds
2. **Given** a memory created on VPS (from another device), **When** sync runs, **Then** memory appears in local cache within 60 seconds
3. **Given** sync failure (VPS unreachable), **When** retries exhaust, **Then** item remains in queue with exponential backoff

---

### User Story 4 - Heavy Query Routing (Priority: P2)

Complex queries (graph traversal, consolidation, LLM generation) are routed to VPS while simple operations stay local.

**Why this priority**: Balances performance (local = fast) with capability (VPS = powerful).

**Independent Test**: Execute graph query, verify it routes to VPS and returns results.

**Acceptance Scenarios**:

1. **Given** a simple recall query, **When** executed, **Then** results come from local SQLite (latency < 100ms)
2. **Given** a graph traversal query, **When** executed, **Then** request routes to VPS API and returns results
3. **Given** a consolidation request, **When** triggered, **Then** VPS performs consolidation and notifies edge agent of updates

---

### User Story 5 - Multi-Device Identity (Priority: P3)

A user with multiple devices sees consistent identity and memory across all devices.

**Why this priority**: Power user feature - most users start with single device.

**Independent Test**: Authenticate same account on two devices, verify memories sync bidirectionally.

**Acceptance Scenarios**:

1. **Given** user with two authenticated devices, **When** memory created on Device A, **Then** it appears on Device B within 2 minutes
2. **Given** conflicting edits on two devices, **When** sync runs, **Then** last-write-wins with conflict logged
3. **Given** new device authentication, **When** identity baseline pulls, **Then** device has full memory context within 5 minutes

---

### Edge Cases

- What happens when local SQLite fills up? (Answer: LRU eviction of cached VPS memories, queued writes never evicted)
- How does system handle authentication expiry? (Answer: Graceful degradation to offline mode, prompt re-auth)
- What if VPS is permanently unreachable? (Answer: Local-only mode continues, sync queue persists indefinitely)
- What happens on device wipe? (Answer: Re-authenticate, pull from VPS, local-only memories lost if not synced)

## Requirements *(mandatory)*

### Functional Requirements

**Edge Agent**:
- **FR-001**: Agent MUST install and start within 30 seconds on supported platforms (macOS, Windows, Linux, iOS, Android)
- **FR-002**: Agent MUST authenticate with VPS using OAuth2 or API key
- **FR-003**: Agent MUST store memories in local SQLite database
- **FR-004**: Agent MUST provide FastAPI endpoints for local integrations (localhost:8080)
- **FR-005**: Agent MUST queue all write operations for VPS sync
- **FR-006**: Agent MUST support offline mode for ingest and recall operations
- **FR-007**: Agent MUST be under 50MB installed size

**Sync Engine**:
- **FR-008**: Sync engine MUST run as background process with configurable interval (default: 30s)
- **FR-009**: Sync engine MUST handle network failures with exponential backoff (10s, 60s, 300s)
- **FR-010**: Sync engine MUST track sync status per item (queued, syncing, synced, failed)
- **FR-011**: Sync engine MUST support bidirectional sync (local→VPS and VPS→local)
- **FR-012**: Sync engine MUST resolve conflicts using last-write-wins strategy

**Query Routing**:
- **FR-013**: System MUST route simple queries (keyword, recent, by-id) to local SQLite
- **FR-014**: System MUST route complex queries (graph traversal, semantic search) to VPS
- **FR-015**: System MUST route consolidation and LLM operations to VPS
- **FR-016**: System MUST cache VPS query results locally with configurable TTL

**VPS Integration**:
- **FR-017**: VPS MUST provide REST API for edge agent communication
- **FR-018**: VPS MUST support webhook notifications for push updates to edge agents
- **FR-019**: VPS MUST track device registrations per user account
- **FR-020**: VPS MUST enforce rate limits per device (100 req/min default)

### Key Entities

- **EdgeAgent**: The installed software on user's device; attributes: device_id, user_id, install_date, last_sync, sync_status
- **LocalMemory**: Cached memory in SQLite; attributes: id, content, embedding (optional), created_at, synced_at, source (local/vps)
- **SyncQueue**: Pending operations for VPS; attributes: id, operation (create/update/delete), payload, status, retry_count, created_at
- **DeviceRegistration**: VPS record of authenticated devices; attributes: device_id, user_id, device_name, last_seen, platform

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agent installs and authenticates in under 60 seconds on first run
- **SC-002**: Local recall queries return results in under 100ms (p95)
- **SC-003**: VPS queries return results in under 500ms (p95) over typical network
- **SC-004**: Sync latency is under 60 seconds for 95% of operations
- **SC-005**: Agent memory footprint is under 100MB RAM during normal operation
- **SC-006**: System supports 10,000 concurrent edge agents per VPS instance
- **SC-007**: Offline mode works indefinitely with local-only operations
- **SC-008**: Multi-device sync achieves eventual consistency within 5 minutes

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         USER'S EDGE DEVICE                               │
│                         (Lightweight ~50MB)                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐ │
│  │   Edge Agent    │   │    SQLite DB    │   │      Sync Queue         │ │
│  │   (FastAPI)     │──▶│   (Hot Cache)   │   │  (Pending Operations)   │ │
│  │   :8080         │   │                 │   │                         │ │
│  └─────────────────┘   └─────────────────┘   └─────────────────────────┘ │
│          │                                              │                │
│          │  Local Ops                      Background   │                │
│          ▼                                   Sync       ▼                │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                         Sync Engine                                 │ │
│  │  - Bidirectional sync with VPS                                      │ │
│  │  - Conflict resolution (last-write-wins)                            │ │
│  │  - Exponential backoff on failure                                   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
└────────────────────────────────────│─────────────────────────────────────┘
                                     │ HTTPS
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                              VPS BACKEND                                 │
│                          (Heavy Processing)                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐ │
│  │  dionysus-api   │   │   PostgreSQL    │   │        Neo4j            │ │
│  │     :8000       │──▶│   (Canonical)   │──▶│    (Graph Memory)       │ │
│  └─────────────────┘   └─────────────────┘   └─────────────────────────┘ │
│          │                                              ▲                │
│          │                                              │                │
│          ▼                                              │                │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐ │
│  │      n8n        │──▶│    Graphiti     │   │        Ollama           │ │
│  │   (Workflows)   │   │   (Entities)    │   │     (Embeddings)        │ │
│  └─────────────────┘   └─────────────────┘   └─────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Assumptions

- Users have reliable (but not always available) internet connectivity
- VPS can handle 10,000+ concurrent device connections
- SQLite is sufficient for edge device storage (typical user < 100MB memories)
- OAuth2 or API key authentication is acceptable for MVP
- Last-write-wins is acceptable conflict resolution for MVP

## Dependencies

- Existing VPS infrastructure (dionysus-api, PostgreSQL, Neo4j, n8n)
- SQLite library for edge platforms
- Cross-platform build tooling (Rust/Go for CLI, Flutter/React Native for mobile)
