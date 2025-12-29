# Feature Specification: Self-Healing Resilience (Plan B Strategies)

**Feature Branch**: `feature/034-self-healing-resilience`
**Status**: In-Progress
**Input**: Resilience feedback from core refactor. Enable the "Fleet" to run autonomously without breaking on minor tool failures.

## Overview
Dionysus 3 currently handles errors by stopping and reporting them. This feature implements autonomous "Plan B" logic, allowing agents to detect failures (timeouts, empty results, parsing errors) and pivot to alternative strategies without human intervention.

## User Scenarios & Testing

### User Story 1 - Search Fallback (Priority: P1)
As an agent, if my high-fidelity semantic search returns no results, I want to automatically fall back to a broad keyword search or attractor basin probe, so I don't give up on the task.

**Independent Test**: Mock a semantic search to return empty. Verify the agent automatically issues a secondary `keyword_search` or `basin_probe`.

### User Story 2 - Retry with Metaplasticity (Priority: P1)
As the system, if a Docker sandbox times out, I want to automatically retry the task once with an increased `max_steps` budget and a higher-tier model (e.g., Nano -> Mini).

**Independent Test**: Trigger a timeout in a sub-agent. Verify the orchestrator retries the call with adjusted parameters.

## Functional Requirements
- **FR-034-001**: Implement a `ResilienceWrapper` that intercepts tool errors and provides "Strategy Hints" to the agent.
- **FR-034-002**: Define a "Strategy Hierarchy" for core operations (Search, Ingest, Extraction).
- **FR-034-003**: Integrate with `MetaplasticityService` to "heat up" the agent (more steps, better model) after a failure.
- **FR-034-004**: Implement "Silent Healing": log the recovery event but don't bother the orchestrator unless the Plan B also fails.

## Success Criteria
- **SC-001**: System successfully completes a task even after an initial tool failure.
- **SC-002**: Zero "API Hangs" due to tool recursion; all retries are bounded.
- **SC-003**: Provenance records both the failure and the successful recovery path.
