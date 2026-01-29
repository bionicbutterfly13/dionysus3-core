# Plan: Feature 103 - Hexis Boundary Enforcement + Termination Removal

**Objective**: Enforce Hexis boundaries during Heartbeat decision and remove the self-termination feature from the API/service layer.

## Requirements
1. **No sprawl**: Reuse existing Hexis service + prior constraint stack; no new entrypoints.
2. **Gateway compliance**: All memory reads/writes use GraphitiService; no direct DB.
3. **Boundary enforcement**: Boundaries must gate Heartbeat decisions with a hard block on violation.
4. **Remove self-end**: `/hexis/terminate` endpoints and termination service behavior removed.
5. **TDD**: Red → Green → Refactor with tests for boundary enforcement and termination removal.

## Integration (IO Map)
- **Inlets**:
  - `api/agents/heartbeat_agent.py` (decision gating)
  - `api/services/hexis_service.py` (boundary retrieval + evaluation)
  - `api/routers/hexis.py` (termination endpoints removed)
- **Outlets**:
  - `PriorConstraintService` (constraint evaluation)
  - `GraphitiService.search()` (boundary retrieval)

## Tasks
- [~] Add boundary enforcement in Heartbeat (prompt injection + hard post-check) (CLAIMED: Codex-1)
- [ ] Remove termination endpoints + service methods (self-end feature)
- [ ] Add/adjust tests for boundary enforcement and termination removal
- [ ] Update docs if required (journal entry after completion)

## Branch
`feature/103-hexis-boundary-enforcement`
