# Feature Specification: Session Continuity

**Feature Branch**: `001-session-continuity`
**Created**: 2025-12-13
**Status**: Draft
**Input**: Archon Phase 5 tasks + existing IAS session storage

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track Conversations Across Sessions (Priority: P1)

The AGI system MUST track conversations across multiple sessions, linking related dialogues into a coherent "journey" that represents the user's progression over time.

**Why this priority**: Without session tracking, each conversation is isolated. The AGI cannot reference past discussions ("Remember when we talked about X?") which breaks the illusion of continuous relationship.

**Independent Test**: Create 3 sessions, send messages to each, verify all 3 appear in a single journey timeline with proper ordering.

**Acceptance Scenarios**:

1. **Given** a new user starts their first session, **When** a session is created, **Then** a new journey is created and the session is linked to it
2. **Given** a user with an existing journey, **When** they start a new session, **Then** the session is linked to their existing journey (not a new one)
3. **Given** a journey with 5 sessions, **When** querying journey timeline, **Then** sessions are returned in chronological order with timestamps

---

### User Story 2 - Query Journey History (Priority: P2)

Users and the AGI MUST be able to query past conversations within a journey using natural language patterns like "What did we discuss in session X?" or "Remember when we discussed Y?"

**Why this priority**: Tracking without retrieval provides no value. The AGI needs to actually USE the session history to provide continuity.

**Independent Test**: Add 3 sessions with distinct topics, query "sessions about topic X", verify correct session is returned.

**Acceptance Scenarios**:

1. **Given** a journey with 10 sessions, **When** querying "What did we discuss about goals?", **Then** sessions mentioning goals are returned with relevant snippets
2. **Given** a journey, **When** querying "session from last week", **Then** sessions within that time window are returned
3. **Given** a session with diagnosis, **When** querying journey history, **Then** diagnosis metadata is included in results

---

### User Story 3 - Link Documents to Journey (Priority: P3)

The AGI MUST be able to link uploaded documents, generated artifacts, and external content to a user's journey for future reference.

**Why this priority**: Sessions aren't just conversations - users may upload files, receive generated plans, etc. These artifacts should be part of the journey timeline.

**Independent Test**: Add document to journey, query journey timeline, verify document appears alongside sessions.

**Acceptance Scenarios**:

1. **Given** a journey, **When** a document is added via `add_document_to_journey()`, **Then** the document appears in the journey timeline
2. **Given** a journey with mixed sessions and documents, **When** querying timeline, **Then** both types are returned interleaved by timestamp
3. **Given** a document linked to a journey, **When** deleting the document, **Then** the journey reference is cleaned up (no orphan references)

---

### Edge Cases

- ~~What happens when a user creates a session without being authenticated (anonymous journey)?~~ **Resolved**: Device_id always exists; no anonymous state possible.
- How does the system handle journey retrieval when database is temporarily unavailable? *(Deferred to planning phase)*
- ~~What happens if two sessions are created simultaneously for the same device?~~ **Resolved**: Multiple concurrent sessions allowed per journey.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a journey record on first session creation for a user
- **FR-002**: System MUST link subsequent sessions to existing journey (not create duplicates)
- **FR-003**: System MUST store session summaries for efficient journey queries
- **FR-004**: System MUST support querying journey history by keyword, time range, and metadata
- **FR-005**: *(Deferred - Post-MVP)* System MAY track thoughtseed_trajectory and attractor_dynamics_history per journey (Dionysus IWMT consciousness concepts)
- **FR-006**: System MUST expose journey operations via MCP tools for AGI self-reference

### Key Entities

- **Journey**: Represents a device's complete interaction history; identified by device_id (persistent local identifier); has many Sessions and Documents
- **Session**: A single conversation with messages, timestamps, optional diagnosis; linked to exactly one Journey
- **JourneyDocument**: A document/artifact linked to a journey with type and metadata

### Integration Dependencies

- **PostgreSQL**: Primary storage for journeys, sessions, and documents (local database via DATABASE_URL)
- **002-remote-persistence-safety**: Optional sync to Neo4j for backup/recovery (future integration)

## Clarifications

### Session 2025-12-15

- Q: How is a user identified to link sessions into a journey? → A: Device/installation ID (persistent local identifier)
- Q: Where is journey/session data persisted? → A: PostgreSQL (local, same as 002 memories)
- Q: How are anonymous sessions handled? → A: Not applicable - device_id always exists, no anonymous state
- Q: What are thoughtseed_trajectory and attractor_dynamics_history (FR-005)? → A: Dionysus IWMT consciousness concepts; deferred from MVP
- Q: What happens if two sessions are created simultaneously for the same device? → A: Allow multiple concurrent sessions per journey

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Journey creation adds <50ms to first session creation
- **SC-002**: Journey timeline query returns <200ms for journeys with 100+ sessions
- **SC-003**: Zero data loss when linking sessions to journeys (referential integrity enforced)
- **SC-004**: AGI can successfully query "What did we discuss?" and receive relevant results
