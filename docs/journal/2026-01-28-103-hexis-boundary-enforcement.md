# 2026-01-28: Hexis Boundary Enforcement + Termination Removal

**Feature:** 103-hexis-boundary-enforcement
**Author:** Mani Saint-Victor, MD (via Codex)
**Status:** In Progress (feature branch)

## The Why
Hexis boundaries were stored but not enforced, and self-termination endpoints conflicted with safe-by-default governance. This update hardens boundary enforcement in the Heartbeat decision loop and removes the self-end feature entirely.

## The What
- **Boundary enforcement in Heartbeat:** Boundaries are injected into System 1/System 2 prompts and a hard post-check blocks violations.
- **Hexis boundary evaluation:** Boundaries are mapped to PriorConstraint rules (BASAL/PROHIBIT). `regex:` prefix enables explicit matching.
- **Termination removal:** `/hexis/terminate` and `/hexis/terminate/confirm` endpoints and service methods removed.

## The How
- **Code:**
  - `api/agents/heartbeat_agent.py` (boundary injection + post-check)
  - `api/services/hexis_service.py` (boundary fetch + constraint evaluation)
  - `api/routers/hexis.py` (termination endpoints removed)
- **Tests:**
  - `tests/integration/test_heartbeat_hexis_gate.py`
  - `tests/integration/test_hexis_flow.py`
  - `tests/integration/test_hexis_router.py`
  - `tests/contract/test_hexis_api.py`

## Notes
- For reliable enforcement, prefer boundaries that begin with `regex:` (e.g., `regex:delete\s+.*data`).
