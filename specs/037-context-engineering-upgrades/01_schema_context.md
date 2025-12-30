# Feature Specification: SchemaContext Implementation

**Feature Branch**: `037-context-engineering-upgrades`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Context-Engineering/06_schema_design.py

## Clarifications

### Session 2025-12-30
- Q: What is the timeout for Schema Validation? → A: 5s Timeout (GPT-5 Nano is fast).
- Q: How should schemas be defined? → A: Hybrid Wrapper: Define models in Pydantic, but wrap them in `SchemaContext` for LLM interaction and validation logic.

## User Scenarios & Testing

### User Story 1 (US1) - Reliable Heartbeat Decisions (Priority: P1)

As the Dionysus system, I want every heartbeat decision to be strictly validated against a schema before execution, so that I never crash due to "prompt drift" or invalid JSON responses from the LLM.

**Why this priority**: Heartbeat reliability is critical. Current manual prompt formatting is fragile and leads to periodic failures.

**Independent Test**:
- Trigger a heartbeat with a mock LLM that returns slightly malformed JSON (e.g. missing quotes).
- The `SchemaContext` should automatically retry with an error message and eventually return a valid object or a structured failure, rather than crashing the service.

**Acceptance Scenarios**:

1. **Given** the HeartbeatService needs a decision, **When** it calls the LLM, **Then** the request is wrapped in `SchemaContext` with strict JSON validation derived from the Pydantic model.
2. **Given** an invalid JSON response from the LLM, **When** `SchemaContext` validates it, **Then** it triggers a retry with the validation error included in the prompt.
3. **Given** a valid response, **When** it is returned, **Then** it is guaranteed to match the `HeartbeatDecision` Pydantic model.

---

## Requirements

### Functional Requirements

- **FR-001**: Implement `SchemaContext` class based on `Context-Engineering` reference, supporting validation loops and schema-augmented prompts.
- **FR-002**: Define `HeartbeatDecision` as a strict `JSONSchema` (or Pydantic model exportable to JSONSchema).
- **FR-003**: Refactor `HeartbeatService._make_decision` to use `SchemaContext.query()` instead of raw `chat_completion`.
- **FR-004**: The system MUST support configurable retries (default: 3) and a **5s timeout** per attempt.
- **FR-005**: `SchemaContext` MUST accept a Pydantic model class in its constructor and automatically extract the JSON schema using `.model_json_schema()`.

### Key Entities

- **SchemaContext**: A wrapper around the LLM client that enforces JSON Schema validation on outputs.
- **HeartbeatDecision**: The structured output format for OODA loop decisions (ActionPlan, Reasoning, etc.).

## Success Criteria

### Measurable Outcomes

- **SC-001**: Heartbeat decision parsing errors reduced to 0% for standard operation.
- **SC-002**: Retry logic successfully recovers from at least 80% of initial syntax errors without user intervention.
