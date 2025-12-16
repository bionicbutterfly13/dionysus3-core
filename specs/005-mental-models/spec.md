# Feature Specification: Mental Model Architecture

**Feature Branch**: `005-mental-models`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "Implement mental model architecture based on Yufik's neuronal packet theory for prediction, explanation, and reasoning in novel situations"

## Overview

Enable Dionysus to construct, maintain, and revise structured mental representations that predict user behavior, explain patterns, and reason about novel situations. Mental models combine existing memory patterns (attractor basins) into higher-order structures that generate predictions and improve through experience.

### Problem Statement

Currently, Dionysus can recall memories and identify patterns, but lacks the ability to:
- Generate predictions about user behavior or outcomes
- Explain *why* patterns occur (not just *what* patterns exist)
- Reason effectively in novel situations without prior experience
- Improve understanding through prediction error feedback

### Value Proposition

Mental models enable Dionysus to move from **situational awareness** ("what is happening") to **situational understanding** ("why it's happening and what will happen next"), providing more insightful and proactive assistance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prediction Generation During Interaction (Priority: P1)

As a user interacting with Dionysus, I want the system to anticipate my needs based on patterns it has learned, so that I receive proactive and relevant assistance.

**Why this priority**: This is the core value proposition - predictions that improve interaction quality. Without prediction generation, mental models have no observable effect.

**Independent Test**: Create a mental model from existing memory patterns, interact with the system in a context matching the model's domain, and verify that relevant predictions are generated and stored.

**Acceptance Scenarios**:

1. **Given** an active mental model about "user work patterns", **When** the user mentions a topic covered by that model, **Then** the system generates at least one prediction related to the user's likely state or needs.
2. **Given** a context that matches multiple models, **When** processing the current situation, **Then** predictions are generated from all relevant models ordered by confidence.
3. **Given** no active models match the current context, **When** processing the situation, **Then** no predictions are generated (graceful degradation).

---

### User Story 2 - Prediction Error Tracking and Learning (Priority: P1)

As an administrator or the system itself, I want to track how accurate predictions are over time, so that models can be identified for improvement or deprecation.

**Why this priority**: Without error tracking, models cannot improve. This is essential for the learning loop that makes mental models valuable over time.

**Independent Test**: Generate a prediction, wait for the actual outcome, compare prediction to observation, and verify the error is recorded and affects the model's accuracy score.

**Acceptance Scenarios**:

1. **Given** an unresolved prediction from a previous interaction, **When** the actual outcome is observed, **Then** the prediction error is calculated and stored.
2. **Given** a model with multiple resolved predictions, **When** querying model status, **Then** a rolling accuracy score (last 30 days) is available.
3. **Given** a model with average prediction error above threshold (>0.5), **When** checking system health, **Then** the model is flagged for revision.

---

### User Story 3 - Model Revision Based on Errors (Priority: P2)

As the system, I want to automatically revise models that show high prediction error, so that my understanding improves over time without manual intervention.

**Why this priority**: Automatic revision enables continuous improvement. This can be deferred initially while manual model creation is prioritized.

**Independent Test**: Create a model, simulate high prediction errors, trigger the revision process, and verify the model structure is updated and the new accuracy is tracked.

**Acceptance Scenarios**:

1. **Given** a model with consistently high prediction error, **When** the revision process runs, **Then** the model's structure is updated and old structure is preserved in history.
2. **Given** a model undergoing revision, **When** revision completes, **Then** new predictions use the revised structure.
3. **Given** a revision occurs, **When** querying the model, **Then** the revision history shows what changed and why.

---

### User Story 4 - Manual Model Creation (Priority: P2)

As a developer or administrator, I want to manually create mental models by specifying which memory patterns (basins) to combine, so that I can seed the system with known useful models.

**Why this priority**: Manual creation allows bootstrapping the system with useful models before automatic model building is implemented.

**Independent Test**: Specify a model name, domain, and list of existing memory basins; verify the model is created and can generate predictions.

**Acceptance Scenarios**:

1. **Given** valid basin identifiers and a model name, **When** creating a model, **Then** the model is stored and becomes active.
2. **Given** one or more invalid basin identifiers, **When** attempting to create a model, **Then** creation fails with a clear error message.
3. **Given** a newly created model, **When** querying active models, **Then** the new model appears in the list with status "active".

---

### User Story 5 - Model Types and Domains (Priority: P3)

As a user, I want Dionysus to maintain different types of models (about me, about itself, about the world), so that predictions are appropriately categorized and applied.

**Why this priority**: Domain categorization improves prediction relevance but is not essential for core functionality.

**Independent Test**: Create models with different domains, verify they are retrieved when their domain matches the current context.

**Acceptance Scenarios**:

1. **Given** models in different domains (user, self, world), **When** filtering by domain, **Then** only models of that domain are returned.
2. **Given** a context primarily about the user, **When** retrieving relevant models, **Then** user-domain models are prioritized.
3. **Given** a new domain type, **When** creating a model with that domain, **Then** the system accepts the custom domain value.

---

### Edge Cases

- What happens when a model has no constituent basins (basins were deleted)?
  - System marks model as "degraded" and excludes from prediction generation
- How does the system handle circular references in basin relationships?
  - Basin relationships are stored as metadata only; graph traversal is bounded
- What happens when prediction resolution arrives much later (hours/days)?
  - Predictions have a time-to-live; expired unresolved predictions are marked as "timed out"
- How does the system behave with 100+ active models?
  - Relevance scoring limits active model selection per context to configurable max (default: 5)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow creation of mental models from one or more existing memory basins
- **FR-002**: System MUST generate predictions when processing contexts that match active models
- **FR-003**: System MUST track prediction accuracy by comparing predictions to observed outcomes
- **FR-004**: System MUST calculate and store prediction error for each resolved prediction
- **FR-005**: System MUST maintain a rolling accuracy score for each model (30-day window)
- **FR-006**: System MUST flag models with average error above threshold for revision
- **FR-007**: System MUST preserve revision history including trigger, old structure, and new structure
- **FR-008**: System MUST support model domains: "user", "self", "world", and custom domains
- **FR-009**: System MUST validate that all referenced basins exist before creating a model
- **FR-010**: System MUST support model lifecycle states: draft, active, deprecated
- **FR-011**: System MUST allow querying models by domain and status
- **FR-012**: System MUST record predictions with confidence scores and context
- **FR-013**: System MUST integrate with existing active inference processing

### Key Entities

- **Mental Model**: A structured combination of memory basins that generates predictions. Contains name, domain, constituent basins, prediction templates, and validation state.
- **Model Prediction**: A specific prediction generated by a model, including the context that triggered it, confidence level, and resolution status.
- **Model Revision**: A historical record of changes to a model's structure, including what triggered the revision and accuracy before/after.
- **Basin Relationship**: Metadata describing how constituent basins relate within a model (causal, temporal, hierarchical).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mental models can be created from existing memory basins within 2 seconds
- **SC-002**: System generates relevant predictions for 80% of contexts that match active models
- **SC-003**: Prediction errors are calculated and stored within 1 minute of observation
- **SC-004**: Model accuracy scores are queryable and updated in real-time
- **SC-005**: High-error models (>0.5 avg error) are automatically flagged within 24 hours
- **SC-006**: Model revision preserves 100% of historical structure for audit
- **SC-007**: System supports at least 100 active models without performance degradation
- **SC-008**: Prediction generation adds less than 500ms to interaction processing time

## Assumptions

- Memory basins (clusters) already exist and are populated with relevant memories
- Active inference processing is already operational in the heartbeat system
- The system has access to LLM capabilities for generating and evaluating predictions
- Prediction error calculation is semantic (requires LLM comparison), not exact match

## Dependencies

- Feature 001: Session Continuity (for memory persistence)
- Feature 002: Remote Persistence Safety (for backup of model data)
- Existing: Memory clustering system (attractor basins)
- Existing: Heartbeat and active inference processing

## Out of Scope

- Automatic discovery of which basins to combine into models (manual or rule-based creation only for MVP)
- Cross-user model sharing or templates
- Real-time model training during interaction (batch revision only)
- Visualization of model structures
