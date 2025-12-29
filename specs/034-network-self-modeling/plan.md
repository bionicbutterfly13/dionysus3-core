# Implementation Plan: Network Reification and Self-Modeling

**Branch**: `034-network-self-modeling` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/034-network-self-modeling/spec.md`

## Summary

Implement neuroscience-grounded self-modeling capabilities for cognitive agents based on Treur's research. This feature adds four purely additive components: (1) NetworkState model for observable W/T/H values, (2) Self-prediction auxiliary task for agent regularization, (3) Hebbian learning dynamics for knowledge graph relationships, (4) Role matrix specification stored in Neo4j. All components are opt-in via configuration flags with zero impact on existing functionality.

## Technical Context

**Language/Version**: Python 3.11+ (async/await, Pydantic v2)
**Primary Dependencies**: FastAPI, smolagents, Pydantic v2, Graphiti (Neo4j access)
**Storage**: Neo4j via n8n webhooks (network states, role matrices, Hebbian weights)
**Testing**: pytest with async support, contract tests for API endpoints
**Target Platform**: Linux server (VPS), Docker deployment
**Project Type**: Single monolithic API with modular services
**Performance Goals**: 100ms network state queries for ≤1000 connections (SC-001)
**Constraints**: Neo4j access via webhooks only (except Graphiti), RBAC from existing audit system
**Scale/Scope**: ~10-50 snapshots/day/agent, 30-day retention for historical reconstruction

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Non-Breaking Design | ✅ PASS | All components additive, opt-in via flags |
| Existing Test Preservation | ✅ PASS | SC-009, SC-010 explicitly require zero regression |
| Neo4j Access Rules | ✅ PASS | Uses webhooks + Graphiti (approved exception) |
| RBAC Compliance | ✅ PASS | Same access as audit logs (clarified) |

**No violations requiring justification.**

## Project Structure

### Documentation (this feature)

```text
specs/034-network-self-modeling/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
api/
├── models/
│   ├── network_state.py      # NEW: NetworkState, SelfModelState, TimingState
│   ├── hebbian.py            # NEW: HebbianConnection model
│   ├── role_matrix.py        # NEW: RoleMatrix graph structure types
│   └── prediction.py         # NEW: PredictionRecord for self-modeling
├── services/
│   ├── network_state_service.py    # NEW: NetworkState CRUD, snapshots
│   ├── self_modeling_service.py    # NEW: Self-prediction auxiliary task
│   ├── hebbian_service.py          # NEW: Hebbian weight updates
│   ├── role_matrix_service.py      # NEW: Role matrix Neo4j operations
│   └── metaplasticity_service.py   # EXTEND: Add second-order H states
├── routers/
│   └── network_state.py      # NEW: REST endpoints for network state queries

tests/
├── unit/
│   ├── test_network_state.py
│   ├── test_hebbian.py
│   ├── test_role_matrix.py
│   └── test_self_modeling.py
├── integration/
│   └── test_network_state_neo4j.py
└── contract/
    └── test_network_state_api.py
```

**Structure Decision**: Follows existing api/ structure. New models/services added alongside existing ones. No modifications to existing files except extending metaplasticity_service.py with optional second-order states.

## Complexity Tracking

> No violations requiring justification. All components additive.

---

## Phase 0: Research

### Research Tasks

1. **Treur Network Dynamics**: Best practices for implementing temporal-causal network equations in Python
2. **Hebbian Learning Implementation**: Standard formulas and decay functions for association learning
3. **Neo4j Graph Patterns**: Optimal schema for role matrix storage (nodes vs. relationship properties)
4. **Snapshot Delta Calculation**: Efficient algorithms for detecting >5% state changes
5. **smolagents Integration**: How to inject auxiliary tasks without modifying core agent loop

### Research Output

See [research.md](./research.md) for detailed findings.

---

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for entity definitions.

### API Contracts

See [contracts/](./contracts/) for OpenAPI specifications.

### Quickstart

See [quickstart.md](./quickstart.md) for implementation guide.
