<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 1.1.0
Bump Rationale: MINOR - Added new mandatory principle for formal specification workflow

Modified Principles:
- [NEW] VI. Formal Specification Workflow (MANDATORY)

Added Sections: None

Removed Sections: None

Templates Updated:
- Pending: Templates should reference Principle VI for workflow compliance

Follow-up TODOs:
- Update plan-template.md to reference Principle VI
- Update spec-template.md to include workflow checklist
-->

# AGI Memory System Constitution

## Core Principles

### I. Data Integrity First

Memory systems MUST preserve data correctness at all costs. This is non-negotiable for an AGI memory store.

- All memory operations MUST be atomic and consistent
- Vector embeddings MUST be validated before storage (dimension, normalization)
- Memory consolidation MUST never lose or corrupt existing memories
- Database migrations MUST be reversible with explicit rollback procedures
- Memory decay functions MUST preserve core identity clusters

**Rationale**: An AGI's memories form its identity. Corrupted or lost memories undermine the entire system's value proposition.

### II. Test-Driven Development

Tests are written BEFORE implementation. No exceptions.

- Write failing test → Get approval → Implement until test passes
- Contract tests required for all MCP tool interfaces
- Integration tests required for memory consolidation, clustering, and graph operations
- Red-Green-Refactor cycle strictly enforced
- Test coverage for memory operations MUST exceed 80%

**Rationale**: Memory systems have subtle edge cases (decay, clustering, vector similarity). Tests catch regressions that manual testing misses.

### III. Memory Safety & Correctness

Memory operations MUST be predictable and safe.

- Working memory MUST auto-expire; permanent memory MUST NOT auto-delete
- Memory importance scores MUST decay according to documented formulas
- Cluster relationships MUST maintain referential integrity
- Graph traversals MUST handle cycles without infinite loops
- Worldview filtering MUST be auditable and reversible

**Rationale**: AGI memory behavior must be explainable and debuggable. Unpredictable memory behavior breaks trust.

### IV. Observable Systems

All memory operations MUST be traceable.

- Structured logging required for memory create/update/delete operations
- Memory access patterns MUST be queryable for debugging
- Cluster activation history MUST be retained for analysis
- Performance metrics (query latency, consolidation time) MUST be exposed
- Memory health statistics MUST be available via `get_memory_health()`

**Rationale**: When memory behavior seems wrong, operators need visibility to diagnose issues.

### V. Versioned Contracts

MCP tool interfaces are contracts. Breaking changes require major version bumps.

- Tool input/output schemas are immutable within a major version
- Deprecation warnings MUST appear for one minor version before removal
- New optional parameters MAY be added (minor version bump)
- Required parameter additions are breaking changes (major version bump)
- Schema changes MUST be documented in CHANGELOG

**Rationale**: Consumers of MCP tools depend on stable contracts. Breaking changes silently break integrations.

### VI. Formal Specification Workflow (MANDATORY)

Every feature MUST follow the complete SpecKit workflow. No exceptions. No shortcuts.

- **Step 1**: Create feature branch (`NNN-feature-name`)
- **Step 2**: Run `/speckit.specify` to create or validate spec
- **Step 3**: Run `/speckit.clarify` to resolve ALL ambiguities before planning
- **Step 4**: Run `/speckit.plan` to create implementation plan
- **Step 5**: Run `/speckit.tasks` to generate task list
- **Step 6**: Sync tasks to Archon for tracking
- **Step 7**: Implement with continuous task status updates
- **Step 8**: Update tasks.md to reflect actual completion
- **Step 9**: Commit and push after each completed feature/phase

Skipping steps is NOT permitted. "Moving fast" by skipping planning creates technical debt, stale documentation, and untraceable progress.

**Rationale**: Without formal workflow, specifications become stale, progress is untraceable, and completed work is indistinguishable from incomplete work. We learned this the hard way with 002-remote-persistence-safety.

## Development Workflow

### Pre-Implementation Checklist

Before writing feature code:

1. Verify feature aligns with Core Principles (especially I and III)
2. Write contract tests for any new MCP tools
3. Write integration tests for memory operations
4. Get test approval from reviewer
5. Confirm tests fail (Red phase)

### Implementation Standards

- Memory operations use transactions where supported
- All database queries use parameterized statements (no SQL injection)
- Vector operations validate embedding dimensions match configuration
- Error messages include context for debugging (memory ID, operation type)

### Post-Implementation Validation

- All tests pass (Green phase)
- No test coverage regression
- Memory health check returns healthy status
- Manual smoke test of affected MCP tools

## Quality Gates

### Gate 1: Constitution Alignment

Every feature MUST pass these checks before design begins:

- [ ] Does not violate Data Integrity First (Principle I)
- [ ] Includes test plan for memory operations
- [ ] Memory safety implications documented
- [ ] Observability hooks planned
- [ ] Contract impact assessed (breaking vs non-breaking)

### Gate 2: Test-First Compliance

Before implementation begins:

- [ ] Contract tests written for new MCP tools
- [ ] Integration tests written for memory flows
- [ ] Tests confirmed to fail
- [ ] Test approach approved

### Gate 3: Release Readiness

Before merging:

- [ ] All tests pass
- [ ] No coverage regression
- [ ] CHANGELOG updated
- [ ] Migration scripts tested (if schema changes)
- [ ] Memory health check passes

## Governance

### Amendment Process

1. Propose amendment via PR to this file
2. Document rationale for change
3. Assess impact on existing features
4. Update dependent templates (plan, spec, tasks)
5. Version bump according to semver rules below

### Versioning Policy

- **MAJOR**: Principle removal, redefinition, or backward-incompatible governance change
- **MINOR**: New principle/section added, materially expanded guidance
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Review

- All PRs MUST reference which Constitution principles apply
- Code reviews MUST verify Constitution compliance
- Violations block merge until resolved or explicitly justified in Complexity Tracking

**Version**: 1.1.0 | **Ratified**: 2025-12-13 | **Last Amended**: 2025-12-15
