# Feature Specification: Heartbeat Agent Handoff

**Feature Branch**: `010-heartbeat-handoff`  
**Created**: 2025-12-26  
**Status**: Draft  
**Input**: User description: "Hand off OODA loop from procedural HeartbeatService to autonomous smolagents.CodeAgent orchestration."

## User Scenarios & Testing

### User Story 1 - Autonomous OODA Execution (Priority: P1)

As a cognitive system, I want to manage my own decision cycle using reasoning rather than fixed logic, so that I can adapt to complex environmental changes.

**Why this priority**: Core shift from procedural to agentic control. This is the primary goal of Dionysus 3.0.

**Independent Test**: Trigger a manual heartbeat and verify via logs that the `HeartbeatAgent` (CodeAgent) reasoned about its state and selected tools to execute its plan.

**Acceptance Scenarios**:

1. **Given** an active heartbeat cycle, **When** energy is sufficient, **Then** the agent executes a multi-step plan using at least two different cognitive tools.
2. **Given** low energy (< 2.0), **When** a heartbeat is triggered, **Then** the agent decides to REST to conserve energy.

---

### User Story 2 - Trajectory-Aware Reasoning (Priority: P2)

As a cognitive system, I want to reason over my recent agent trajectories (experiences), so that I can learn from previous successes and failures in real-time.

**Why this priority**: Enables short-term learning and context-aware behavior.

**Independent Test**: Ingest a trajectory, trigger a heartbeat, and verify the agent's "Orientation" mentions the specific outcome of the previous trajectory.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST delegate the DECIDE and ACT phases of the OODA loop EXCLUSIVELY to a `smolagents.CodeAgent`. Legacy procedural fallback logic MUST be removed.
- **FR-002**: Agent MUST have access to the following MCP tools: `semantic_recall`, `reflect_on_topic`, `synthesize_information`, and `manage_energy`.
- **FR-003**: System MUST provide the agent with a comprehensive context snapshot (Energy, Goals, Memories, Trajectories).
- **FR-004**: Agent MUST be able to prioritize goals based on current environmental urgency.
- **FR-005**: Model IDs MUST be configurable via environment variables (`SMOLAGENTS_MODEL`) and default to `openai/gpt-5-nano-2025-08-07`.

## Key Entities

- **HeartbeatAgent**: The smolagents CodeAgent instance.
- **CognitiveContext**: The unified data structure passed to the agent.
- **HeartbeatLog**: Persistent record of agent reasoning and tool usage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of heartbeat cycles are successfully managed by the agent without procedural fallback.
- **SC-002**: Average cycle reasoning time is under 15 seconds.
- **SC-003**: Agent successfully completes at least one "active" goal per 5 heartbeat cycles.