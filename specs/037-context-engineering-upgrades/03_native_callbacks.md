# Feature Specification: Native Callback Registry

**Feature Branch**: `037-context-engineering-upgrades`
**Created**: 2025-12-30
**Status**: Draft
**Input**: smolagents/src/smolagents/memory.py

## User Scenarios & Testing

### User Story 1 - Robust Audit Hooks (Priority: P3)

As a developer, I want to attach audit and MoSAEIC capture hooks to agents using the native `CallbackRegistry` pattern, so that my monitoring code doesn't break when agent internals change.

**Why this priority**: Current monkey-patching of `agent.step_callbacks` is fragile and "non-idiomatic" for `smolagents`.

**Independent Test**:
- Register a dummy callback for `ActionStep`.
- Run an agent step.
- Verify the callback was triggered with the correct `step` object and `kwargs`.

**Acceptance Scenarios**:

1. **Given** a `ConsciousnessManager` initialization, **When** listeners are attached, **Then** they use `CallbackRegistry.register()` instead of list assignment.
2. **Given** an agent execution, **When** a step completes, **Then** all registered native callbacks fire correctly.

---

## Requirements

### Functional Requirements

- **FR-001**: Remove custom list assignment for `step_callbacks` in `ConsciousnessManager`.
- **FR-002**: Implement/Verify `CallbackRegistry` usage for `PerceptionAgent`, `ReasoningAgent`, and `MetacognitionAgent`.
- **FR-003**: Ensure MoSAEIC capture hooks are correctly registered as native callbacks.

### Key Entities

- **CallbackRegistry**: The standard `smolagents` mechanism for event handling.
- **ActionStep**: The event type we primarily listen to.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Codebase contains zero instances of manual `step_callbacks = [...]` assignment for `smolagents`.
- **SC-002**: Audit logs continue to populate without interruption during refactor.
