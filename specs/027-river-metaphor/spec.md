# Feature Specification: River Metaphor Flow Analysis

**Feature Branch**: `027-river-metaphor`  
**Status**: Draft  
**Input**: Port the "River Metaphor" context engineering from Dionysus 2.0 to enhance Dionysus 3's metacognition.

## Overview
Dionysus 2.0 used a "River Metaphor" to describe information flow (Emerging, Flowing, Converging, Stable, Turbulent). In Dionysus 3, we port this logic into the `MetacognitionAgent` to allow the system to evaluate its own "Thought Stream" quality.

## User Scenarios & Testing

### User Story 1 - Flow State Detection (Priority: P1)
As an operator, I want the system to detect when its reasoning has become "Turbulent," so I can intervene or trigger a "Cool Down" cycle.

**Independent Test**: Simulate a series of conflicting agent decisions. Verify that the `MetacognitionAgent` emits a `FlowState:Turbulent` signal in the monitoring dashboard.

## Functional Requirements
- **FR-001**: Implement the `FlowState` enum: EMERGING, FLOWING, CONVERGING, STABLE, TURBULENT.
- **FR-002**: Create a `ContextStream` service that calculates "Information Density" and "Turbulence Level" based on recent Graphiti episodes.
- **FR-003**: Expose a `/api/monitoring/flow` endpoint that returns the current "River" status of the system.

## Success Criteria
- **SC-001**: System can distinguish between a "Flowing" state (productive tasks) and a "Turbulent" state (high error rates).
- **SC-002**: The `MetacognitionAgent` uses Flow State to adjust the `max_steps` or `model_id` of hierarchical agents.
