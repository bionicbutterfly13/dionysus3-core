# Feature Specification: Procedural Memory as Skills

**Feature Branch**: `006-procedural-skills`  
**Created**: 2025-12-17  
**Status**: Draft  
**Input**: User description: "Replace ThoughtSeed for procedural memory with a Skill abstraction; keep ThoughtSeed for ideation. Graph traversal is primary recall; vectors allowed as secondary."

## Overview

Procedural memory should be represented as `(:Skill)` nodes (capability primitives that improve with practice, have prerequisites, decompose into subskills, transfer across contexts, and decay without use).

This feature adds a `Skill` abstraction to the canonical Neo4j schema and exposes a vetted traversal query (`skill_graph`) via the existing n8n traversal webhook (`/webhook/memory/v1/traverse`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Skill Graph Recall (Priority: P1)

As the agent, I want to traverse a skill’s dependency/substep graph so that I can reason about “what I can do”, “what prerequisites are missing”, and “how to decompose actions”.

**Why this priority**: This is the minimum slice that enables graph-traversal-based procedural reasoning without requiring full skill extraction/learning automation.

**Independent Test**: Create a `Skill` node with `REQUIRES` and `HAS_SUBSTEP` relationships; call `POST /api/memory/traverse` with `query_type=skill_graph`; verify the returned graph contains the skill and its neighbors.

**Acceptance Scenarios**:
1. **Given** a `Skill` with `skill_id`, **When** I call `/api/memory/traverse` with `{"query_type":"skill_graph","params":{"skill_id":"..."}}`, **Then** I receive the `Skill` node plus outgoing/incoming neighbors for supported relationship types.
2. **Given** an unknown `skill_id`, **When** I call `skill_graph`, **Then** the response is successful but returns no records (or an explicit not-found error if we standardize this later).

---

### User Story 2 - Skill Provenance & Applicability (Priority: P2)

As the agent, I want to see what a skill was learned from and what contexts it applies to, so I can transfer skills appropriately.

**Why this priority**: Provenance and applicability are core to procedural memory (transfer and auditability).

**Independent Test**: Create `(:Skill)-[:LEARNED_FROM]->(:Document)` and `(:Skill)-[:APPLIES_TO]->(:Context)`; traverse via `skill_graph`; verify these edges appear in `outgoing`.

**Acceptance Scenarios**:
1. **Given** `LEARNED_FROM` and `APPLIES_TO` edges, **When** I call `skill_graph`, **Then** the response includes those edges and the connected nodes.

---

### User Story 3 - ThoughtSeed Remains for Ideation (Priority: P3)

As the agent, I want ThoughtSeeds to remain a separate ideation construct so that procedural memory does not get conflated with germination.

**Why this priority**: Keeps cognitive functions distinct and avoids schema drift.

**Independent Test**: Ensure traversal queries and docs clearly separate `ThoughtSeed` (ideation) from `Skill` (procedural).

**Acceptance Scenarios**:
1. **Given** a `ThoughtSeed` graph, **When** I add Skills, **Then** Skills are not stored as ThoughtSeeds and traversal queries use `Skill` label.

### Edge Cases

- Cycles in `REQUIRES` / `HAS_SUBSTEP` graphs (must not hang; queries should be bounded).
- Missing/invalid `skill_id` in traversal params should produce a clear error from n8n validation.
- Skills may exist without any edges; traversal should still return the node.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST represent procedural memory as `(:Skill)` nodes (distinct from `(:ThoughtSeed)`).
- **FR-002**: The system MUST support these Skill properties: `skill_id`, `name`, `description`, `proficiency`, `practice_count`, `last_practiced`, `decay_rate`.
- **FR-003**: The system MUST support these Skill relationships:
  - `(:Skill)-[:REQUIRES]->(:Skill)`
  - `(:Skill)-[:HAS_SUBSTEP]->(:Skill)`
  - `(:Skill)-[:APPLIES_TO]->(:Context)`
  - `(:Skill)-[:LEARNED_FROM]->(:Document|:Session)`
- **FR-004**: The API MUST provide `POST /api/memory/traverse` that routes traversal requests through n8n (no direct Neo4j access).
- **FR-005**: n8n MUST expose a vetted traversal query `query_type=skill_graph` that returns a skill plus its neighbors for supported relationship types.
- **FR-006**: The application MUST NEVER connect directly to Neo4j; all reads/writes MUST go through n8n webhooks.

### Key Entities

- **Skill**: A procedural capability with practice-driven proficiency and decay.
- **Context**: Applicability scope for transfer learning (may be sparse initially).
- **ThoughtSeed**: Ideation/germination construct (not procedural).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `skill_graph` traversal returns in < 1s for graphs up to 200 neighbors (bounded query).
- **SC-002**: Procedural memory queries use graph traversal as primary mechanism (documented + exposed via traversal webhook).
- **SC-003**: No code path in the application connects to Neo4j directly (webhook-only enforced).

