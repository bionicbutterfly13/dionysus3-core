# Feature Specification: Neuronal Packet Mental Models

**Feature Branch**: `030-neuronal-packet-mental-models`  
**Created**: 2025-12-27  
**Status**: Draft  
**Input**: Integrate Neuronal Packet Dynamics (Yufik), Multi-Order Self-Modeling (Treur), and EFE-driven Thoughtseeds (Kavi) with Context-Engineering and MemEvolve/Graphiti synergy.

## Clarifications

### Session 2025-12-27
- Q: How is "Goal Divergence" calculated in the EFEEngine? → A: Vector Distance (Cosine distance between ThoughtSeed vector and Goal embedding)
- Q: What happens to original basins when they are merged into an SE? → A: Hierarchy (Basins remain active and are linked via `PART_OF` relationships)
- Q: What triggers Level-3 Metaplasticity (learning rate adjustment)? → A: Surprise-Driven (Higher rates when OODA prediction error is high)
- Q: How should mental model evolution history be stored? → A: Typed (Episodic vs Structural Trajectories)
- Q: What is the primary source of "Surprise" for metaplasticity? → A: Prediction Error (Aggregate error from ModelService)

## User Scenarios & Testing

### User Story 1 - Energy-Well Stability (Priority: P1)
As the system, I want my memory clusters to act as "Energy Wells" with defined boundary energies, so that I can maintain stable mental models and prevent context bleed during complex tasks.

**Why this priority**: Essential for maintaining a coherent "Project Identity" and preventing agents from being distracted by irrelevant graph context.

**Independent Test**: Artificially increase "Surprise" (prediction error); verify that "Deep Wells" (high boundary energy) remain active while "Shallow Wells" (low confidence) are suppressed or trigger a recall.

### User Story 2 - Autonomous Curiosity via EFE (Priority: P1)
As an agent, I want to use Expected Free Energy (EFE) to decide whether to "Research" (Epistemic) or "Execute" (Pragmatic), so I can proactively fill knowledge gaps before acting.

**Why this priority**: Directly reduces hallucinations and increases the accuracy of agentic outputs by prioritizing truth-seeking when confidence is low.

### User Story 3 - Level-3 Metaplasticity Control (Priority: P2)
As the ConsciousnessManager, I want to adjust the learning rate of my specialized agents based on their OODA cycle performance and MemEvolve trajectories, so the system adapts faster to new environments.

**Why this priority**: Provides the "Second-Order Adaptation" required for long-term strategic evolution and efficiency.

### User Story 4 - Context Pollution Prevention (Priority: P1)
As the system, I want to use "Explorer Agents" to scan the knowledge graph and identify semantic attractors, so that context pollution is minimized and agents are focused on the most relevant synergistic whole.

## Requirements

### Functional Requirements
- **FR-030-001**: Augment `MemoryCluster` nodes in Neo4j with `boundary_energy` (float), `cohesion_ratio` (float), and `stability` (float) properties. [P]
- **FR-030-002**: Implement a `NeuronalPacket` class that encapsulates a group of related `ThoughtSeeds` and enforces mutual constraints (Synergistic Wholes). Hierarchical relationships MUST be preserved via `PART_OF` links to Superordinate Ensembles (SE). [P]
- **FR-030-003**: Implement an `EFEEngine` that calculates Expected Free Energy for candidate thoughtseeds using the formula: `EFE = Uncertainty (Entropy) + Goal Divergence`. Uncertainty is calculated as the Shannon Entropy of the ThoughtSeed's `prediction_probabilities`; Goal Divergence is the Cosine distance to the goal embedding. [P]
- **FR-030-004**: Integrate `EFEEngine` into the `ThoughtSeed` network logic to select the dominant thought via winner-take-all dynamics.
- **FR-030-005**: Implement a `MetaplasticityController` (Level 3) that monitors OODA cycle "Surprise" (based on aggregate `prediction_error` and MemEvolve trajectories) and adjusts the `learning_rate` and `max_steps` of `smolagents`. [P]
- **FR-030-006**: Persist mental model evolution history as `Trajectory` nodes with specific `type` attributes (`EPISODIC` vs `STRUCTURAL`).
- **FR-030-007**: Create a `ContextExplorerTool` for `smolagents` that implements the `/research.agent` protocol from Context-Engineering to identify and activate project-specific semantic attractors.
- **FR-030-008**: Map the **Avatar Mental Model** ([LEGACY_AVATAR_HOLDER] state) into the Energy Well framework, allowing agents to track user "Attractor Basins" (e.g., Resistance, Breakthrough) using the same stability and energy metrics.

### Non-Functional Requirements
- **NFR-030-001**: EFE calculations MUST complete in <50ms per thoughtseed to maintain system responsiveness.
- **NFR-030-002**: Neo4j property updates MUST be batch-executed via n8n webhooks to ensure consistency with the Neo4j-only architecture.

## Success Criteria

### Measurable Outcomes
- **SC-030-001**: 30% reduction in agent hallucinations due to EFE-driven curiosity.
- **SC-030-002**: Stable OODA cycle duration via synergistic grouping.
- **SC-030-003**: 100% of agent learning rates are dynamically adjusted.