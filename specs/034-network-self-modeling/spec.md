# Feature Specification: Network Reification and Self-Modeling

**Feature Branch**: `034-network-self-modeling`
**Created**: 2025-12-29
**Status**: Draft
**Input**: User description: "Implement the missing mental model concepts from Treur's research: (1) Network reification layer with explicit self-model states (W, T, H) for connection weights, thresholds, and speed factors, (2) Auxiliary self-modeling task for agent regularization, (3) Hebbian learning dynamics for knowledge graph relationships, (4) Role matrix specification system for formal network topology management."

## Overview

This feature introduces a neuroscience-grounded foundation for self-modifying agent architecture. Currently, the system's mental models are static data structures with procedural adaptation. This feature adds new observability and learning layers that enable agents to introspect and adapt their own structure.

**CRITICAL: Non-Breaking Design**

All components in this feature are **purely additive**:
- New models sit alongside existing ones (no schema migrations required)
- New services wrap existing functionality (existing behavior unchanged)
- All new capabilities are opt-in via configuration flags
- Existing agents, mental models, and learning pipelines continue working exactly as before

The implementation is based on Jan Treur's research on self-modeling networks and adaptive mental models, combined with findings on self-modeling as regularization from recent neural network research.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Network State Observation (Priority: P1)

As a system operator, I need to observe the internal network states (connection weights, thresholds, speed factors) of cognitive agents so that I can understand why agents make specific decisions and diagnose unexpected behavior.

**Why this priority**: Foundation for all other features. Without observable network states, no self-modeling or adaptation is possible. Provides immediate debugging value.

**Independent Test**: Can be fully tested by querying any agent's network state and receiving a structured representation of its W (weights), T (thresholds), and H (speed) values. Delivers immediate observability value.

**Non-Breaking**: Adds new query endpoint; existing agents work without modification.

**Acceptance Scenarios**:

1. **Given** a running cognitive agent, **When** I request its network state, **Then** I receive a structured snapshot showing all connection weights between components, activation thresholds, and adaptation speed factors.
2. **Given** an agent processing a task, **When** I observe its network state before and after, **Then** I can see which connections strengthened or weakened and which thresholds changed.
3. **Given** multiple agents in the system, **When** I request network states for each, **Then** each returns its unique configuration reflecting its learning history.

---

### User Story 2 - Self-Prediction for Agent Regularization (Priority: P2)

As a system architect, I need agents to predict their own next internal states so that the system automatically reduces unnecessary complexity and maintains interpretable behavior over time.

**Why this priority**: Prevents agent "complexity creep" where learned behaviors become increasingly opaque. Research shows 15-25% complexity reduction with self-modeling. Critical for long-term system maintainability.

**Independent Test**: Can be fully tested by comparing agent complexity metrics (weight distribution width, parameter efficiency) before and after enabling self-prediction. Delivers measurable regularization.

**Non-Breaking**: Self-prediction is an optional auxiliary task. Agents without it enabled behave exactly as before.

**Acceptance Scenarios**:

1. **Given** an agent with self-prediction enabled, **When** it completes a learning cycle, **Then** it generates predictions about its next internal state and compares them to actual outcomes.
2. **Given** agents with and without self-prediction, **When** both process the same workload over time, **Then** the self-predicting agent maintains narrower weight distributions (lower complexity).
3. **Given** an agent's self-prediction accuracy drops below threshold, **When** this is detected, **Then** the system flags the agent for potential drift or instability.

---

### User Story 3 - Hebbian Learning for Knowledge Relationships (Priority: P2)

As a knowledge manager, I need knowledge graph relationships to strengthen based on co-activation patterns so that frequently-used associations become more accessible and rarely-used ones fade appropriately.

**Why this priority**: Grounds knowledge graph learning in established neuroscience principles. Enables organic knowledge organization that mirrors human memory consolidation.

**Independent Test**: Can be fully tested by tracking relationship strength changes over multiple activations. Delivers biologically-plausible learning dynamics.

**Non-Breaking**: Adds optional `hebbian_weight` property to relationships. Existing relationships without this property work unchanged.

**Acceptance Scenarios**:

1. **Given** two concepts frequently retrieved together, **When** they are co-activated multiple times, **Then** the connection weight between them increases according to the Hebbian principle.
2. **Given** a relationship that hasn't been activated recently, **When** time passes without co-activation, **Then** the connection weight decays according to the persistence parameter.
3. **Given** a new relationship is proposed, **When** the system evaluates it, **Then** initial weight is assigned based on co-activation evidence from the source context.

---

### User Story 4 - Role Matrix Network Specification (Priority: P3)

As a system designer, I need to formally specify network topology using role matrices so that I can define, validate, and version-control agent architectures declaratively.

**Why this priority**: Enables reproducible agent configurations and formal verification of network properties. Important for production deployment and compliance.

**Independent Test**: Can be fully tested by defining a network via role matrices and verifying the instantiated agent matches the specification. Delivers declarative configuration.

**Non-Breaking**: Role matrices are a new specification format. Existing agent configurations via code/config remain fully supported.

**Acceptance Scenarios**:

1. **Given** a role matrix specification defining connections and parameters, **When** I instantiate an agent from it, **Then** the agent's network state exactly matches the specification.
2. **Given** two role matrix specifications, **When** I compare them, **Then** I can identify structural differences (added/removed connections, changed parameters).
3. **Given** a running agent, **When** I export its current state as a role matrix, **Then** I receive a specification that can recreate an equivalent agent.

---

### User Story 5 - Multi-Level Adaptation Control (Priority: P3)

As a system operator, I need second-order learning controls so that adaptation speed itself adapts based on context—learning faster when encountering novelty and stabilizing when patterns are established.

**Why this priority**: Completes the three-level architecture (base → first-order self-model → second-order self-model). Enables truly autonomous adaptation without manual tuning.

**Independent Test**: Can be fully tested by exposing an agent to high-novelty and low-novelty contexts and measuring adaptation rate changes. Delivers context-sensitive learning.

**Non-Breaking**: Extends existing MetaplasticityController with optional second-order states. Existing metaplasticity behavior unchanged when new states not configured.

**Acceptance Scenarios**:

1. **Given** an agent encountering high prediction error (novelty), **When** the second-order controller detects this, **Then** adaptation speed increases to learn faster.
2. **Given** an agent in a stable context with low prediction error, **When** the second-order controller detects this, **Then** adaptation speed decreases to prevent unnecessary changes.
3. **Given** an agent under high stress/error conditions, **When** the stress-reduces-adaptation principle is active, **Then** learning temporarily slows to prevent destabilization.

---

### Edge Cases

- What happens when connection weights approach boundary values (0 or 1)?
  - System enforces soft bounds with asymptotic behavior preventing exact 0 or 1
- How does system handle circular self-model references (agent modeling its own modeling)?
  - Self-model states are one level deep by default; recursive modeling requires explicit configuration
- What happens when role matrix specifies impossible configurations (contradictory constraints)?
  - Validation fails with specific constraint violations before instantiation
- How does Hebbian learning handle negative relationships (inhibitory connections)?
  - Anti-Hebbian rule applies: co-activation weakens inhibitory connections
- What happens when an agent's network state becomes too large to observe efficiently?
  - Hierarchical summarization provides aggregate statistics with drill-down capability
- What happens to existing agents when this feature is deployed?
  - Nothing changes. All new functionality is opt-in. Existing agents continue operating exactly as before.
- What happens when multiple processes update the same network state concurrently?
  - Last-write-wins strategy applies; full audit trail ensures no data is lost since all changes trigger snapshots

## Requirements *(mandatory)*

### Functional Requirements

**Network Reification Layer (Additive - New Models)**

- **FR-001**: System MUST provide new NetworkState model to represent connection weights (W) as explicit, observable state values
- **FR-002**: System MUST provide new NetworkState model to represent activation thresholds (T) as explicit, observable state values
- **FR-003**: System MUST provide new NetworkState model to represent adaptation speed factors (H) as explicit, observable state values
- **FR-004**: System MUST provide query interface for snapshot and streaming access to network state values
- **FR-005**: System MUST persist network state snapshots to Neo4j via existing webhook infrastructure, triggered on significant change events (>5% delta) plus daily checkpoints
- **FR-005a**: System MUST enforce same access control on network state queries as agent audit logs (existing RBAC)

**Self-Modeling Task (Additive - Optional Capability)**

- **FR-006**: System MUST support optional auxiliary self-prediction tasks that predict next internal state
- **FR-007**: System MUST calculate prediction error between predicted and actual internal states when self-prediction is enabled
- **FR-008**: System MUST use self-prediction error as an optional regularization signal during learning
- **FR-009**: System MUST track self-prediction accuracy metrics over time when enabled

**Hebbian Learning Dynamics (Additive - Optional Enhancement)**

- **FR-010**: System MUST support optional Hebbian weight property on knowledge graph relationships
- **FR-011**: System MUST support configurable persistence parameter (μ) controlling learned weight durability
- **FR-012**: System MUST apply weight decay to relationships with Hebbian weights based on time since last activation
- **FR-013**: System MUST enforce weight boundaries to prevent runaway strengthening or complete elimination

**Role Matrix Specification (Additive - Neo4j Graph Structure)**

- **FR-014**: System MUST store role matrix connectivity (mb matrix) as Neo4j graph nodes and relationships
- **FR-015**: System MUST store role matrix connection weights (mcw matrix) as Neo4j relationship properties
- **FR-016**: System MUST store role matrix aggregation parameters (mcfp matrix) as Neo4j node properties
- **FR-017**: System MUST store role matrix speed factors (ms matrix) as Neo4j node properties
- **FR-018**: System MUST validate role matrix graph structure for internal consistency via Cypher constraints
- **FR-019**: System MUST instantiate agents from role matrix graph queries
- **FR-020**: System MUST export running agent state as role matrix graph structure

**Multi-Level Adaptation (Additive - Extension to Existing)**

- **FR-021**: System MUST support optional first-order self-model states for tracking W, T values
- **FR-022**: System MUST support optional second-order self-model states for controlling adaptation speed (H)
- **FR-023**: System MUST modulate adaptation speed based on prediction error magnitude when enabled
- **FR-024**: System MUST support optional stress-reduces-adaptation principle as configurable behavior

### Key Entities

- **NetworkState**: New model - complete snapshot of an agent's reified network including all W, T, H values with timestamps
- **SelfModelState**: New model - first-order representation of network characteristics as observable values (WX,Y, TY)
- **TimingState**: New model - second-order control state (HY) governing adaptation speed for each first-order state
- **RoleMatrix**: Neo4j graph structure - declarative specification of network topology stored as nodes/relationships representing five sub-matrices (mb, mcw, mcfp, mcfw, ms)
- **HebbianConnection**: Extension - adds optional dynamic weight, last activation time, and persistence parameter to relationships
- **PredictionRecord**: New model - self-prediction attempt with predicted state, actual state, error magnitude, and timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Network state queries return complete W, T, H values within 100ms for agents with up to 1000 connections
- **SC-002**: Agents with self-prediction enabled show 15-25% narrower weight distributions compared to baseline after 1000 learning cycles
- **SC-003**: Self-prediction accuracy exceeds 70% for stable agents (prediction error < 0.3 on normalized scale)
- **SC-004**: Hebbian-updated relationships show correlation > 0.8 between co-activation frequency and connection strength
- **SC-005**: Role matrix round-trip (export → import) produces functionally equivalent agents (state divergence < 1%)
- **SC-006**: Second-order adaptation achieves 2x faster learning on novel patterns vs. fixed-rate baseline
- **SC-007**: 100% of role matrix validation errors are detected before agent instantiation (no runtime failures from spec errors)
- **SC-008**: Historical network state analysis can reconstruct any agent's state from any point in the past 30 days
- **SC-009**: All existing tests pass without modification after feature deployment (zero regression)
- **SC-010**: Agents without new features enabled show identical behavior to pre-deployment baseline

## Assumptions

- All new functionality is opt-in via configuration flags (default: disabled)
- New models are stored in separate collections/tables, not modifying existing schemas
- Existing MetaplasticityController provides foundation for second-order adaptation (will be wrapped, not modified)
- Neo4j knowledge graph supports adding new edge properties via Graphiti without schema migration
- Agent audit trail infrastructure can accommodate network state snapshots without significant performance impact
- Smolagents framework allows injection of optional auxiliary tasks without modifying core agent loop
- System has sufficient storage for network state history (estimated 1KB per snapshot × ~10-50 snapshots/day/agent based on change-event + daily checkpoint strategy)

## Clarifications

### Session 2025-12-29

- Q: What is the network state snapshot frequency for historical reconstruction? → A: On significant change events (>5% delta from last snapshot) plus daily checkpoint snapshots
- Q: What access control applies to network state queries? → A: Same access as agent audit logs (existing RBAC)
- Q: What format for role matrix specifications? → A: Neo4j graph structure (nodes and relationships, not file-based serialization)
- Q: How are concurrent network state updates handled? → A: Last-write-wins with full audit trail (no data loss due to snapshot history)

## Dependencies

- Feature 030 (Energy Wells) - provides stability metrics that inform threshold adaptation
- Existing mental_model.py - new NetworkState wraps existing functionality
- Existing metaplasticity_service.py - new TimingState wraps existing controller
- Existing kg_learning_service.py - HebbianConnection adds optional properties
