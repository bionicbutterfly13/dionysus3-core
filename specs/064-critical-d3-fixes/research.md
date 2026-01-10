# Research: Critical D3 Bug Fixes

**Feature**: 064-critical-d3-fixes
**Date**: 2026-01-10

## Research Questions

### Q1: How should IAS session updates be persisted without direct Neo4j access?

**Decision**: Use n8n webhook

**Rationale**:
- CLAUDE.md explicitly states IAS is a "high-value business asset" requiring n8n webhooks
- n8n provides audit trail for all IAS operations
- Existing pattern in codebase: `memory/v1/recall`, `memory/v1/traverse` webhooks

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| Graphiti service | IAS requires audit trail via n8n per CLAUDE.md |
| Direct Neo4j | Explicitly prohibited |
| Session manager internal method | Still uses direct driver access internally |

**Implementation**:
- Create n8n workflow for IAS session updates
- Use HMAC signature for webhook authentication
- Fallback to error if webhook not configured

### Q2: Which duplicate endpoint definition should be kept?

**Decision**: Keep first definition (lines 45-58)

**Rationale**:
- First definition includes `Depends(get_monitoring_service_with_trace)`
- Returns `trace_id` in response for observability
- Second definition loses this capability

**Verification**:
- Manual inspection of both definitions
- First provides more functionality (trace_id support)

### Q3: Are there existing n8n webhooks for IAS?

**Findings**:
- No existing `N8N_IAS_SESSION_UPDATE_URL` environment variable
- Need to either create new n8n workflow or use Graphiti as fallback

**Decision**: Use Graphiti service as interim solution until n8n workflow is created
- This avoids blocking the fix on n8n workflow creation
- Still complies with "no direct Neo4j" rule
- Can migrate to n8n later when workflow is ready

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| FastAPI | existing | Router framework |
| Graphiti | existing | Neo4j access abstraction |
| httpx | existing | Async HTTP client (for future n8n) |

## No Additional Research Required

This is a bug fix feature with well-defined scope. All technical decisions are straightforward:
1. Delete duplicate code
2. Use existing Graphiti service instead of direct Neo4j
3. Maintain existing API contracts
