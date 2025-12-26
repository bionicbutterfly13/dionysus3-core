# Feature Specification: Core Services Neo4j Migration

**Feature Branch**: `011-core-services-migration`  
**Created**: 2025-12-26  
**Status**: Draft  
**Input**: User description: "Migrate Worldview, ThoughtSeed, and Model services to Neo4j-only architecture."

## User Scenarios & Testing

### User Story 1 - Neo4j-Native Mental Models (Priority: P1)

As a cognitive system, I want my mental models and predictions stored in the graph, so that I can exploit relational links for reasoning.

**Why this priority**: Eliminates the last relational dependency in the cognitive core.

**Independent Test**: Create a model via REST API and verify the node exists in Neo4j with correct constituent basin relationships.

---

### User Story 2 - Precision-Weighted Belief Updates (Priority: P2)

As a cognitive system, I want my worldview confidence updated mathematically based on prediction error stability.

**Why this priority**: Implements active inference principles from Dionysus 2.0 correctly in the new architecture.

**Independent Test**: Resolve 5 predictions with error and verify the `Worldview` node confidence reflects the precision-weighted formula.

---

## Requirements

### Functional Requirements

- **FR-001**: All database operations in `ModelService`, `WorldviewIntegrationService`, and `ThoughtSeedIntegrationService` MUST use `WebhookNeo4jDriver`.
- **FR-002**: Direct PostgreSQL references MUST be removed from all core services.
- **FR-003**: `WorldviewIntegrationService` MUST implement the formula: `confidence_update = error / (1 + variance)`.

## Key Entities

- **MentalModel**: Attractor-basin based predictive structure.
- **WorldviewPrimitive**: Core belief node in the knowledge graph.
- **ThoughtSeed**: Emergent idea node.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of Model/Worldview tests pass using Neo4j as the source of truth.
- **SC-002**: Zero relational database migration files or SQL strings remain in the core service layer.