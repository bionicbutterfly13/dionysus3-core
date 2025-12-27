# Feature Specification: Rollback Safety Net for Agentic Changes

**Feature Branch**: `021-rollback-safety-net`  \
**Created**: 2025-12-27  \
**Status**: Draft  \
**Input**: Port Dionysus 2.0 rollback/checkpoint service to protect smolagent-driven refactors, memory writes, and migrations with <30s recovery.

## User Scenarios & Testing

### User Story 1 - Pre-change Checkpoint (Priority: P1)
As an operator, I want an easy way to checkpoint files/metadata before an agentic refactor, so I can recover quickly if the change is bad.

**Independent Test**: Create a checkpoint for a component, modify the code, then rollback and verify files and metadata restore.

### User Story 2 - Fast Rollback Execution (Priority: P1)
As an operator, I want rollback to finish in under 30 seconds with minimal manual steps, so incidents don’t block live work.

**Independent Test**: Trigger rollback via API/CLI; measure duration <30s and confirm task status reflects success.

### User Story 3 - Retention & Auditability (Priority: P2)
As an operator, I want retention windows, backup metadata (sizes, checksums), and history, so I can audit and clean storage safely.

**Independent Test**: List checkpoints, see retention timestamps, and verify history records success/failure with reasons.

## Requirements

### Functional Requirements
- **FR-001**: Implement checkpoint creation that backs up primary files plus discovered related files, metadata, and relevant DB state to a configurable path.
- **FR-002**: Provide rollback that restores backups, updates statuses, and records history with duration and outcome.
- **FR-003**: Expose CLI/API + smolagent tool hooks to create checkpoints and perform rollbacks; require confirmation for destructive actions.
- **FR-004**: Include retention policy support (days) and cleanup of expired checkpoints.
- **FR-005**: Log structured events for checkpoint create/restore with sizes, checksums, and errors; surface counts via monitoring (Spec 023).

### Success Criteria
- **SC-001**: Checkpoint + rollback round-trip restores code and metadata for a sample component with checksum match.
- **SC-002**: Rollback completes in <30s in a test scenario.
- **SC-003**: Expired checkpoints are cleaned up according to retention without affecting active ones.

