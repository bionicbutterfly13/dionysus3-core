# Feature Specification: Critical D3 Bug Fixes

**Feature Branch**: `064-critical-d3-fixes`
**Created**: 2026-01-10
**Status**: Draft
**Input**: User description: "Critical D3 refactoring: Fix 3 critical bugs - duplicate endpoint in monitoring.py, Neo4j access violation in ias.py, undefined variables in action_executor.py"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix Undefined Variables in ObserveHandler (Priority: P1)

A developer calling the `ObserveHandler.execute()` method expects it to complete without runtime errors. Currently, the code references undefined variables (`memory_record`, `s`) causing immediate `NameError` crashes.

**Why this priority**: This is a blocking bug - any code path that triggers ObserveHandler will crash the application. Must be fixed first to ensure basic operability.

**Independent Test**: Can be fully tested by calling the Observe action handler and verifying it returns a valid `ActionResult` without throwing `NameError`.

**Acceptance Scenarios**:

1. **Given** a running Dionysus API, **When** the Observe action is executed, **Then** it returns a valid `EnvironmentSnapshot` without runtime errors
2. **Given** the HeartbeatService has state, **When** ObserveHandler accesses energy and heartbeat count, **Then** it uses the pre-fetched values from earlier in the method

**Status**: COMPLETED (fixed in action_executor.py lines 136, 140-141)

---

### User Story 2 - Remove Duplicate Endpoint in Monitoring Router (Priority: P1)

An API consumer accessing `GET /api/monitoring/cognitive` expects consistent behavior. Currently, the endpoint is defined twice, with the second definition overwriting the first and losing the `trace_id` parameter.

**Why this priority**: This causes silent behavioral regression - the API contract is broken without any visible error, making debugging difficult.

**Independent Test**: Can be fully tested by calling `GET /api/monitoring/cognitive` with a `trace_id` parameter and verifying the parameter is properly received and processed.

**Acceptance Scenarios**:

1. **Given** the monitoring router is loaded, **When** OpenAPI spec is generated, **Then** only one definition of `/api/monitoring/cognitive` exists
2. **Given** a request to `/api/monitoring/cognitive` with `trace_id=xyz`, **When** the endpoint is called, **Then** the trace_id parameter is available to the handler

**Status**: COMPLETED (deleted duplicate endpoint in monitoring.py lines 60-72)

---

### User Story 3 - Replace Direct Neo4j Access in IAS Router (Priority: P1)

A system administrator expects all database access to go through approved patterns (Graphiti service or n8n webhooks). Currently, `ias.py` constructs raw Cypher queries and executes them directly, violating the architectural constraint.

**Why this priority**: This violates CLAUDE.md prohibition on direct Neo4j access. Must be fixed to maintain data integrity, security, and audit trail requirements.

**Independent Test**: Can be fully tested by running a grep for direct Neo4j imports/patterns in the router and verifying IAS operations still function correctly via Graphiti.

**Acceptance Scenarios**:

1. **Given** the IAS router code, **When** searching for direct Cypher query construction, **Then** no raw Cypher strings are found outside of Graphiti service
2. **Given** a session update request to IAS, **When** the update is processed, **Then** it persists via Graphiti service or n8n webhook (not direct Neo4j)
3. **Given** the codebase, **When** running `grep -r "execute_query" api/routers/ias.py`, **Then** no direct driver calls are found

**Status**: COMPLETED (rewrote update_persistent_session() to use Graphiti service)

---

### Edge Cases

- What happens when `HeartbeatService.get_current_state()` returns None or raises an exception? (Already handled with fallback defaults)
- How does the system handle monitoring requests when no trace is active? (Should return valid response without trace context)
- What happens when Graphiti service is unavailable during IAS session update? (Should fail gracefully with appropriate error)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST NOT reference undefined variables in any production code path
- **FR-002**: System MUST NOT have duplicate FastAPI endpoint definitions that silently override each other
- **FR-003**: System MUST access Neo4j exclusively through Graphiti service or n8n webhooks (per CLAUDE.md)
- **FR-004**: System MUST maintain all existing API functionality after fixes
- **FR-005**: System MUST pass all existing unit tests after changes

### Key Entities

- **ActionResult**: Return type from action handlers containing status, energy cost, and result data
- **EnvironmentSnapshot**: Data structure containing system state (energy, heartbeat count, memory count, goals)
- **Session**: IAS session entity persisted to Neo4j (now via Graphiti)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero `NameError` exceptions when executing any action handler
- **SC-002**: OpenAPI specification shows exactly one definition per endpoint path
- **SC-003**: Running `grep -r "from neo4j import" api/routers/` returns zero matches
- **SC-004**: Running `grep -r "_driver.execute_query" api/routers/` returns zero matches
- **SC-005**: All existing tests pass (`python -m pytest tests/ -v`)
- **SC-006**: API server starts without errors (`uvicorn api.main:app --reload`)

## Assumptions

- The `recent_memories_count` variable defined at line 103 is the intended source for the snapshot field
- The `current_energy` and `heartbeat_count` variables defined at lines 88-95 are the intended sources for snapshot fields
- The duplicate endpoint in monitoring.py was unintentional and the first definition (with trace_id support) is the correct one
- Graphiti service provides equivalent functionality to direct Neo4j queries for IAS session management

## Scope Boundaries

**In Scope**:
- Fix undefined variables in `action_executor.py` (COMPLETED)
- Remove duplicate endpoint in `monitoring.py`
- Replace direct Neo4j access in `ias.py` with Graphiti service

**Out of Scope**:
- Refactoring other services that may have similar issues
- Adding new features or capabilities
- Performance optimization
- Additional test coverage beyond verifying fixes work
