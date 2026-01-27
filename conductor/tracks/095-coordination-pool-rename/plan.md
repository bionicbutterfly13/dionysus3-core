# Implementation Plan: Coordination Pool Rename & Refactor

**Track ID**: 095-coordination-pool-rename
**Status**: Active
**Spec**: [spec.md](./spec.md)

## Phase 1: Models & Constants (P0)

- [ ] **Task 1.1**: Update `api/models/coordination.py` to include `Fleet` aliases.
- [ ] **Task 1.2**: Standardize `TaskType` to include OODA-aligned phases.
- [ ] **Task 1.3**: Add `FleetStatus` model.

## Phase 2: Service Refactor (P0)

- [ ] **Task 2.1**: Refactor `api/services/coordination_service.py` -> `api/services/agent_fleet_service.py`.
- [ ] **Task 2.2**: Rename `CoordinationService` class to `AgentFleetService`.
- [ ] **Task 2.3**: Update `get_coordination_service` to provide the renamed instance.
- [ ] **Task 2.4**: Implement `fleet_` prefixed methods.

## Phase 3: Router & API (P1)

- [ ] **Task 3.1**: Create `api/routers/fleet.py` mirroring `coordination.py`.
- [ ] **Task 3.2**: Add deprecation warnings to `/api/v1/coordination` endpoints.
- [ ] **Task 3.3**: Update `api/main.py` to include the new router.

## Phase 4: Documentation & Cleanup (P2)

- [ ] **Task 4.1**: Update Quartz concept pages.
- [ ] **Task 4.2**: Update `CLAUDE.md` architecture section.
- [ ] **Task 4.3**: Update `AGENTS.md` delegation instructions.

## Testing Strategy

- [ ] **T1**: Unit tests for `AgentFleetService`.
- [ ] **T2**: Contract tests for `/api/v1/fleet`.
- [ ] **T3**: Integration tests verifying OODA-to-Fleet delegation.