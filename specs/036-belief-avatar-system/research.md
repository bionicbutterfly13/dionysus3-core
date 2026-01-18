# Research: Belief Avatar System

**Feature**: 036-belief-avatar-system
**Date**: 2025-12-30

## Research Tasks

### 1. Router Patterns in Codebase

**Decision**: Follow existing FastAPI router patterns from `api/routers/avatar.py` and `api/routers/ias.py`

**Rationale**: Consistency with existing codebase ensures maintainability and familiar patterns for future developers.

**Key Patterns Identified**:
- Router prefix: `/belief-journey` (follows `/avatar`, `/ias` convention)
- Tags for OpenAPI grouping: `["belief-journey"]`
- Request/Response Pydantic models defined at top of file
- Singleton service access via `get_*_service()` functions
- HTTPException for 404/400 errors with descriptive detail
- Health endpoint at `/health` returning status dict

**Alternatives Considered**:
- Class-based views: Rejected - not used in this codebase
- APIRouter subclassing: Rejected - unnecessary complexity

### 2. UUID Handling in FastAPI

**Decision**: Use `UUID` type annotation from `uuid` module directly in path parameters

**Rationale**: FastAPI automatically validates UUID format, returning 422 for invalid UUIDs.

**Pattern**:
```python
from uuid import UUID

@router.get("/journey/{journey_id}")
async def get_journey(journey_id: UUID):
    ...
```

**Alternatives Considered**:
- String validation with regex: Rejected - UUID type provides this automatically
- Custom validator: Rejected - overkill for standard UUID handling

### 3. Error Handling Patterns

**Decision**: Use HTTPException with standard status codes

**Rationale**: Consistent with existing routers, provides clear client feedback.

**Patterns**:
```python
# 404 for not found
raise HTTPException(status_code=404, detail="Journey not found")

# 400 for validation/business logic errors
raise HTTPException(status_code=400, detail="Belief not in this journey")

# 500 caught by global handler, log and re-raise
```

**Error Response Structure**:
```json
{
  "success": false,
  "detail": "Error message here"
}
```

### 4. Skills Library Format

**Decision**: Markdown files with YAML frontmatter for metadata

**Rationale**: Human-readable, version-controllable, compatible with existing skills patterns.

**Location**: `/Volumes/Asylum/skills-library/personal/bionicbutterfly13/consciousness/`

**Structure**:
```markdown
---
name: avatar-simulation
version: 1.0.0
description: Simulate [LEGACY_AVATAR_HOLDER] avatar experience
triggers:
  - simulate avatar
  - avatar roleplay
  - claudia experience
---

# Avatar Simulation Skill

[Skill content and instructions...]
```

**Alternatives Considered**:
- JSON/YAML only: Rejected - less readable for complex instructions
- Python modules: Rejected - skills-library uses markdown format

### 5. Service Integration Pattern

**Decision**: Import singleton getter from service module

**Rationale**: Matches existing pattern in `api/routers/avatar.py`

**Pattern**:
```python
from api.services.belief_tracking_service import get_belief_tracking_service

@router.post("/journey/create")
async def create_journey(request: CreateJourneyRequest):
    service = get_belief_tracking_service()
    journey = await service.create_journey(request.participant_id)
    return {"success": True, "data": journey.model_dump()}
```

### 6. Response Structure

**Decision**: Wrap responses in `{"success": True, "data": ...}` structure

**Rationale**: Consistent with `api/routers/avatar.py` pattern, allows uniform error handling.

**Success Response**:
```json
{
  "success": true,
  "data": { ... }
}
```

**Error Response**:
```json
{
  "detail": "Error message"
}
```

---

## Resolved Clarifications

All technical context items resolved through codebase research. No external research required.

| Item | Resolution |
|------|------------|
| Router patterns | Follow avatar.py/ias.py conventions |
| UUID handling | Native UUID type in path params |
| Error handling | HTTPException with 400/404/500 |
| Skills format | Markdown with YAML frontmatter |
| Service access | Singleton getter pattern |
| Response format | `{success, data}` wrapper |
