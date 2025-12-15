# Quickstart: Session Continuity

**Date**: 2025-12-15
**Prerequisites**: Docker, Python 3.11+, running PostgreSQL instance

## Setup

### 1. Apply Schema Migration

```bash
# Connect to database
docker exec -i dionysus-postgres psql -U dionysus -d dionysus

# Run migration
docker exec -i dionysus-postgres psql -U dionysus -d dionysus < migrations/001_session_continuity.sql
```

### 2. Verify Tables Created

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('journeys', 'sessions', 'journey_documents');
```

Expected output:
```
     table_name
--------------------
 journeys
 sessions
 journey_documents
```

## Usage Examples

### MCP: Create or Get Journey

```python
# Via MCP client
result = await mcp_client.call_tool(
    "get_or_create_journey",
    {"device_id": "550e8400-e29b-41d4-a716-446655440000"}
)
# Returns: {"journey_id": "...", "is_new": true, "session_count": 0}
```

### MCP: Query Journey History

```python
# Search for sessions about "goals"
result = await mcp_client.call_tool(
    "query_journey_history",
    {
        "journey_id": "550e8400-e29b-41d4-a716-446655440000",
        "query": "goals",
        "limit": 5
    }
)
# Returns: {"sessions": [...], "total_results": 3}
```

### MCP: Add Document to Journey

```python
# Link a WOOP plan to journey
result = await mcp_client.call_tool(
    "add_document_to_journey",
    {
        "journey_id": "550e8400-e29b-41d4-a716-446655440000",
        "document_type": "woop_plan",
        "title": "Morning Routine WOOP",
        "content": "Wish: Wake up at 6am..."
    }
)
# Returns: {"document_id": "...", "created_at": "..."}
```

### API: Session with Journey Integration

```bash
# Create session with device_id header (automatically links to journey)
curl -X POST http://localhost:8000/ias/session \
  -H "X-Device-Id: 550e8400-e29b-41d4-a716-446655440000"

# Response includes journey_id and is_new_journey flag
# {"session_id": "...", "journey_id": "...", "created_at": "...", "is_new_journey": true}

# Query journey history via /recall endpoint
curl -G http://localhost:8000/ias/recall \
  -H "X-Device-Id: 550e8400-e29b-41d4-a716-446655440000" \
  --data-urlencode "query=goals"

# Generate WOOP plan (auto-saved to journey)
curl -X POST http://localhost:8000/ias/woop \
  -H "X-Device-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"wish": "Exercise daily", "outcome": "Better health", "obstacle": "Tired after work"}'
```

## Validation Checklist

After implementation, verify:

- [ ] `get_or_create_journey` returns existing journey for same device_id
- [ ] `get_or_create_journey` creates new journey for new device_id
- [ ] `query_journey_history` returns sessions matching keyword
- [ ] `query_journey_history` filters by date range
- [ ] `add_document_to_journey` creates document linked to journey
- [ ] Session creation automatically links to journey
- [ ] Journey timeline shows sessions and documents interleaved by date

## Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Journey creation | <50ms | Time from request to response |
| History query (100 sessions) | <200ms | Time with keyword search |
| Document add | <30ms | Time from request to response |

## Troubleshooting

### "Journey not found" error
```sql
-- Check journey exists
SELECT * FROM journeys WHERE id = 'your-journey-id';
```

### Slow history queries
```sql
-- Check GIN index exists
\d sessions
-- Look for: idx_sessions_summary_gin
```

### Missing sessions in timeline
```sql
-- Verify FK constraint
SELECT s.id, s.journey_id, j.id as journey_exists
FROM sessions s
LEFT JOIN journeys j ON s.journey_id = j.id
WHERE j.id IS NULL;
-- Should return 0 rows
```
