# Feature Spec: Unified Consciousness Integration Pipeline (Feature 045)

**Created**: 2025-12-31
**Status**: Draft
**Branch**: 045-consciousness-integration-pipeline

## 1. Overview
The **Unified Consciousness Integration Pipeline** acts as the central cognitive nervous system for Dionysus 3.0. It orchestrates the flow of information between high-level reasoning (OODA), long-term semantic memory (Graphiti/Neo4j), and continuous autobiographical self-awareness. 

Every significant "Cognitive Event" (reasoning session, tool usage, or breakthrough) must be processed through this pipeline to ensure it is recorded in the agent's "self-story" and used to update the system's internal world model.

## 2. Goals
- **Unified Event Processing**: Provide a single entry point (`process_cognitive_event`) for recording and integrating reasoning outcomes.
- **Cross-System Traceability**: Ensure that a reasoning session creates:
    1.  An **Autobiographical Event** (Self-story).
    2.  **Graphiti Episodes** (Entity/Fact extraction).
    3.  **Meta-Cognitive Episodes** (Strategy learning).
- **Physics Update**: Hook into the Active Inference engine to update prediction errors and free energy based on the event's outcome.
- **Attractor Basin Modulation**: Strengthen or weaken memory basins based on the success of the reasoning path.

## 3. Implementation Details

### 3.1 Pipeline Service (`api/services/consciousness_integration_pipeline.py`)
Implement `ConsciousnessIntegrationPipeline`:
- **`process_cognitive_event(problem, reasoning_trace, outcome, context)`**:
    - Calls `AutobiographicalService.record_event`.
    - Calls `GraphitiService.ingest_message` (for fact extraction).
    - Calls `MetaCognitiveLearner.record_episode`.
    - Calls `BasinService.strengthen_basin` (if successful).
    - Calculates and logs system-wide **Coherence** and **Emergence** metrics.

### 3.2 Integration into OODA Loop
The `ConsciousnessManager` will call this pipeline at the end of every `run_ooda_cycle`.

## 4. Dependencies
- `api.services.autobiographical_service`
- `api.services.graphiti_service`
- `api.services.meta_cognitive_service`
- `api.services.basin_service` (or equivalent)

## 5. Testing Strategy
- **Integration Test**: Run an OODA cycle and verify that nodes are created in Neo4j for ALL three systems (Autobiographical, Graphiti, and Meta-Cognition).

## 6. Success Criteria
- A single call to the pipeline updates all persistence layers.
- System logs show "Unified Integration successful" with a traceability ID.
- Retrieval of past events shows linked entities and strategic lessons.