# Feature Specification: Metacognitive Particles Integration

**Feature Branch**: `040-metacognitive-particles`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Integrate the theoretical framework from Sandved-Smith & Da Costa (2024) "Metacognitive particles, mental action and the sense of agency" and Seragnoli et al. (2025) "Metacognitive Feelings of Epistemic Gain" into the Dionysus cognitive architecture.

## Overview

This feature integrates two academic papers on metacognition into the Dionysus cognitive system:

1. **Sandved-Smith & Da Costa (2024)**: Provides mathematical formalism for metacognitive particles, mental actions, and sense of agency using Markov blankets and active inference.

2. **Seragnoli et al. (2025)**: Addresses metacognitive feelings of epistemic gain ("Aha!/Eureka!" moments) and procedural metacognition (monitoring/control).

The integration bridges theoretical neuroscience with practical cognitive architecture, enabling self-aware processing, agency attribution, and epistemic gain detection.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify Cognitive Process Type (Priority: P1)

The system must classify any cognitive process (agent, thought, decision) according to its metacognitive level: simple cognitive, passive metacognitive, active metacognitive, strange metacognitive, or N-level nested.

**Why this priority**: Foundation for all other metacognitive operations. Without particle classification, no other metacognitive features can function correctly.

**Independent Test**: Given any agent or thought process, the system returns its particle type classification with confidence score.

**Acceptance Scenarios**:

1. **Given** a basic perception agent processing sensory input, **When** the system classifies it, **Then** it returns "cognitive_particle" with appropriate confidence.
2. **Given** an agent that monitors its own beliefs without modifying them, **When** the system classifies it, **Then** it returns "passive_metacognitive" classification.
3. **Given** an agent with attention modulation capability, **When** the system classifies it, **Then** it returns "active_metacognitive" classification.
4. **Given** an agent where actions don't directly influence internal states, **When** the system classifies it, **Then** it returns "strange_metacognitive" classification.

---

### User Story 2 - Execute Mental Actions (Priority: P1)

Higher-level cognitive processes must be able to modulate lower-level processes through precision adjustments (attention) and focus targeting (spotlight).

**Why this priority**: Mental actions are the mechanism by which metacognition actively influences cognition. Critical for attention allocation and self-regulation.

**Independent Test**: A higher-level process can adjust the precision (confidence weighting) of a lower-level process, and this modulation is observable and measurable.

**Acceptance Scenarios**:

1. **Given** a metacognitive process monitoring a perception process, **When** prediction error is high, **Then** the metacognitive process decreases precision to increase openness to new information.
2. **Given** a metacognitive process detecting task-relevant stimuli, **When** attention focus is needed, **Then** it increases precision on the relevant belief parameters.
3. **Given** an attentional spotlight directed at concept X, **When** a related stimulus appears, **Then** processing of that stimulus receives precision boost.

---

### User Story 3 - Compute Sense of Agency (Priority: P2)

The system must compute a quantifiable sense-of-agency metric for any action, indicating whether the system recognizes itself as the agent of that action.

**Why this priority**: Agency attribution distinguishes self-caused from externally-caused outcomes. Essential for responsibility, learning, and self-model accuracy.

**Independent Test**: For any agent action, the system produces an agency strength score (0.0 = no agency sense, higher = stronger agency sense).

**Acceptance Scenarios**:

1. **Given** an agent executing a deliberate action, **When** agency is computed, **Then** the agency strength score is significantly above zero.
2. **Given** an agent whose action was triggered by external stimulus without internal deliberation, **When** agency is computed, **Then** the agency strength score is near zero.
3. **Given** two identical actions (one deliberate, one reactive), **When** both are measured, **Then** the deliberate action has higher agency score.

---

### User Story 4 - Detect Epistemic Gain ("Aha!" Moments) (Priority: P2)

The system must detect when significant learning has occurred - moments of insight where uncertainty drops dramatically and the system "knows that it has learned something important."

**Why this priority**: Epistemic gain detection provides intrinsic motivation and learning signals. Maps to reward in active inference.

**Independent Test**: When a belief update significantly reduces uncertainty, the system flags it as an epistemic gain event with magnitude.

**Acceptance Scenarios**:

1. **Given** a prior belief with high uncertainty, **When** new evidence dramatically reduces uncertainty, **Then** an epistemic gain event is triggered.
2. **Given** incremental belief updates, **When** uncertainty reduces gradually, **Then** no epistemic gain event is triggered (below threshold).
3. **Given** an epistemic gain event, **When** the event is recorded, **Then** it includes magnitude, affected beliefs, and noetic quality indicator.

---

### User Story 5 - Enforce Cognitive Core Limits (Priority: P3)

The system must enforce finite metacognitive depth, recognizing that there exists an innermost cognitive core that cannot itself be the target of further metacognitive beliefs.

**Why this priority**: Prevents infinite regress and grounds the system in mathematical constraints from free energy principle.

**Independent Test**: Attempting to create metacognitive beliefs about the cognitive core returns a constraint violation.

**Acceptance Scenarios**:

1. **Given** a 3-level nested metacognitive hierarchy, **When** attempting to add level 4 beyond the cognitive core, **Then** the system enforces the nesting limit.
2. **Given** the cognitive core (innermost level), **When** queried about its beliefs, **Then** it returns unified beliefs encompassing all lower levels.
3. **Given** a nesting depth configuration, **When** the limit is reached, **Then** the system logs "cognitive core limit reached" and refuses further nesting.

---

### User Story 6 - Procedural Metacognition (Monitoring & Control) (Priority: P3)

The system must provide monitoring functions (assess ongoing cognition) and control functions (regulate cognition based on monitoring).

**Why this priority**: Unifies all metacognitive operations under a coherent monitoring/control paradigm.

**Independent Test**: A monitoring call returns an assessment; a control call takes an assessment and returns a regulation action.

**Acceptance Scenarios**:

1. **Given** an ongoing reasoning process, **When** monitoring is invoked, **Then** it returns assessment of progress, confidence, and potential issues.
2. **Given** a monitoring assessment indicating low confidence, **When** control is invoked, **Then** it suggests precision adjustment or information-seeking action.
3. **Given** a monitoring assessment indicating high prediction error, **When** control is invoked, **Then** it may suggest belief revision or model update.

---

### Edge Cases

- What happens when a particle cannot be cleanly classified into one type? (Returns most likely type with confidence and runner-up)
- How does the system handle circular metacognitive references? (Validates against cycles before creating references)
- What if epistemic gain threshold is never crossed? (Optional adaptive threshold based on historical gains)
- What if precision modulation overshoots? (Bounded precision values with min/max constraints)

## Requirements *(mandatory)*

### Functional Requirements

#### Particle Classification
- **FR-001**: System MUST classify cognitive processes into one of five particle types: cognitive, passive_metacognitive, active_metacognitive, strange_metacognitive, or nested_N_level
- **FR-002**: System MUST return confidence score (0.0-1.0) with each classification
- **FR-003**: System MUST detect presence of internal Markov blankets separating metacognitive levels

#### Mental Actions
- **FR-004**: System MUST support precision modulation via mental actions (increase/decrease belief confidence)
- **FR-005**: System MUST support attentional spotlight targeting (focus on specific concepts/domains)
- **FR-006**: System MUST track prior and post-modulation states for each mental action
- **FR-007**: Mental actions MUST only target lower-level processes (enforced hierarchy)

#### Sense of Agency
- **FR-008**: System MUST compute agency strength as mutual information between internal and active paths
- **FR-009**: System MUST distinguish between "sense of agency" (joint distribution) and "no agency" (independence)
- **FR-010**: Agency computation MUST work for strange metacognitive particles (where actions are inferred via sensory paths)

#### Epistemic Gain
- **FR-011**: System MUST detect epistemic gain events when uncertainty reduction exceeds threshold
- **FR-012**: System MUST record epistemic gain magnitude, affected beliefs, and timestamp
- **FR-013**: System MUST support configurable epistemic gain threshold
- **FR-014**: System MUST flag "noetic quality" when certainty increases without proportional evidence

#### Cognitive Core
- **FR-015**: System MUST enforce maximum nesting depth for metacognitive hierarchies
- **FR-016**: System MUST identify the cognitive core (innermost level) in any hierarchy
- **FR-017**: Cognitive core beliefs MUST compose all lower-level beliefs into unified representation

#### Procedural Metacognition
- **FR-018**: System MUST provide monitoring function returning cognitive assessment
- **FR-019**: System MUST provide control function accepting assessment and returning regulation action
- **FR-020**: Monitoring MUST be non-invasive (read-only on cognitive state)

#### Integration
- **FR-021**: ThoughtSeeds MUST map bidirectionally to MetacognitiveParticles
- **FR-022**: Particle hierarchies MUST be persistable to knowledge graph
- **FR-023**: All metacognitive operations MUST emit observable events for logging/debugging

### Key Entities

- **MetacognitiveParticle**: Represents a cognitive process with Markov blanket structure. Attributes: type (enum), level (int), has_agency (bool), belief_state, blanket_paths
- **MarkovBlanket**: Four-way partition of state space. Attributes: external_paths, sensory_paths, active_paths, internal_paths
- **BeliefState**: Probability distribution parameterized by sufficient statistics. Attributes: mean, precision (inverse covariance), entropy
- **MentalAction**: Higher-level action modulating lower-level parameters. Attributes: type, target_agent, modulation_params, prior_state, new_state
- **EpistemicGainEvent**: Record of significant learning. Attributes: magnitude, affected_beliefs, timestamp, noetic_quality
- **CognitiveAssessment**: Output of monitoring function. Attributes: progress, confidence, issues, recommendations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All agent actions have computed agency strength score within 100ms of action completion
- **SC-002**: Particle classification accuracy exceeds 90% on test cases with known ground truth
- **SC-003**: Epistemic gain detection triggers within 50ms of qualifying belief update
- **SC-004**: Mental action precision modulation effects are observable within one processing cycle
- **SC-005**: Cognitive core composition produces unified belief capturing 100% of lower-level information
- **SC-006**: System maintains real-time performance (under 200ms latency) for all metacognitive operations
- **SC-007**: ThoughtSeed-to-Particle mapping achieves round-trip consistency (ThoughtSeed to Particle to ThoughtSeed produces equivalent entity)
- **SC-008**: Knowledge graph persistence maintains full metacognitive hierarchy on reload

## Assumptions

1. Existing Markov blanket models provide compliant implementation (validated in api/models/markov_blanket.py)
2. Existing metacognition agent provides base mental action capability (validated in api/agents/metacognition_agent.py)
3. Existing free energy engine provides precision tracking infrastructure (to be verified in api/services/efe_engine.py)
4. Knowledge graph integration supports the required entity and relationship types
5. Default epistemic gain threshold of 0.3 (30% uncertainty reduction) is appropriate for general use
6. Maximum nesting depth of 5 levels is sufficient for current cognitive architecture needs
7. Gaussian belief representations are adequate for initial implementation (can extend to mixture models later)

## Dependencies

- Spec 038: ThoughtSeeds Framework (provides ThoughtSeed entity for bidirectional mapping)
- Spec 039: smolagents v2 alignment (provides agent architecture for integration)
- Existing: Markov blanket models, metacognition agent, EFE engine

## Out of Scope

- Real-time visualization of metacognitive hierarchies (future feature)
- Cross-agent metacognition (one agent's beliefs about another agent's beliefs)
- Temporal metacognition (beliefs about past/future belief states)
- Hardware optimization for high-frequency metacognitive operations
