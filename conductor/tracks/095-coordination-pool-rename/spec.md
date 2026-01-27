# Specification: Coordination Pool Rename & Refactor

**Track ID**: 095-coordination-pool-rename
**Date**: 2026-01-27
**Author**: Mani Saint-Victor, MD

## Overview

The "Coordination Pool" (Feature 020) provides a background worker system for multi-agent tasks. To align with established cognitive architecture metaphors (The River, The Boardroom), the terminology should be refactored.

## Requirements

- **FR-001**: Rename "Coordination Pool" to "Agent Fleet" or "Boardroom Pool" (to be decided). Let's go with **"Agent Fleet"** for the HOT worker tier.
- **FR-002**: Refactor `api/services/coordination_service.py` and related models.
- **FR-003**: Update all delegation documentation.
- **FR-004**: Ensure backward compatibility via aliases if necessary (transition phase).
- **FR-005**: Align task types with OODA phases (Research, Design, Execute, Audit).

## Constraints

- **SC-001**: Zero downtime for API endpoints (keep old names as aliases).
- **SC-002**: Standardize on `fleet_` prefix instead of `coordination_`.
- **SC-003**: Maintain isolation guarantees.

## Success Criteria

1. Codebase uses `AgentFleet` terminology for background workers.
2. API endpoints are versioned or aliased (`/api/v1/fleet` instead of `/api/v1/coordination`).
3. Documentation (Quartz) reflects the new naming convention.