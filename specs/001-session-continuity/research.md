# Research: Session Continuity

**Date**: 2025-12-13
**Input**: Technical Context from plan.md

## Research Summary

All NEEDS CLARIFICATION items resolved. Feature can proceed to design.

---

## Decision 1: Session Storage Migration Strategy

**Decision**: Dual-mode storage - keep in-memory for MVP compatibility, add PostgreSQL persistence for new journeys.

**Rationale**:
- Existing IAS router uses in-memory `sessions: dict[str, dict]` (api/routers/ias.py:108)
- Breaking change to remove in-memory would require frontend changes
- Adding PostgreSQL persistence alongside allows gradual migration
- SessionManager service abstracts storage backend

**Alternatives Considered**:
1. **Full PostgreSQL migration** - Rejected: Breaking change to existing clients
2. **Redis for sessions** - Rejected: Adds infrastructure dependency, PostgreSQL sufficient
3. **Keep in-memory only** - Rejected: Doesn't satisfy persistence requirement

---

## Decision 2: Journey-Session Linking Pattern

**Decision**: Use `journey_id` FK on sessions table with `device_id` as journey grouping key.

**Rationale**:
- Schema pattern follows existing FK relationships (e.g., `episodic_memories.memory_id → memories.id`)
- `device_id` is always present (no anonymous state per clarification 2025-12-15)
- Journey is created lazily on first session for a device_id
- Device ID stored in `~/.dionysus/device_id` (UUID v4)

**Alternatives Considered**:
1. **Session has many journeys** - Rejected: Inverts natural relationship
2. **Junction table (journey_sessions)** - Rejected: Adds complexity, 1:N sufficient
3. **Embedded journey data in session** - Rejected: Violates normalization, complicates queries

---

## Decision 3: MCP Tool Exposure

**Decision**: Add 3 new MCP tools: `get_or_create_journey`, `query_journey_history`, `add_document_to_journey`.

**Rationale**:
- Follows existing MCP tool pattern in `mcp/server.py` (e.g., `create_memory`, `search_memories`)
- Tool names match Archon task descriptions exactly
- Enables Dionysus self-reference ("Remember when we discussed...")
- Non-breaking addition (new tools only)

**Alternatives Considered**:
1. **Extend existing memory tools** - Rejected: Journey is not a memory type
2. **Single journey_operation tool with action param** - Rejected: Less discoverable, violates SRP
3. **REST API only** - Rejected: Dionysus needs MCP access for self-reference

---

## Decision 4: Thoughtseed Trajectory Tracking (DEFERRED)

**Decision**: Defer `thoughtseed_trajectory` and `attractor_dynamics_history` to post-MVP.

**Rationale**:
- FR-005 marked as deferred in spec clarification (2025-12-15)
- These are Dionysus IWMT consciousness concepts requiring separate design
- MVP focuses on core journey/session tracking
- Schema can add JSONB columns later without breaking changes

**Future Implementation** (when ready):
- Store as JSONB columns on journey table
- JSONB allows flexible schema evolution
- Append-only trajectory pattern

---

## Decision 5: Query Interface Design

**Decision**: Use full-text search on session summaries with optional time-range and keyword filters.

**Rationale**:
- PostgreSQL pg_trgm extension already enabled (schema.sql:16)
- Session summaries are generated/stored for efficient search (avoid scanning full messages)
- Time-range queries use existing TIMESTAMPTZ indexes
- Keyword search uses GIN index on summary text

**Alternatives Considered**:
1. **Vector similarity search** - Rejected: Requires embedding sessions, adds latency
2. **Raw message search** - Rejected: Too slow for large journeys
3. **Elasticsearch** - Rejected: Adds infrastructure, PostgreSQL sufficient for scale

---

## Technology Validation

| Component | Status | Notes |
|-----------|--------|-------|
| asyncpg | ✓ Exists | Used in mcp/server.py |
| PostgreSQL | ✓ Exists | schema.sql, docker-compose |
| pg_trgm | ✓ Exists | Extension enabled |
| pydantic | ✓ Exists | Used in api/routers/ias.py |
| pytest | ✓ Exists | test.py, pytest.ini |
| MCP SDK | ✓ Exists | mcp/server.py |

---

## Schema Extension Preview

```sql
-- New tables for session continuity (MVP)
CREATE TABLE journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,  -- Always present per clarification
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
    -- thoughtseed_trajectory JSONB - DEFERRED post-MVP
    -- attractor_dynamics_history JSONB - DEFERRED post-MVP
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID REFERENCES journeys(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,  -- NULL if session still active
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    summary TEXT,
    messages JSONB DEFAULT '[]',
    diagnosis JSONB,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE journey_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID REFERENCES journeys(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    title TEXT,
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_journeys_device ON journeys(device_id);
CREATE INDEX idx_sessions_journey ON sessions(journey_id);
CREATE INDEX idx_sessions_created ON sessions(journey_id, created_at);
CREATE INDEX idx_sessions_summary_gin ON sessions USING GIN (to_tsvector('english', summary));
CREATE INDEX idx_journey_docs_journey ON journey_documents(journey_id);
```
