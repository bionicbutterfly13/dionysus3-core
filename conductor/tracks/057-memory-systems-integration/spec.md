# Feature Specification: Memory Systems Integration

**Track ID**: 057-memory-systems-integration
**Status**: In Progress (0%)
**Depends On**: 038-thoughtseeds-framework (in progress), 039-smolagents-v2-alignment (done)

## Overview

Consolidate memory system integrations so Nemori, MemEvolve, and AutoSchemaKG share a Graphiti-backed Neo4j path, while ensuring active inference is the sole decision engine for Meta-ToT and basin context remains explicitly linked during semantic distillation.

## Problem Statement

Current integration issues:
1. Legacy MCTS/POMCP logic still appears in Meta-ToT pathways.
2. Nemori semantic distillates lack explicit attractor basin + Markov blanket linkage.
3. Neo4j is still accessed via multiple channels (Graphiti + n8n) in some services.
4. MemEvolve ingest/recall alignment lacks test coverage.
5. AutoSchemaKG integration and concept ingestion need Graphiti-aligned paths.

## Requirements

- **FR-057-001**: Meta-ToT uses active inference scoring only (no MCTS/POMCP branches).
- **FR-057-002**: Nemori distillation metadata tags basin + Markov blanket context.
- **FR-057-003**: Development events link to AttractorBasin + MarkovBlanket nodes in Graphiti.
- **FR-057-004**: Neo4j access is routed through Graphiti in memory retrieval paths.
- **FR-057-005**: MemEvolve adapter stores Trajectory nodes and recalls via Graphiti.
- **FR-057-006**: AutoSchemaKG ingest uses Graphiti with validated concept ingestion.
- **FR-057-007**: Nemori implements `ContextCell` with token budgets and symbolic residue.
- **FR-057-008**: Attractor Basins implement `ResonanceCoupling` logic.

## Success Criteria

- **SC-057-001**: No references to MCTS/POMCP remain in Meta-ToT execution logic.
- **SC-057-002**: Distilled semantic events link to basin + blanket nodes in Neo4j.
- **SC-057-003**: VectorSearchService no longer uses n8n cypher calls.
- **SC-057-004**: MemEvolve ingest/recall/evolve tests pass with Graphiti mocks.
- **SC-057-005**: AutoSchemaKG concept ingest persists via Graphiti with tests.
- **SC-057-006**: Nemori episodes respect token budgets and produce symbolic residue.

## Dependencies

- Graphiti service availability and Neo4j schema additions are additive only.
- MemEvolve + AutoSchemaKG repos available in `/Volumes/Asylum/repos`.
