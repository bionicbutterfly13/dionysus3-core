# Implementation Plan: Neuronal Packet Mental Models

**Branch**: `030-neuronal-packet-mental-models` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/030-neuronal-packet-mental-models/spec.md`

## Summary

Enhance the system's cognitive architecture by integrating Neuronal Packet Dynamics, Multi-Order Self-Modeling, and EFE-driven Thoughtseeds. This involves augmenting the Neo4j schema with energy-well properties, implementing a hybrid Expected Free Energy (EFE) calculation engine for ThoughtSeed competition, and a Level-3 Metaplasticity controller within the ConsciousnessManager to dynamically adjust agent learning rates based on OODA prediction error.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, smolagents, api.services.claude, Graphiti-core, numpy  
**Storage**: Neo4j (MemoryCluster, Trajectory nodes)  
**Testing**: pytest  
**Target Platform**: Linux VPS (Docker container)  
**Project Type**: Single API Service  
**Performance Goals**: <50ms EFE calculation, <100ms Neo4j property updates  
**Constraints**: Webhook-only Neo4j updates, strict project-scoping  
**Scale/Scope**: System-wide cognitive upgrade affecting all specialized agents  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Library-First**: Core logic encapsulated in `NeuronalPacket` and `EFEEngine` libraries.
- [x] **II. CLI Interface**: EFE calculation and Metaplasticity state testable via CLI scripts.
- [x] **III. Test-First (NON-NEGOTIABLE)**: Unit tests for EFE formulas and Neo4j property mappings required before implementation.
- [x] **IV. Integration Testing**: Contract tests for n8n webhook updates included.
- [x] **V. Observability**: Tracing surprise levels, learning rate adjustments, and EFE scores across OODA cycles.

## Smolagents Synergy Elements

This upgrade provides three specific benefits to the `smolagents` fleet:

1.  **Context Pruning (Complexity Collapse)**: `NeuronalPackets` will act as context filters. Agents will only see tools and memories that are part of the active "Synergistic Whole," reducing hallucination and token waste.
2.  **Autonomous curiosity (EFE-driven Tooling)**: Implementing a `cognitive_check` tool that allows an agent to calculate its own Expected Free Energy. This enables the agent to autonomously pivot to "Epistemic" (Research) mode when it detects high uncertainty.
3.  **Adaptive Persistence (Metaplasticity)**: The `MetaplasticityController` will dynamically adjust the `max_steps` and `learning_rate` of specialized agents (e.g., MarketingAgent) based on real-time OODA prediction error.

## Project Structure

### Documentation (this feature)

```text
specs/030-neuronal-packet-mental-models/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cognitive-upgrade-api.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
api/
├── services/
│   ├── efe_engine.py               # NEW [P]
│   ├── metaplasticity_service.py   # NEW [P]
│   └── model_service.py            # ENHANCE
├── agents/
│   └── consciousness_manager.py     # ENHANCE
├── models/
│   ├── cognitive.py                # NEW
│   └── mental_model.py             # ENHANCE
└── dionysus_mcp/
    └── tools/
        └── cognitive_tools.py      # NEW

tests/
├── unit/
│   ├── test_efe_engine.py          # NEW [P]
│   └── test_metaplasticity.py      # NEW [P]
└── contract/
    └── test_neo4j_schema.py        # NEW
```

**Structure Decision**: Standard API service structure. Mark EFEEngine and Metaplasticity logic for parallel development [P] as they are mathematically independent until the final OODA integration.

## Complexity Tracking

No Constitution violations. Implementation adheres to mandated Neo4j-only, agentic standards.