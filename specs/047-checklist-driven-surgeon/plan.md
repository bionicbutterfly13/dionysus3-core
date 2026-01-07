# Implementation Plan: Checklist-Driven Surgeon Metaphor

**Branch**: `047-checklist-driven-surgeon` | **Date**: 2025-12-31 | **Spec**: `/specs/047-checklist-driven-surgeon/spec.md`

## Summary
Implement the "Checklist-Driven Surgeon" metaphor by porting and integrating research-validated cognitive tools from Dionysus 2.0. This approach enforces a rigorous, multi-step verification protocol for all complex reasoning tasks, mirroring the disciplined environment of a surgical operating room.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: smolagents, LiteLLM (openai/gpt-5-nano)  
**Storage**: Neo4j (via Graphiti-backed driver shim), Graphiti  
**Testing**: pytest  
**Target Platform**: Linux server (VPS)
**Project Type**: Autonomous Cognitive Engine  
**Performance Goals**: <5s overhead per verification step, significant reduction in reasoning entropy.  
**Constraints**: Must maintain smolagents hierarchical managed agent architecture.

## Project Structure

### Documentation (this feature)

```text
specs/047-checklist-driven-surgeon/
├── spec.md              # Feature specification
├── plan.md              # This file
├── tasks.md             # Task list
└── checklist.md         # Operational checklist
```

### Source Code (repository root)

```text
api/
├── agents/
│   ├── consciousness_manager.py # Orchestrator updates
│   ├── managed/
│   │   └── reasoning.py         # Agent description updates
│   └── tools/
│       └── cognitive_tools.py   # Tool implementations
└── services/
    └── consciousness_integration_pipeline.py # Pipeline integration
```

## Structure Decision
Integration will occur primarily within the `ReasoningAgent` (as the "Surgeon") and the `ConsciousnessManager` (as the "Hospital Director" enforcing the protocol).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multi-step verification | Essential for the Surgeon metaphor | Single-pass generation is prone to hallucination |
