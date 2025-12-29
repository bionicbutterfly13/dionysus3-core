# Tasks: River Metaphor Flow Analysis

**Input**: spec.md
**Status**: Pending

## Phase 1: Foundation (P1)
- [ ] T001 Implement `FlowState` enum (EMERGING, FLOWING, CONVERGING, STABLE, TURBULENT) in `api/models/cognitive.py` (FR-001)
- [ ] T002 Create `ContextStream` service to calculate "Information Density" and "Turbulence Level" in `api/services/context_stream.py` (FR-002)

## Phase 2: Interfaces (P1)
- [ ] T003 Expose `GET /api/monitoring/flow` endpoint in `api/routers/monitoring.py` (FR-003)

## Phase 3: Integration (P2)
- [ ] T004 Integrate `FlowState` detection into `MetacognitionAgent` for dynamic `max_steps` adjustment (SC-002)

## Phase 4: Testing (P2)
- [ ] T005 Unit tests for turbulence calculation
- [ ] T006 Integration test for flow state adjustment in OODA loop
