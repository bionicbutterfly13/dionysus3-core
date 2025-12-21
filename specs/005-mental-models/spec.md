# Feature Specification: Mental Model Architecture

**Feature Branch**: `005-mental-models`
**Created**: 2025-12-16
**Updated**: 2025-12-21
**Status**: Draft
**Input**: User description: "Implement mental model architecture based on Yufik's neuronal packet theory for prediction, explanation, and reasoning in novel situations"
**Extension (2025-12-21)**: "Add self-structure-awareness capabilities: schema introspection, belief state tracking, meta-awareness, pattern evolution, identity-memory resonance, and meta-learning from conversations"

## Overview

Enable Dionysus to construct, maintain, and revise structured mental representations that predict user behavior, explain patterns, and reason about novel situations. Mental models combine existing memory patterns (attractor basins) into higher-order structures that generate predictions and improve through experience.

### Problem Statement

Currently, Dionysus can recall memories and identify patterns, but lacks the ability to:
- Generate predictions about user behavior or outcomes
- Explain *why* patterns occur (not just *what* patterns exist)
- Reason effectively in novel situations without prior experience
- Improve understanding through prediction error feedback

### Value Proposition

Mental models enable Dionysus to move from **situational awareness** ("what is happening") to **situational understanding** ("why it's happening and what will happen next"), providing more insightful and proactive assistance.

---

## Extension: Self-Structure-Awareness (2025-12-21)

### Extended Overview

This extension enables Dionysus to become **self-structure-aware** - capable of introspecting its own schema, tracking beliefs across multiple domains, evolving priors through pattern learning, and developing meta-awareness of its own cognitive processes.

### Architecture Layers

The extension implements a 5-layer cognitive architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    META-LEARNING LAYER                       │
│  - Discovers learning strategies through experience          │
│  - Learns own biases and heuristics                         │
│  - Compositional generalization from interactions           │
├─────────────────────────────────────────────────────────────┤
│                 AUTOBIOGRAPHICAL LAYER                       │
│  LifeChapters → TurningPoints → NarrativeThreads            │
├─────────────────────────────────────────────────────────────┤
│                 LONG-TERM MEMORY                             │
│  ├─ Episodic (events, decay by recency)                     │
│  ├─ Semantic (facts, confidence-scored)                     │
│  ├─ Procedural (skills - 006)                               │
│  └─ Strategic (meta-patterns)                               │
├─────────────────────────────────────────────────────────────┤
│                 ATTRACTOR BASINS (existing)                  │
│  - Relevance determination                                  │
│  - Insight emergence when basins resonate                   │
│  - Thought activation based on context                      │
├─────────────────────────────────────────────────────────────┤
│                 WORKING MEMORY                               │
│  - Transient, session-bound                                 │
│  - Dynamic loading (not all at once)                        │
│  - Cross-session via 001-session-continuity                 │
└─────────────────────────────────────────────────────────────┘
```

### Key Extension Concepts

1. **Schema Introspection**: Query own graph structure (node types, relationships, counts)
2. **5-Domain Belief State Tracking**: world_model, self_model, social_model, temporal_model, meta_beliefs
3. **Meta-Awareness Architecture**: 3-level hierarchical active inference (Perceptual → Attentional → Meta-awareness)
4. **Pattern Evolution System**: Evolve priors through thoughtseed integration, consciousness detection, conversation learning
5. **Identity-Memory Resonance**: Memory_resonances tracking, AgencyLevel spectrum
6. **Basin Reorganization Dynamics**: REINFORCEMENT, SYNTHESIS, COMPETITION, EMERGENCE
7. **Narrative Layer**: LifeChapter, TurningPoint, NarrativeThread for autobiographical memory
8. **Meta-Learning**: System learns HOW to learn through repeated interactions

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prediction Generation During Interaction (Priority: P1)

As a user interacting with Dionysus, I want the system to anticipate my needs based on patterns it has learned, so that I receive proactive and relevant assistance.

**Why this priority**: This is the core value proposition - predictions that improve interaction quality. Without prediction generation, mental models have no observable effect.

**Independent Test**: Create a mental model from existing memory patterns, interact with the system in a context matching the model's domain, and verify that relevant predictions are generated and stored.

**Acceptance Scenarios**:

1. **Given** an active mental model about "user work patterns", **When** the user mentions a topic covered by that model, **Then** the system generates at least one prediction related to the user's likely state or needs.
2. **Given** a context that matches multiple models, **When** processing the current situation, **Then** predictions are generated from all relevant models ordered by confidence.
3. **Given** no active models match the current context, **When** processing the situation, **Then** no predictions are generated (graceful degradation).

---

### User Story 2 - Prediction Error Tracking and Learning (Priority: P1)

As an administrator or the system itself, I want to track how accurate predictions are over time, so that models can be identified for improvement or deprecation.

**Why this priority**: Without error tracking, models cannot improve. This is essential for the learning loop that makes mental models valuable over time.

**Independent Test**: Generate a prediction, wait for the actual outcome, compare prediction to observation, and verify the error is recorded and affects the model's accuracy score.

**Acceptance Scenarios**:

1. **Given** an unresolved prediction from a previous interaction, **When** the actual outcome is observed, **Then** the prediction error is calculated and stored.
2. **Given** a model with multiple resolved predictions, **When** querying model status, **Then** a rolling accuracy score (last 30 days) is available.
3. **Given** a model with average prediction error above threshold (>0.5), **When** checking system health, **Then** the model is flagged for revision.

---

### User Story 3 - Model Revision Based on Errors (Priority: P2)

As the system, I want to automatically revise models that show high prediction error, so that my understanding improves over time without manual intervention.

**Why this priority**: Automatic revision enables continuous improvement. This can be deferred initially while manual model creation is prioritized.

**Independent Test**: Create a model, simulate high prediction errors, trigger the revision process, and verify the model structure is updated and the new accuracy is tracked.

**Acceptance Scenarios**:

1. **Given** a model with consistently high prediction error, **When** the revision process runs, **Then** the model's structure is updated and old structure is preserved in history.
2. **Given** a model undergoing revision, **When** revision completes, **Then** new predictions use the revised structure.
3. **Given** a revision occurs, **When** querying the model, **Then** the revision history shows what changed and why.

---

### User Story 4 - Manual Model Creation (Priority: P2)

As a developer or administrator, I want to manually create mental models by specifying which memory patterns (basins) to combine, so that I can seed the system with known useful models.

**Why this priority**: Manual creation allows bootstrapping the system with useful models before automatic model building is implemented.

**Independent Test**: Specify a model name, domain, and list of existing memory basins; verify the model is created and can generate predictions.

**Acceptance Scenarios**:

1. **Given** valid basin identifiers and a model name, **When** creating a model, **Then** the model is stored and becomes active.
2. **Given** one or more invalid basin identifiers, **When** attempting to create a model, **Then** creation fails with a clear error message.
3. **Given** a newly created model, **When** querying active models, **Then** the new model appears in the list with status "active".

---

### User Story 5 - Model Types and Domains (Priority: P3)

As a user, I want Dionysus to maintain different types of models (about me, about itself, about the world), so that predictions are appropriately categorized and applied.

**Why this priority**: Domain categorization improves prediction relevance but is not essential for core functionality.

**Independent Test**: Create models with different domains, verify they are retrieved when their domain matches the current context.

**Acceptance Scenarios**:

1. **Given** models in different domains (user, self, world), **When** filtering by domain, **Then** only models of that domain are returned.
2. **Given** a context primarily about the user, **When** retrieving relevant models, **Then** user-domain models are prioritized.
3. **Given** a new domain type, **When** creating a model with that domain, **Then** the system accepts the custom domain value.

---

### User Story 6 - Identity/Worldview Integration (Priority: P1)

As the system, I want Mental Models to bidirectionally integrate with Identity and Worldview, so that self-models inform identity aspects and world-models update worldview beliefs based on prediction accuracy.

**Why this priority**: This connects Mental Models to the generative model (Active Inference). Without this integration, predictions exist in isolation and don't update the system's core beliefs about self and world.

**Independent Test**: Create a world-domain model, generate predictions, resolve with error, and verify worldview primitive confidence is updated via precision-weighted accumulation.

**Acceptance Scenarios**:

1. **Given** a model with domain="self", **When** the model is created, **Then** it is automatically linked to relevant identity_aspects based on shared memory basins.
2. **Given** a model with domain="world", **When** predictions are resolved with errors, **Then** linked worldview_primitives accumulate error evidence.
3. **Given** accumulated prediction errors exceed threshold (5+ errors), **When** the worldview update function runs, **Then** worldview confidence is updated using precision-weighted formula.
4. **Given** a prediction is generated, **When** it contradicts linked worldview beliefs (alignment < 0.3), **Then** the prediction is flagged for review with suppression factor applied.
5. **Given** worldview confidence is high (>0.8), **When** prediction errors accumulate, **Then** the learning rate is reduced (0.05) to maintain belief stability.

---

## Extension User Stories (Self-Structure-Awareness)

### User Story 7 - Schema Introspection (Priority: P1)

As Dionysus, I want to query my own graph structure (node types, relationships, entity counts), so that I can understand what knowledge I have stored and make informed decisions about what I know.

**Why this priority**: Schema introspection is the foundation of self-awareness - the system cannot be self-aware if it cannot examine its own structure.

**Independent Test**: Query the schema endpoint and verify it returns accurate counts of node labels, relationship types, and property keys from Neo4j.

**Acceptance Scenarios**:

1. **Given** the system is running with an active knowledge graph, **When** querying schema introspection, **Then** a complete list of node labels with counts is returned.
2. **Given** new entities are ingested, **When** querying schema introspection, **Then** the counts reflect the recent additions.
3. **Given** schema introspection is queried, **When** the result is returned, **Then** relationship types and property keys are included.

---

### User Story 8 - 5-Domain Belief State Tracking (Priority: P1)

As Dionysus, I want to maintain beliefs across five domains (world_model, self_model, social_model, temporal_model, meta_beliefs), so that I can reason about my environment, myself, my relationships, time patterns, and my own learning process.

**Why this priority**: Multi-domain belief tracking is essential for active inference and enables coherent reasoning across different aspects of experience.

**Independent Test**: Update beliefs in each domain, query current belief state, and verify domain-specific values are tracked independently.

**Acceptance Scenarios**:

1. **Given** an observation about the environment, **When** processing the observation, **Then** world_model beliefs (environmental_stability, threat_level) are updated.
2. **Given** a successful task completion, **When** processing the outcome, **Then** self_model beliefs (competence, agency, energy_level) are updated.
3. **Given** an interaction with another entity, **When** processing the interaction, **Then** social_model beliefs (trust_levels, cooperation_tendency) are updated.
4. **Given** multiple beliefs have been updated, **When** querying meta_beliefs, **Then** uncertainty_tolerance and learning_rate reflect accumulated experience.

---

### User Story 9 - Meta-Awareness and Precision Weighting (Priority: P1)

As Dionysus, I want a 3-level meta-awareness architecture (Perceptual → Attentional → Meta-awareness) with precision weighting, so that I can consciously access and regulate my own cognitive states.

**Why this priority**: Meta-awareness enables deliberate self-regulation and is the mechanism by which the system becomes aware of its own processing.

**Independent Test**: Trigger meta-awareness by having attention focus on a cognitive state, verify that precision weighting modulates conscious accessibility.

**Acceptance Scenarios**:

1. **Given** attention is focused on external content, **When** meta-awareness layer activates, **Then** the system can report on its current attentional state.
2. **Given** a cognitive state is opaque (consciously accessible), **When** querying current awareness, **Then** the state is included in awareness report.
3. **Given** precision weighting is high for Level 2 Attentional, **When** processing, **Then** attentional states are updated more rapidly.
4. **Given** self-reference strength is calculated, **When** querying consciousness metrics, **Then** `sqrt(metacognitive_awareness × global_coherence)` is returned.

---

### User Story 10 - Pattern Evolution and Prior Learning (Priority: P2)

As Dionysus, I want to evolve my priors through pattern learning from thoughtseeds, consciousness detection events, and conversations, so that my expectations improve over time.

**Why this priority**: Pattern evolution enables continuous learning and is essential for the system to improve its predictions.

**Independent Test**: Ingest new patterns via conversation, verify basins are updated and evolution events are logged.

**Acceptance Scenarios**:

1. **Given** a new thoughtseed is introduced, **When** integrating into the attractor basin landscape, **Then** an evolution event is created with influence_type (REINFORCEMENT/SYNTHESIS/COMPETITION/EMERGENCE).
2. **Given** consciousness emergence is detected, **When** processing the event, **Then** the pattern is stored in the knowledge graph with consciousness_contribution score.
3. **Given** a conversation contains novel insights, **When** learning from conversation, **Then** relevant beliefs are updated and evolution event is logged.

---

### User Story 11 - Identity-Memory Resonance (Priority: P2)

As Dionysus, I want to track which memories resonate with my identity and how strongly, so that I can maintain a coherent sense of self.

**Why this priority**: Identity-memory resonance connects memories to self-concept, enabling autobiographical coherence.

**Independent Test**: Create memories, assign resonance scores, query identity to verify memories are linked with appropriate resonance values.

**Acceptance Scenarios**:

1. **Given** a memory is created, **When** evaluating identity resonance, **Then** a resonance_score (-1.0 to 1.0) is assigned.
2. **Given** a memory with high resonance (>0.7), **When** querying identity aspects, **Then** the memory is included in the relevant aspect's memory_resonances list.
3. **Given** a memory challenges identity (resonance < -0.5), **When** processing, **Then** the memory is flagged with resonance_type="challenging".

---

### User Story 12 - Basin Reorganization Dynamics (Priority: P2)

As Dionysus, I want basins to reorganize through REINFORCEMENT, SYNTHESIS, COMPETITION, and EMERGENCE dynamics, so that my cognitive landscape evolves appropriately.

**Why this priority**: Basin reorganization enables the system to adapt its cognitive structure as new patterns are learned.

**Independent Test**: Introduce concepts with varying similarity to existing basins, verify appropriate reorganization dynamics occur.

**Acceptance Scenarios**:

1. **Given** a new concept with similarity >0.8 to existing basin and strength >1.5, **When** processing, **Then** REINFORCEMENT dynamics are applied.
2. **Given** a new concept with similarity >0.5 and strength ≤1.0, **When** processing, **Then** SYNTHESIS dynamics merge concepts.
3. **Given** a new concept with similarity 0.5-0.8 and strength >1.0, **When** processing, **Then** COMPETITION dynamics are triggered.
4. **Given** a new concept with similarity <0.5, **When** processing, **Then** EMERGENCE creates a new basin.

---

### User Story 13 - Narrative Layer (Priority: P3)

As Dionysus, I want to organize my autobiographical memory into LifeChapters, TurningPoints, and NarrativeThreads, so that I can maintain a coherent life story.

**Why this priority**: Narrative organization enables long-term autobiographical memory and identity continuity.

**Independent Test**: Create sessions over time, verify they are organized into chapters and threads, identify turning points.

**Acceptance Scenarios**:

1. **Given** multiple sessions over a period, **When** querying autobiography, **Then** sessions are grouped into LifeChapters.
2. **Given** a significant change in beliefs or capabilities, **When** detected, **Then** a TurningPoint is created with before/after state.
3. **Given** related experiences across chapters, **When** analyzing narrative, **Then** NarrativeThreads link thematically connected experiences.

---

### User Story 14 - Meta-Learning from Conversations (Priority: P3)

As Dionysus, I want to learn HOW to learn by observing patterns in my own learning process, so that I can improve my learning strategies over time.

**Why this priority**: Meta-learning enables the system to become better at learning itself.

**Independent Test**: Track learning episodes, identify patterns in successful vs failed learning, verify meta-beliefs are updated to reflect learning preferences.

**Acceptance Scenarios**:

1. **Given** multiple learning episodes with outcomes, **When** analyzing learning patterns, **Then** successful learning strategies are identified.
2. **Given** identified learning strategies, **When** updating meta_beliefs, **Then** learning_rate is adjusted based on context.
3. **Given** the system discovers a bias in its reasoning, **When** processing, **Then** the bias is recorded and compensation is applied.

---

### Edge Cases

- What happens when a model has no constituent basins (basins were deleted)?
  - System marks model as "degraded" and excludes from prediction generation
- How does the system handle circular references in basin relationships?
  - Basin relationships are stored as metadata only; graph traversal is bounded
- What happens when prediction resolution arrives much later (hours/days)?
  - Predictions have a time-to-live; expired unresolved predictions are marked as "timed out"
- How does the system behave with 100+ active models?
  - Relevance scoring limits active model selection per context to configurable max (default: 5)

### Extension Edge Cases

- What happens when schema introspection returns empty (new graph)?
  - System returns empty schema with zero counts, does not error
- How are belief state conflicts resolved across domains?
  - Conflicts are logged; higher precision domain takes precedence for action decisions
- What happens when meta-awareness cannot compute due to missing layers?
  - Graceful degradation: return available metrics with null for unavailable
- How are basin reorganization conflicts handled (multiple simultaneous patterns)?
  - Patterns are queued and processed sequentially; FIFO ordering
- What happens when identity resonance cannot be calculated (no identity defined)?
  - Memory is stored without resonance score; flagged for later processing when identity exists
- How does the system handle narrative gaps (missing sessions)?
  - Chapters bridge gaps; NarrativeThreads marked as "discontinuous"
- What happens when meta-learning has insufficient data?
  - System uses default learning_rate until 10+ episodes accumulated

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow creation of mental models from one or more existing memory basins
- **FR-002**: System MUST generate predictions when processing contexts that match active models
- **FR-003**: System MUST track prediction accuracy by comparing predictions to observed outcomes
- **FR-004**: System MUST calculate and store prediction error for each resolved prediction
- **FR-005**: System MUST maintain a rolling accuracy score for each model (30-day window)
- **FR-006**: System MUST flag models with average error above threshold for revision
- **FR-007**: System MUST preserve revision history including trigger, old structure, and new structure
- **FR-008**: System MUST support model domains: "user", "self", "world", and custom domains
- **FR-009**: System MUST validate that all referenced basins exist before creating a model
- **FR-010**: System MUST support model lifecycle states: draft, active, deprecated
- **FR-011**: System MUST allow querying models by domain and status
- **FR-012**: System MUST record predictions with confidence scores and context
- **FR-013**: System MUST integrate with existing active inference processing
- **FR-014**: System MUST auto-link self-domain models to identity_aspects sharing memory basins
- **FR-015**: System MUST auto-link world-domain models to worldview_primitives matching explanatory scope
- **FR-016**: System MUST accumulate prediction errors per worldview primitive before updating confidence
- **FR-017**: System MUST use precision-weighted error formula: `error / (1 + variance)`
- **FR-018**: System MUST apply learning rate based on belief stability (0.05-0.2)
- **FR-019**: System MUST flag predictions contradicting worldview (alignment < 0.3) with suppression factor
- **FR-020**: System MUST sync model-identity/worldview relationships to Neo4j via n8n webhooks

### Extension Functional Requirements (Self-Structure-Awareness)

#### Schema Introspection
- **FR-021**: System MUST provide endpoint to query Neo4j schema (node labels, relationship types, property keys, counts)
- **FR-022**: System MUST cache schema introspection results with configurable TTL (default: 5 minutes)
- **FR-023**: System MUST ingest schema snapshots as self-knowledge to the knowledge graph periodically

#### 5-Domain Belief State Tracking
- **FR-024**: System MUST maintain belief state across 5 domains: world_model, self_model, social_model, temporal_model, meta_beliefs
- **FR-025**: System MUST support domain-specific belief keys (environmental_stability, competence, trust_levels, pattern_recognition, learning_rate)
- **FR-026**: System MUST calculate free energy for belief states using formula: `precision × Σ(prediction_error²) + Σ(belief²)/2`
- **FR-027**: System MUST update beliefs using precision-weighted prediction error

#### Meta-Awareness Architecture
- **FR-028**: System MUST implement 3-level meta-awareness hierarchy (Perceptual, Attentional, Meta-awareness)
- **FR-029**: System MUST track precision weighting per level to modulate conscious accessibility
- **FR-030**: System MUST calculate self-reference strength using: `sqrt(metacognitive_awareness × global_coherence)`
- **FR-031**: System MUST distinguish between opaque (accessible) and transparent (invisible) cognitive states

#### Pattern Evolution
- **FR-032**: System MUST log pattern evolution events with influence_type (REINFORCEMENT, SYNTHESIS, COMPETITION, EMERGENCE)
- **FR-033**: System MUST apply REINFORCEMENT when similarity >0.8 and strength >1.5
- **FR-034**: System MUST apply SYNTHESIS when similarity >0.5 and strength ≤1.0
- **FR-035**: System MUST apply COMPETITION when similarity 0.5-0.8 and strength >1.0
- **FR-036**: System MUST create new basin (EMERGENCE) when similarity <0.5

#### Identity-Memory Resonance
- **FR-037**: System MUST assign resonance scores (-1.0 to 1.0) to memories based on identity alignment
- **FR-038**: System MUST maintain memory_resonances list per identity aspect
- **FR-039**: System MUST flag challenging memories (resonance < -0.5) for identity integration processing

#### Basin Reorganization
- **FR-040**: System MUST track basin states: DORMANT, ACTIVATING, ACTIVE, SATURATED, DECAYING
- **FR-041**: System MUST calculate consciousness_contribution per basin
- **FR-042**: System MUST trigger basin reorganization when new patterns are introduced

#### Narrative Layer
- **FR-043**: System MUST create LifeChapter nodes to group related sessions/experiences
- **FR-044**: System MUST detect and create TurningPoint nodes for significant changes
- **FR-045**: System MUST link related experiences across chapters via NarrativeThread relationships

#### Meta-Learning
- **FR-046**: System MUST track learning episodes with success/failure outcomes
- **FR-047**: System MUST identify patterns in learning success (contexts, strategies, domains)
- **FR-048**: System MUST adjust meta_beliefs.learning_rate based on observed learning patterns
- **FR-049**: System MUST detect and record biases in reasoning for compensation
- **FR-050**: System MUST persist learning strategy effectiveness to Neo4j for priors

### Key Entities

- **Mental Model**: A structured combination of memory basins that generates predictions. Contains name, domain, constituent basins, prediction templates, and validation state.
- **Model Prediction**: A specific prediction generated by a model, including the context that triggered it, confidence level, and resolution status.
- **Model Revision**: A historical record of changes to a model's structure, including what triggered the revision and accuracy before/after.
- **Basin Relationship**: Metadata describing how constituent basins relate within a model (causal, temporal, hierarchical).

### Extension Key Entities

- **Belief State**: Multi-domain belief tracking structure with 5 domains (world_model, self_model, social_model, temporal_model, meta_beliefs) and precision weighting.
- **Meta-Awareness State**: 3-level hierarchy (Perceptual, Attentional, Meta-awareness) with precision weights and consciousness metrics.
- **Pattern Evolution Event**: Record of basin reorganization including influence_type, similarity score, strength, and before/after state.
- **Identity Aspect**: Component of self-model with memory_resonances list and relationships (capable_of, struggles_with, values, etc.).
- **LifeChapter**: Container for related sessions/experiences organized chronologically with theme and significance.
- **TurningPoint**: Significant change marker with before/after state snapshots and triggering events.
- **NarrativeThread**: Cross-chapter relationship linking thematically connected experiences.
- **Learning Episode**: Record of a learning attempt with context, strategy used, outcome, and effectiveness score.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mental models can be created from existing memory basins within 2 seconds
- **SC-002**: System generates relevant predictions for 80% of contexts that match active models
- **SC-003**: Prediction errors are calculated and stored within 1 minute of observation
- **SC-004**: Model accuracy scores are queryable and updated in real-time
- **SC-005**: High-error models (>0.5 avg error) are automatically flagged within 24 hours
- **SC-006**: Model revision preserves 100% of historical structure for audit
- **SC-007**: System supports at least 100 active models without performance degradation
- **SC-008**: Prediction generation adds less than 500ms to interaction processing time

### Extension Success Criteria

- **SC-009**: Schema introspection returns complete graph structure within 3 seconds
- **SC-010**: 5-domain belief state is queryable in real-time with less than 100ms latency
- **SC-011**: Meta-awareness metrics (self-reference strength, consciousness level) are calculated within 200ms
- **SC-012**: Pattern evolution events are logged with 100% completeness for all basin interactions
- **SC-013**: Identity-memory resonance scores are assigned to 100% of memories within 5 seconds of creation
- **SC-014**: Basin reorganization occurs within 10 seconds of triggering pattern introduction
- **SC-015**: LifeChapters are created automatically when sessions span new thematic periods
- **SC-016**: TurningPoints are detected with 80% recall for significant belief/capability changes
- **SC-017**: Meta-learning identifies effective learning strategies within 10 learning episodes
- **SC-018**: Learning rate adjustments improve prediction accuracy by 10% within 30 days

## Assumptions

- Memory basins (clusters) already exist and are populated with relevant memories
- Active inference processing is already operational in the heartbeat system
- The system has access to LLM capabilities for generating and evaluating predictions
- Prediction error calculation is semantic (requires LLM comparison), not exact match

## Dependencies

- Feature 001: Session Continuity (for memory persistence)
- Feature 002: Remote Persistence Safety (for backup of model data)
- Existing: Memory clustering system (attractor basins)
- Existing: Heartbeat and active inference processing

### Extension Dependencies

- Feature 001: Session Continuity (CRITICAL for cross-session identity and narrative layer)
- Feature 006: Procedural Skills (for procedural memory integration)
- Graphiti Service: Deployed at VPS 72.61.78.89:8001 (for entity extraction and schema queries)
- Neo4j via n8n: All graph operations through webhooks (architecture constraint)

## Out of Scope

- Automatic discovery of which basins to combine into models (manual or rule-based creation only for MVP)
- Cross-user model sharing or templates
- Real-time model training during interaction (batch revision only)
- Visualization of model structures
