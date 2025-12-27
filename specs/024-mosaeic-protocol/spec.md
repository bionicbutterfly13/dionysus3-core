# Feature Specification: MOSAEIC Protocol (S.A.E.I.C Windows)

**Feature Branch**: `024-mosaeic-protocol`  
**Status**: Draft  
**Input**: Implement the visceral core of the Inner Architect System: Mental Observation of Senses, Actions, Emotions, Impulses, and Cognitions.

## Overview
Dionysus 2.0 defined the MOSAEIC protocol but it remained "mostly stubbed." In Dionysus 3, we implement the **Five-Window Capture** system as a first-class citizen of the memory architecture. This allows agents to capture not just "what happened," but the deep experiential richness of the user (Dr. Mani) or the agent's own internal state.

## User Scenarios & Testing

### User Story 1 - Experiential Ingestion (Priority: P1)
As a user, I want to record an experience using the 5 windows (Senses, Actions, Emotions, Impulses, Cognitions), so that the agent understands my deep psychological state during a crisis or breakthrough.

**Independent Test**: Use the `mosaeic_capture` tool to ingest a narrative. Verify that Neo4j creates an `Episode` node linked to five distinct `Window` nodes (Senses, Actions, etc.).

### User Story 2 - Emotional Pattern Recognition (Priority: P1)
As an agent, I want to query the MOSAEIC graph to find correlations between specific "Impulses" and "Actions," so I can identify self-sabotage patterns.

**Independent Test**: Run a Cypher query finding all `Impulse` nodes linked to `Action:Sabotage`. Verify that the system can "recollect" the emotional triggers.

## Functional Requirements
- **FR-001**: Implement the `MOSAEICCapture` model with five windows: Senses, Actions, Emotions, Impulses, Cognitions.
- **FR-002**: Create a smolagent tool `mosaeic_capture` that extracts these five dimensions from any raw text.
- **FR-003**: Persist MOSAEIC episodes to Neo4j via Graphiti, using specific relationship types (e.g., `TRIGGERED_BY`, `MANIFESTED_AS`).
- **FR-004**: Integrate with the `PerceptionAgent` to ensure every "State Snapshot" includes a MOSAEIC evaluation.

## Success Criteria
- **SC-001**: A single raw text input results in 5 structured "Window" entities in the Knowledge Graph.
- **SC-002**: The `MarketingAgent` can cite specific "Emotional Richness" from the MOSAEIC graph when writing advertorials.
- **SC-003**: Zero loss of psychological nuance compared to Dr. Mani's original vision.
