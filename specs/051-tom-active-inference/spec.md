# Feature Specification: Theory-of-Mind Active Inference Integration

**Feature Branch**: `051-tom-active-inference`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "Integrate MetaMind ToM pipeline with active inference architecture for [LEGACY_AVATAR_HOLDER] empathy modeling"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ToM-Enhanced Empathetic Responses (Priority: P1)

When an [LEGACY_AVATAR_HOLDER] user interacts with the IAS system (chat, belief journey, WOOP planning), the system generates multiple hypotheses about the user's mental state (beliefs, desires, intentions, emotions, thoughts) and selects the most appropriate response based on active inference principles.

**Why this priority**: This is the core value proposition - directly improves empathetic response quality for [LEGACY_AVATAR_HOLDER]s by modeling their psychological states rather than generic responses.

**Independent Test**: Can be fully tested by submitting user utterances to the IAS chat endpoint and measuring empathy scores of responses. Delivers immediate value through improved response quality without requiring subsequent stories.

**Acceptance Scenarios**:

1. **Given** user sends "I feel like I'm failing even though I hit all my metrics", **When** system processes the message, **Then** system generates 7 ToM hypotheses covering belief (metric-driven self-worth), desire (validation beyond numbers), intention (seeking reassurance), emotion (inadequacy), and thought patterns (cognitive dissonance)

2. **Given** ToM hypotheses are generated, **When** system selects response strategy, **Then** system uses expected free energy calculation to select hypothesis with minimal EFE (balancing epistemic uncertainty and pragmatic goal alignment)

3. **Given** winning hypothesis is "User believes metrics are insufficient for self-worth", **When** system generates response, **Then** response acknowledges the metrics achievement while addressing the underlying belief about worth

4. **Given** user is in crisis mode (high stress utterance), **When** ToM hypotheses are generated, **Then** system includes emotional hypotheses weighted toward hypervigilance and threat detection patterns

---

### User Story 2 - Response Quality Validation (Priority: P2)

After generating a response based on ToM hypothesis, the system validates the response for empathy (alignment with inferred mental state) and coherence (consistency with conversation context), iteratively refining until quality thresholds are met.

**Why this priority**: Prevents low-quality responses from reaching users. Particularly critical for [LEGACY_AVATAR_HOLDER]s who are hypervigilant and sensitive to misalignment.

**Independent Test**: Can be tested by generating responses and measuring utility scores (empathy + coherence). Delivers value by ensuring quality gating without requiring ToM integration.

**Acceptance Scenarios**:

1. **Given** response is generated from ToM hypothesis, **When** validation is triggered, **Then** system calculates empathy score (0.0-1.0) measuring alignment with inferred mental state

2. **Given** response is generated, **When** validation is triggered, **Then** system calculates coherence score (0.0-1.0) measuring consistency with conversation context and user history

3. **Given** response has utility score < 0.9 (empathy * 0.8 + coherence * 0.2), **When** refinement is triggered, **Then** system generates critique and optimizes response, repeating up to 3 times

4. **Given** response validation fails after 3 refinement attempts, **When** final response is selected, **Then** system logs quality warning and falls back to best available response with explicit confidence indicator

---

### User Story 3 - Social Memory Persistence (Priority: P3)

User preferences and emotional patterns extracted during interactions are stored in the Graphiti temporal knowledge graph, enabling long-term relationship modeling and context-aware future interactions.

**Why this priority**: Enables session continuity and personalization. Builds on P1/P2 by adding persistence layer for discovered mental states.

**Independent Test**: Can be tested by ingesting interactions, querying Graphiti for extracted preferences/emotions, and verifying temporal recall. Delivers value through personalized memory without requiring response generation.

**Acceptance Scenarios**:

1. **Given** user interaction contains preference statement ("I prefer email over phone"), **When** social memory extraction is triggered, **Then** system extracts preference and stores in Graphiti with timestamp and evidence

2. **Given** user utterance expresses emotion, **When** social memory extraction is triggered, **Then** system identifies emotion type, intensity (0.0-1.0), context, and creates EmotionalState entity in Graphiti

3. **Given** user returns for new session, **When** bootstrap recall retrieves context, **Then** system includes relevant user preferences and emotional history from previous interactions

4. **Given** user preference conflicts with new statement, **When** social memory is updated, **Then** system creates temporal fact evolution in Graphiti (preference changed from X to Y at timestamp T)

---

### User Story 4 - Identity Coherence Monitoring (Priority: P4)

System monitors responses for alignment with the [LEGACY_AVATAR_HOLDER] identity framework (Before Identity pain points, After Identity aspirations) and IAS curriculum principles, triggering control actions when misalignment is detected.

**Why this priority**: Ensures brand consistency and framework adherence. Builds on previous stories by adding identity-level validation layer.

**Independent Test**: Can be tested by submitting responses for identity alignment scoring against Before/After Identity models. Delivers value through brand voice consistency.

**Acceptance Scenarios**:

1. **Given** response is generated, **When** identity coherence check is triggered, **Then** system calculates alignment score with user's Before Identity (acknowledges pain points like hypervigilance, metric obsession)

2. **Given** response is generated, **When** identity coherence check is triggered, **Then** system calculates alignment score with user's After Identity (aspiring self with balanced self-worth, sustainable achievement)

3. **Given** response has identity alignment < 0.7, **When** metacognition monitoring detects misalignment, **Then** system generates IDENTITY_MISALIGNMENT issue with severity 0.8 and triggers response regeneration

4. **Given** response uses generic AI language (not Perry Belcher voice style), **When** voice validation is triggered, **Then** system flags violation and enforces 5th grade reading level + direct communication style

---

### Edge Cases

- What happens when ToM hypotheses all have similar EFE scores (no clear winner)?
  - System selects hypothesis with highest diversity contribution (least represented mental state type in recent history)

- How does system handle contradictory user statements within same interaction?
  - System creates multiple hypotheses representing internal conflict and selects response addressing the tension

- What happens when empathy and coherence are in conflict (empathetic response would be incoherent)?
  - System prioritizes empathy (β=0.8 weighting) but adds context to maintain minimal coherence

- How does system handle cultural or ethical domain constraint violations in ToM hypotheses?
  - System filters hypotheses through identity coherence monitoring before EFE calculation, rejecting violations

- What happens when user is new with no social memory history?
  - System uses [LEGACY_AVATAR_HOLDER] archetype defaults from avatar research knowledge base

- How does system handle precision modulation when surprise is high but confidence is also high?
  - System prioritizes surprise signal (potential prediction error) and lowers precision to enable exploration

## Requirements *(mandatory)*

### Functional Requirements

#### ToM Hypothesis Generation

- **FR-001**: System MUST generate 7 ToM hypotheses per user interaction covering 5 mental state types (Belief, Desire, Intention, Emotion, Thought) using round-robin diversity mechanism

- **FR-002**: System MUST create ToM hypotheses using user utterance, conversation context, and social memory summary as inputs

- **FR-003**: System MUST convert each ToM hypothesis to ThoughtSeed format with cognitive layer assignment (conceptual/metacognitive/abstract/perceptual) based on mental state type

- **FR-004**: System MUST assign activation levels to ToM thoughtseeds based on hypothesis confidence scores

- **FR-005**: System MUST gracefully degrade to non-ToM response generation when LLM calls fail or timeout, logging quality warning for monitoring

- **FR-006**: System MUST persist all ToM hypotheses to short-term storage with 30-day retention period for debugging and analysis

- **FR-007**: System MUST persist winning hypotheses and high-surprise losing hypotheses (surprise > 0.7) to long-term storage indefinitely for learning

- **FR-008**: System MUST automatically expire and delete short-term ToM hypothesis records older than 30 days

#### Active Inference Selection

- **FR-009**: System MUST calculate expected free energy (EFE) for each ToM hypothesis using formula: EFE = (1/Precision) × Uncertainty + Precision × Divergence

- **FR-010**: System MUST extract prediction probabilities from ToM hypothesis confidence distributions

- **FR-011**: System MUST generate thought vectors from ToM hypothesis embeddings

- **FR-012**: System MUST retrieve user goal vectors from active goal backlog (priority: ACTIVE goals first)

- **FR-013**: System MUST select ToM hypothesis with minimal EFE as winner (winner-take-all competition)

- **FR-014**: System MUST use current agent precision level from MetaplasticityService precision registry

#### Response Validation

- **FR-015**: System MUST calculate empathy score (0.0-1.0) measuring response alignment with selected ToM hypothesis

- **FR-016**: System MUST calculate coherence score (0.0-1.0) measuring response consistency with conversation context and user history

- **FR-017**: System MUST compute utility score using formula: Utility = 0.8 × Empathy + 0.2 × Coherence

- **FR-018**: System MUST iteratively refine response when utility < 0.9, with maximum 3 refinement attempts

- **FR-019**: System MUST generate critique for low-utility responses identifying specific empathy or coherence gaps

- **FR-020**: System MUST optimize response based on critique while maintaining alignment with ToM hypothesis

#### Social Memory Integration

- **FR-021**: System MUST extract user preferences from interactions using LLM-powered preference detection

- **FR-022**: System MUST identify emotional markers with emotion type, intensity (0.0-1.0), timestamp, context, and evidence

- **FR-023**: System MUST store preferences as UserPreference entities in Graphiti temporal knowledge graph

- **FR-024**: System MUST store emotional markers as EmotionalState entities in Graphiti with temporal relationships

- **FR-025**: System MUST retrieve relevant preferences and emotional history during bootstrap recall for session context

- **FR-026**: System MUST handle temporal fact evolution when user preferences change over time

- **FR-027**: System MUST retain UserPreference and EmotionalState entities indefinitely until user explicitly requests data deletion

- **FR-028**: System MUST provide user data deletion capability that removes all UserPreference and EmotionalState entities associated with user upon request

#### Identity Coherence Monitoring

- **FR-029**: System MUST calculate alignment score between responses and user's Before Identity (Undesired) model

- **FR-030**: System MUST calculate alignment score between responses and user's After Identity (Desired) model

- **FR-031**: System MUST create IdentityCoherencePattern monitoring pattern checking alignment every 5 interactions

- **FR-032**: System MUST generate IDENTITY_MISALIGNMENT issue when alignment score < 0.7

- **FR-033**: System MUST validate responses against Perry Belcher voice rules and 5th grade reading level constraint

- **FR-034**: System MUST enforce IAS curriculum principle alignment (9 lessons, 3 phases)

#### Basin Activation

- **FR-035**: System MUST activate attractor basins from winning ToM hypothesis using existing activate_basins_from_winner mechanism

- **FR-036**: System MUST strengthen basin activation based on ToM confidence level (activation_strength = confidence * 0.5)

- **FR-037**: System MUST create basin transitions when high-EFE ToM hypothesis creates perturbation exceeding basin stability threshold

- **FR-038**: System MUST record basin-memory associations for Hebbian learning (ToM basins that co-activate wire together)

#### Observability

- **FR-039**: System MUST emit metrics for ToM hypothesis generation latency (p50, p95, p99 percentiles)

- **FR-040**: System MUST emit metrics for ToM hypothesis count per interaction and winning hypothesis selection rate

- **FR-041**: System MUST emit metrics for empathy validation scores, coherence validation scores, and utility scores

- **FR-042**: System MUST log structured events for LLM call failures, graceful degradation triggers, and quality warnings

- **FR-043**: System MUST log ToM hypothesis details (type, confidence, EFE score) for winning hypotheses at INFO level

- **FR-044**: System MUST emit metrics for basin activation success rate and basin stability scores

### Key Entities

- **ToMHypothesis**: Represents mental state hypothesis about user
  - Attributes: mental_state_type (Belief/Desire/Intention/Emotion/Thought), description, confidence, type_focus, neuronal_packet
  - Relationships: Converts to ThoughtSeed, links to UserProfile, stores in CognitiveEpisode

- **ThoughtSeedToM**: ThoughtSeed variant specifically for ToM hypotheses
  - Attributes: layer (conceptual/metacognitive/abstract/perceptual), activation_level, efe_score, precision, thought_content
  - Relationships: Competes with other thoughtseeds, activates attractor basins, generates responses

- **EmpathyValidation**: Response quality assessment
  - Attributes: empathy_score (0.0-1.0), coherence_score (0.0-1.0), utility_score, critique, refinement_count
  - Relationships: Links to response, ToM hypothesis, validation iteration history

- **UserPreference**: Extracted user preference stored in Graphiti
  - Attributes: preference_key, preference_value, timestamp, evidence, source
  - Relationships: Links to User entity, temporal fact evolution chain

- **EmotionalState**: User emotional marker stored in Graphiti
  - Attributes: emotion_type, intensity (0.0-1.0), timestamp, context, evidence, source
  - Relationships: Links to User entity, interaction episode, emotional pattern clusters

- **IdentityCoherenceMonitoring**: Metacognition pattern for identity alignment
  - Attributes: before_identity_alignment (0.0-1.0), after_identity_alignment (0.0-1.0), voice_compliance, ias_principle_alignment
  - Relationships: Links to IdentitySection, MonitoringPattern, control actions

## Clarifications

### Session 2026-01-02

- Q: How frequently should the system check identity coherence alignment (FR-025 parameter N)? → A: Every 5 interactions (N=5)
- Q: How long should user preference and emotional state data be retained? → A: Until user deletion request (indefinite retention with user control)
- Q: How should the system handle LLM call failures during ToM processing? → A: Graceful degradation to non-ToM response generation
- Q: What observability signals should be captured for production monitoring? → A: Metrics + structured logs (hypothesis counts, scores, failures)
- Q: Should ToM hypotheses be stored persistently or kept only for the duration of the interaction? → A: Store winning + high-surprise losing hypotheses indefinitely for learning, keep all hypotheses 30 days for debugging

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Empathetic response quality improves by 40% as measured by human raters scoring responses on 5-point empathy scale (baseline: current IAS chat responses)

- **SC-002**: 90% of responses pass empathy/coherence validation (utility >= 0.9) within 3 refinement attempts

- **SC-003**: ToM hypothesis generation completes in under 2 seconds for 95th percentile requests

- **SC-004**: Social memory recall accuracy reaches 85% (retrieved preferences/emotions match user confirmation)

- **SC-005**: Identity alignment violations decrease by 60% (baseline: current metacognition monitoring logs)

- **SC-006**: User-reported "response felt off" incidents decrease by 50% within first month of deployment

- **SC-007**: System handles 500 concurrent ToM-enhanced interactions without degradation

- **SC-008**: Basin activation from ToM winners creates stable attractors (stability >= 0.8) in 80% of cases

- **SC-009**: Response refinement reduces average utility gap by 0.15 per iteration (e.g., 0.75 → 0.90 in 1 iteration)

- **SC-010**: [LEGACY_AVATAR_HOLDER] users report 30% increase in "system understands me" satisfaction metric
