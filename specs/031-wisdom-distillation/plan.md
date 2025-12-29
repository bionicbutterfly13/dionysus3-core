# Implementation Plan: Wisdom Distillation

**Spec**: [spec.md](./spec.md)

## Summary
Build the "Librarian" layer of Dionysus that synthesizes raw data into a coherent "System Soul."

## Technical Context
- **Data Source**: `wisdom_extraction_raw.json` and the Neo4j `Episode` graph.
- **Service**: `api/services/wisdom_service.py`.
- **Agent**: `api/agents/knowledge/wisdom_distiller.py` (CodeAgent).

## Milestones
1. **Wisdom Models**: Define `MentalModel`, `StrategicPrinciple`, and `CaseStudy` Pydantic schemas.
2. **The Distiller Agent**: Implement a `smolagent` that can read clusters of raw data and output canonical summaries.
3. **Graph Mapping**: Implement the service that writes these canonical units to Neo4j and handles the `provenance_chain` links.
4. **OODA Integration**: Update the `PerceptionAgent` to prioritize distilled Wisdom during memory recall.

## Verification
- Run distillation on the current `wisdom_extraction_raw.json`.
- Verify graph structure via Cypher.
