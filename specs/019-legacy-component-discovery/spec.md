# Feature Specification: Legacy Component Discovery & Scoring

**Feature Branch**: `019-legacy-component-discovery`  \
**Created**: 2025-12-27  \
**Status**: Draft  \
**Input**: Bring Dionysus 2.0 consciousness-aware component discovery and scoring into Dionysus 3 to auto-select refactor targets and align them with smolagents.

## User Scenarios & Testing

### User Story 1 - Consciousness Pattern Detection (Priority: P1)
As a maintainer, I want automated scanning of legacy repos for awareness/inference/memory patterns, so I can quickly identify which modules should become smolagent tools or agents.

**Independent Test**: Run `discover` against Dionysus-2.0 path and receive a list of components tagged with consciousness patterns and composite quality scores.

### User Story 2 - Strategic Value Scoring (Priority: P1)
As a maintainer, I want strategic value signals (uniqueness, reusability, framework alignment) per component, so I can prioritize high-value ports first.

**Independent Test**: For a known high-value file, the assessment returns `migration_recommended=True` with composite score ≥ configured threshold.

### User Story 3 - Enhancement/Risk Surfacing (Priority: P2)
As a maintainer, I want auto-suggested enhancement opportunities and risk flags, so I can plan refactors with minimal manual triage.

**Independent Test**: A component with memory hooks surfaces `memory_system_enhancement` opportunity and dependency-heavy modules emit `high_dependency_complexity` risk.

## Requirements

### Functional Requirements
- **FR-001**: Provide a CLI command (or smolagent tool) to scan a codebase path and emit `ConsciousnessComponent` objects with awareness/inference/memory pattern detection (AST-based) and strategic indicators.
- **FR-002**: Compute composite scores with configurable weights (`consciousness_weight`, `strategic_weight`) and a quality threshold to gate `migration_recommended`.
- **FR-003**: Emit enhancement opportunities (e.g., awareness amplification, active inference integration, memory system enhancement) and risk factors (e.g., dependency burden, low compatibility).
- **FR-004**: Persist or return structured results consumable by other specs (migration pipeline, DAEDALUS pool) and log via structured logging.
- **FR-005**: Integrate with smolagents by exposing a tool that can run discovery and return top-N candidates for agent-led refactor plans.

### Success Criteria
- **SC-001**: Discovery run over Dionysus-2.0 produces ≥1 recommended component with composite score ≥ threshold and non-empty consciousness patterns.
- **SC-002**: At least one enhancement opportunity and one risk factor are present for qualifying components.
- **SC-003**: Output is available both via CLI/API and as a smolagent tool invocation.

## Implementation Notes (Progress)
- Discovery engine lives in `api/services/discovery_service.py` with trace logging.
- Interfaces delivered: smolagent tool `discover_components`, FastAPI route `POST /api/discovery/run`, CLI `scripts/discover_legacy_components.py`.
- Tests in `tests/test_discovery_service.py`; live run against D2.0 produces ranked candidates.
