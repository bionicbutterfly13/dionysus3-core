# Feature Specification: Agentic Knowledge Graph Learning Loop

**Feature Branch**: `022-agentic-kg-learning`  \
**Created**: 2025-12-27  \
**Status**: Draft  \
**Input**: Bring Dionysus 2.0 agentic KG loop (dynamic relationship types, attractor basins, cognition-base learning) into Graphiti-backed Dionysus 3.

## User Scenarios & Testing

### User Story 1 - Dynamic Relationship Extraction (Priority: P1)
As a researcher agent, I want LLM-assisted extraction of relationships with dynamic types, so the graph evolves with the domain instead of a fixed schema.

**Independent Test**: Ingest a doc with novel relation; Neo4j/Graphiti shows a new relationship type created with confidence and provenance.

### User Story 2 - Basin-Guided Extraction (Priority: P1)
As the system, I want attractor basins that cluster concepts and guide extraction prompts, so relationship quality improves over time.

**Independent Test**: After multiple docs in the same domain, later docs show higher-quality relationships (confidence/precision) leveraging basin context.

### User Story 3 - Learning from Feedback (Priority: P2)
As the system, I want to record successful patterns and boost strategies (relationship types, narrative structures) over time, so extraction gets smarter.

**Independent Test**: After marking high-quality extractions, cognition-base updates strategy priorities and the next run reflects the boosts.

## Requirements

### Functional Requirements
- **FR-001**: Implement an extraction agent/tool that uses LLMs (local/remote) to propose relationships with dynamic types and confidences; store via Graphiti/Neo4j.
- **FR-002**: Maintain attractor basins for concepts, strengthening with frequency/co-occurrence; feed basin context into prompts.
- **FR-003**: Persist cognition-base learning signals (successful patterns, strategy boosts) and apply them on subsequent runs.
- **FR-004**: Track provenance (source doc, run id, model id) and confidence; surface low-confidence edges to human review queue.
- **FR-005**: Provide evaluation hooks to measure extraction quality over batches (precision/recall proxy or review rate).

### Success Criteria
- **SC-001**: New relationship types appear in Neo4j after processing docs with previously unseen relations.
- **SC-002**: Basin strength increases with repeated domain exposure and is referenced in extraction prompts/logs.
- **SC-003**: At least one strategy boost is recorded and used in a subsequent run, improving confidence or reducing review rate.

