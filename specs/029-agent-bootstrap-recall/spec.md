# Feature Specification: Agent Bootstrap Recall

**Feature Branch**: `029-agent-bootstrap-recall`  
**Created**: 2025-12-27  
**Status**: Draft  
**Input**: Automatically recall relevant memories from the graph knowledge at the beginning of each agent session to reduce cognitive cold-start and ensure grounding.

## Clarifications

### Session 2025-12-27
- Q: Where should the bootstrap recall logic reside? → A: ConsciousnessManager Orchestration
- Q: How should large recall payloads be handled? → A: LLM Summarization
- Q: Which retrieval mechanism should be used? → A: Hybrid (Vector Search + Graphiti)
- Q: What is the scope of recalled memories? → A: Project-Scoped (Current `project_id` only)
- Q: How is the bootstrap recall configured? → A: Request-Level (via `submit_task` payload)

## User Scenarios & Testing

### User Story 1 - Automated Session Grounding (Priority: P1)
As an agent, I want to automatically receive the most relevant past memories and latest state trajectories when I start a task, so I can act immediately with full context without manual recall calls.

**Why this priority**: Eliminates "cognitive cold-start" where agents ignore critical project history because they weren't explicitly told to search for it.

**Independent Test**: Start a new OODA cycle with a known historical context in the graph; verify that the initial `orchestrator_log` or `initial_context` contains a "## Past Context" block before any agent tools are invoked.

**Acceptance Scenarios**:
1. **Given** a user prompt about "Feature 020", **When** the OODA cycle starts, **Then** the ConsciousnessManager automatically injects Feature 020's implementation summary into the context.
2. **Given** an empty graph, **When** the OODA cycle starts, **Then** the agent receives a "No relevant past context found" notification but proceeds normally.

### User Story 2 - Temporal Continuity (Priority: P2)
As the system, I want to see the last 3-5 successful trajectories (episodic memories) injected into every session start, so I have a sense of "what just happened."

**Why this priority**: Provides longitudinal continuity across discrete API calls/sessions.

**Independent Test**: Run two consecutive tasks; verify the second task's initial context contains a summary of the first task's results.

## Requirements

### Functional Requirements
- **FR-001**: The `ConsciousnessManager` MUST perform an automatic semantic search against the memory store (VectorSearchService) for the current `project_id` using the user's initial prompt as the query.
- **FR-002**: The system MUST query Graphiti to fetch the last 3-5 successful episodic trajectories for the current `project_id` to ensure temporal grounding.
- **FR-003**: All retrieved memories MUST be formatted into a standard `## Past Context` Markdown block.
- **FR-004**: This block MUST be injected into the `initial_context` passed to the managed agents.
- **FR-005**: The bootstrap recall MUST be configurable via a boolean flag in the task payload (e.g., `bootstrap_recall: true/false`).

### Edge Cases
- **Large Recall Payload**: If the retrieved context exceeds a safe token limit (e.g., 2000 tokens), it MUST be summarized using Claude HAIKU (via api.services.claude) before injection.
- **Service Timeout**: If the memory store (vector search) is slow, the bootstrap recall MUST time out after 2 seconds to avoid blocking the agent start.

## Success Criteria

### Measurable Outcomes
- **SC-001**: 100% of agent sessions start with a "Past Context" block if relevant data exists in the graph.
- **SC-002**: Average "time-to-first-action" for agents is reduced because they don't need to spend the first OODA step on manual recall.
- **SC-003**: 0 instances of agents "hallucinating" or re-implementing existing features because they missed previous context.