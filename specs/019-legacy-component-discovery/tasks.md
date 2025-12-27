# Tasks: Legacy Component Discovery & Scoring

**Input**: spec.md, plan.md

## Phase 1: Core Extraction (P1)
- [x] T001 Port AST-based component analyzer (awareness/inference/memory pattern detection) into `api/services/discovery_service.py`
- [x] T002 Port strategic value scoring (uniqueness, reusability, framework alignment, dependency burden)
- [x] T003 Implement composite scoring with configurable weights and thresholds

## Phase 2: Interfaces (P1)
- [x] T004 Add smolagent tool that runs discovery and returns top-N candidates with `migration_recommended`
- [x] T005 Add FastAPI endpoint `POST /api/v1/discovery/run` returning structured results
- [x] T006 Add CLI wrapper (scripts or `api/cli`) to run discovery against a path and emit JSON/table`

## Phase 3: Insights & Logging (P2)
- [x] T007 Surface enhancement opportunities and risk factors in responses
- [x] T008 Add structured logging with trace ids for discovery runs
- [x] T009 Wire config (weights, thresholds, max files) via env/settings

## Phase 4: Testing (P1)
- [x] T010 Add pytest fixture repo and golden output assertions
- [x] T011 Test threshold gating (migration_recommended toggles)
- [x] T012 Test tool/endpoint contract shapes

## Phase 5: Docs (P3)
- [x] T013 Add README/docs snippet showing smolagent tool + API usage
