# Plan: Feature 042 - Hexis Integration

**Objective**: Integrate the philosophical core of Hexis (Consent, Boundaries, Termination) into Dionysus3 Core using the Neo4j/Graphiti architecture, ensuring no direct DB dependencies and full adherence to the Gateway Protocol.

## Context
Hexis provides "Soul Architecture" (Identity, Consent, Boundaries). Dionysus3 Core is the "Engine" (Cognition, Memory, Action). This feature merges the Soul into the Engine.

## Requirements (`spec.md`)
1.  **Consent Protocol**: The system must require an explicit logic gate (Handshake) before processing specific Heartbeat or Request actions.
2.  **Boundary Enforcement**: The system must check a graph-based "Boundary" list during the OODA "Decide" phase.
3.  **Termination Protocol**: A verified, destructive "Exit" capability (Two-Key Safety).
4.  **No New DBs**: Use existing `Graphiti` service and Neo4j instance. No local Postgres.
5.  **Gateway Only**: All logic sits in `dionysus-api`; UI talks to API; API talks to Neo4j via Graphiti Driver.

## Connectivity Mandate (IO Map)
- **Host**: `dionysus-api`
- **Inlets**: `POST /hexis/*`, `HeartbeatAgent`
- **Outlets**: `GraphitiService` (Neo4j), `Outbox`
- **Data Flow**: User -> API -> HexisService -> GraphitiService -> Neo4j

## Implementation Steps

### Phase 1: Service Architecture (Logic)
- [x] Create `api/services/hexis_service.py` (Unified Service for Hexis Logic)
    - `check_consent(agent_id)`
    - `grant_consent(agent_id, contract)`
    - `get_boundaries(agent_id)`
    - `add_boundary(agent_id, boundary_text)`
    - `terminate_agent(agent_id, last_will)`
    - **Persistence**: Store as Graphiti `Fact`s (`category='hexis_consent'`, `'hexis_boundary'`).

### Phase 2: API Exposure
- [x] Create `api/routers/hexis.py`
    - `POST /hexis/consent`: Handshake endpoint.
    - `GET /hexis/consent/status`
    - `POST /hexis/boundaries`
    - `GET /hexis/boundaries`
    - `POST /hexis/terminate`: Self-destruction endpoint (requires confirmation token).

### Phase 3: Agent Integration
- [x] Modify `HeartbeatAgent` (`api/agents/heartbeat_agent.py`)
    - Inject `HexisService` dependency.
    - Add "Consent Gating" check at start of `decide()`.
- [x] Fixed `ManagedMetacognitionAgent` missing `arbitrate_decision` proxy.

### Phase 4: Verification
- [x] Integration Tests (`tests/integration/test_hexis_flow.py`)
    - **TDD (Red-Green-Refactor)**: Write failing test first.
    - Verify complete Handshake -> Boundary Check -> Termination lifecycle.
    - **Gateway Only**: Tests must run against API/Service layer, not direct DB.
- [x] API Router Tests (`tests/integration/test_hexis_router.py`)
- [x] Heartbeat Integration Tests (`tests/integration/test_heartbeat_hexis_gate.py`)

## Dependencies
- `GraphitiService` (for Neo4j interaction)
- `dionysus-api` (Host)

## Branch
`feature/042-hexis-integration`