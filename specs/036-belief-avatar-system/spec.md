# Feature Specification: Belief Avatar System

**Feature Branch**: `036-belief-avatar-system`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Create specifications for two features: (1) Belief Journey Router - REST API endpoints for the belief tracking service at api/services/belief_tracking_service.py, exposing journey creation, belief lifecycle, experiments, replay loops, MOSAEIC captures, and metrics; (2) Avatar Simulation Skills - Skills for the skills-library enabling interactive avatar roleplay with Theory of Mind modeling, Shell/Core dynamics tracking, and response prediction for the Analytical Empath archetype

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Belief Journey Management via API (Priority: P1)

Course facilitators and AI systems need to track participant belief transformation throughout the 9-lesson IAS program. They access the Belief Journey Router to create journeys, record belief events, and retrieve progress metrics.

**Why this priority**: Core infrastructure for IAS program delivery. Without API endpoints, no external system can interact with the belief tracking service. Enables both human facilitators and automated systems to record and query participant progress.

**Independent Test**: Can be fully tested by making HTTP requests to journey endpoints and verifying correct data persistence and retrieval. Delivers immediate value for programmatic IAS journey tracking.

**Acceptance Scenarios**:

1. **Given** no existing journey, **When** a POST request is made to `/journey/create` with optional participant_id, **Then** a new BeliefJourney is created and returned with unique ID and initial phase set to REVELATION
2. **Given** an active journey, **When** a POST request is made to `/beliefs/limiting/identify` with belief content, **Then** a LimitingBelief is created in IDENTIFIED status and linked to the journey
3. **Given** an identified limiting belief, **When** a POST request is made to `/beliefs/experiment/record` with outcome data, **Then** the experiment result updates belief strength appropriately

---

### User Story 2 - Progress Metrics Retrieval (Priority: P1)

Course facilitators need real-time visibility into participant progress including belief dissolution rates, experiment success rates, and replay loop resolution times. They query the metrics endpoint for comprehensive journey analytics.

**Why this priority**: Enables facilitator oversight and intervention. Critical for identifying participants who need additional support or are progressing well.

**Independent Test**: Can be fully tested by creating a journey with multiple beliefs/experiments, then querying metrics endpoint and verifying calculated values match expected aggregations.

**Acceptance Scenarios**:

1. **Given** a journey with 3 limiting beliefs (1 dissolved, 1 dissolving, 1 identified), **When** GET `/journey/{id}/metrics` is called, **Then** response includes dissolution_rate of 0.33 and correct status counts
2. **Given** a journey with 5 experiments (3 disconfirming, 2 confirming), **When** metrics are retrieved, **Then** experiment_success_rate equals 0.6
3. **Given** a journey with no activity, **When** metrics are retrieved, **Then** all rates are 0 and counts are 0 without errors

---

### User Story 3 - Avatar Simulation with Theory of Mind (Priority: P2)

Content creators and course developers simulate the Analytical Empath avatar's experience of IAS materials. They invoke the avatar simulation skill to generate authentic responses, internal thoughts, and expert observations.

**Why this priority**: Enables rapid course iteration and quality assurance. Helps identify friction points, resistance patterns, and leverage opportunities before live participant exposure.

**Independent Test**: Can be fully tested by providing course content and receiving structured avatar response with Shell/Core dynamics and expert analysis. Delivers value for course design validation.

**Acceptance Scenarios**:

1. **Given** course content (script/lesson), **When** avatar simulation skill is invoked, **Then** response includes avatar's internal thoughts, emotional reactions, and Shell/Core dynamics
2. **Given** content that triggers a known resistance pattern, **When** simulation runs, **Then** resistance is detected and flagged with pattern name and recommended mitigation
3. **Given** content with a leverage point, **When** simulation runs, **Then** expert observer section identifies the mechanism and predicted impact

---

### User Story 4 - Response Prediction Model (Priority: P2)

Course developers predict how the avatar will respond to specific messaging, exercises, or interventions. They query the response prediction capability to optimize content before deployment.

**Why this priority**: Reduces iteration cycles and improves first-pass content quality. Enables data-driven content decisions.

**Independent Test**: Can be fully tested by providing stimulus content and receiving predicted response with confidence score. Delivers immediate content optimization value.

**Acceptance Scenarios**:

1. **Given** a message using "you're not broken" framing, **When** prediction is requested, **Then** response predicts SKEPTICAL with confidence > 0.8 and reason citing market saturation
2. **Given** a message naming specific private experience, **When** prediction is requested, **Then** response predicts ENGAGED with high resonance score
3. **Given** an executive-focused message, **When** prediction is requested, **Then** response predicts SHELL_RESPONSE with note about Empath bypass

---

### User Story 5 - Replay Loop Lifecycle Management (Priority: P3)

Participants and facilitators track rumination patterns from identification through resolution. They use API endpoints to record trigger situations, apply the 3-step process, and track resolution times.

**Why this priority**: Replay loops are the avatar's "core obsession" - 24/7 lived experience. Tracking resolution provides powerful progress evidence.

**Independent Test**: Can be fully tested by creating a loop, interrupting it, resolving it, and verifying status transitions and resolution time capture.

**Acceptance Scenarios**:

1. **Given** a journey, **When** POST `/loops/identify` with trigger, story, emotion, and fear, **Then** ReplayLoop created in ACTIVE status
2. **Given** an active loop, **When** POST `/loops/interrupt` with compassionate reflection, **Then** status transitions to INTERRUPTED
3. **Given** an interrupted loop, **When** POST `/loops/resolve` with lesson and comfort, **Then** status becomes RESOLVED and resolution_time_minutes is calculated

---

### User Story 6 - Shell/Core Dynamics Tracking (Priority: P3)

Avatar simulation tracks which "operating system" is active during content consumption. This enables analysis of content that reaches the Core (private self) vs. content that only activates the Shell (professional persona).

**Why this priority**: Core engagement is the mechanism of transformation. Shell-only engagement means content optimization for the wrong target.

**Independent Test**: Can be fully tested by running simulation on different content types and verifying correct Shell/Core classification with supporting evidence.

**Acceptance Scenarios**:

1. **Given** content about "leadership presence," **When** simulation runs, **Then** Shell activation score > Core activation score
2. **Given** content naming "replay conversations wondering if I hurt someone," **When** simulation runs, **Then** Core activation score > Shell activation score
3. **Given** content sequence, **When** simulation tracks dynamics, **Then** Shell/Core ratio per segment is captured and overall arc mapped

---

### Edge Cases

- What happens when journey_id doesn't exist? Return 404 with clear error message
- What happens when belief_id references wrong journey? Return 400 with validation error
- What happens when duplicate loop trigger is submitted? Create new loop (multiple instances valid)
- What happens when experiment references non-existent belief? Return 400 with reference error
- What happens when avatar simulation receives empty content? Return 400 requiring content
- What happens when metrics requested for journey with no data? Return valid response with zero values

## Requirements *(mandatory)*

### Functional Requirements

**Belief Journey Router (Feature 1)**

- **FR-001**: System MUST expose POST `/journey/create` endpoint that creates a BeliefJourney with optional participant_id and returns the full journey object
- **FR-002**: System MUST expose GET `/journey/{id}` endpoint that retrieves a journey by UUID
- **FR-003**: System MUST expose POST `/journey/{id}/advance` endpoint that records lesson completion and updates current phase
- **FR-004**: System MUST expose POST `/beliefs/limiting/identify` endpoint that creates a LimitingBelief in IDENTIFIED status
- **FR-005**: System MUST expose POST `/beliefs/limiting/{id}/map` endpoint that adds behavioral mappings and transitions to MAPPED status
- **FR-006**: System MUST expose POST `/beliefs/limiting/{id}/evidence` endpoint that adds supporting or challenging evidence
- **FR-007**: System MUST expose POST `/beliefs/limiting/{id}/dissolve` endpoint that marks belief as DISSOLVED
- **FR-008**: System MUST expose POST `/beliefs/empowering/propose` endpoint that creates an EmpoweringBelief in PROPOSED status
- **FR-009**: System MUST expose POST `/beliefs/empowering/{id}/strengthen` endpoint that adds evidence and increases embodiment
- **FR-010**: System MUST expose POST `/beliefs/empowering/{id}/anchor` endpoint that links belief to habit stack
- **FR-011**: System MUST expose POST `/experiments/design` endpoint that creates a BeliefExperiment
- **FR-012**: System MUST expose POST `/experiments/{id}/record` endpoint that records experiment outcome and updates belief strengths
- **FR-013**: System MUST expose POST `/loops/identify` endpoint that creates a ReplayLoop in ACTIVE status
- **FR-014**: System MUST expose POST `/loops/{id}/interrupt` endpoint that records compassionate reflection
- **FR-015**: System MUST expose POST `/loops/{id}/resolve` endpoint that completes the loop with lesson and comfort
- **FR-016**: System MUST expose POST `/mosaeic/capture` endpoint that records a MOSAEIC observation
- **FR-017**: System MUST expose POST `/vision/add` endpoint that creates a VisionElement
- **FR-018**: System MUST expose POST `/support/circle/create` endpoint that initializes SupportCircle
- **FR-019**: System MUST expose POST `/support/circle/{id}/member` endpoint that adds SupportCircleMember
- **FR-020**: System MUST expose GET `/journey/{id}/metrics` endpoint that returns comprehensive journey analytics
- **FR-021**: System MUST expose GET `/health` endpoint that confirms service availability
- **FR-022**: All mutation endpoints MUST persist events to Neo4j via Graphiti integration

**Avatar Simulation Skills (Feature 2)**

- **FR-023**: System MUST provide skill that accepts course content and returns avatar simulation response
- **FR-024**: Avatar response MUST include internal_thoughts section capturing private mental experience
- **FR-025**: Avatar response MUST include emotional_reactions section with specific emotion labels
- **FR-026**: Avatar response MUST include shell_core_dynamics section showing which system is active
- **FR-027**: Avatar response MUST include resistance_patterns section flagging detected objections
- **FR-028**: System MUST provide expert_observer section with leverage points and friction identification
- **FR-029**: System MUST provide response_prediction capability that predicts avatar reaction to stimulus
- **FR-030**: Response prediction MUST include confidence_score (0.0-1.0) and reasoning
- **FR-031**: System MUST track belief_state evolution across simulation segments
- **FR-032**: System MUST respect Prime Directive language constraints (no "broken," "fix," "wrong")
- **FR-033**: System MUST flag content using market-saturated phrases ("you're not broken")

### Key Entities

- **BeliefJourney**: Aggregate root containing all participant transformation data across 9 lessons and 3 phases
- **LimitingBelief**: Identified belief blocking progress, tracked from identification through dissolution
- **EmpoweringBelief**: New belief being built, tracked from proposal through embodiment
- **BeliefExperiment**: Real-world test of belief with hypothesis, action, and outcome
- **ReplayLoop**: Rumination pattern tracked from trigger identification through resolution
- **MOSAEICCapture**: Somatic awareness observation linking sensations to beliefs
- **VisionElement**: Future vision artifact from Phase 2
- **SupportCircle**: Network of mentors, peers, and mentees from Phase 3
- **AvatarState**: Current Shell/Core activation levels and belief positions
- **SimulationResponse**: Structured output from avatar simulation with all required sections

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Facilitators can create and track complete participant journeys through all 9 lessons
- **SC-002**: Journey metrics endpoint returns calculated rates within 1 second
- **SC-003**: Avatar simulation produces response with all required sections for any course content under 5 seconds
- **SC-004**: Response prediction achieves > 75% accuracy on validation set of known avatar responses
- **SC-005**: All belief lifecycle transitions are captured in Neo4j with appropriate relationships
- **SC-006**: Zero data loss when multiple journeys are created and updated concurrently
- **SC-007**: Course developers can identify 3+ leverage points per lesson using simulation
- **SC-008**: Shell/Core dynamics tracking correctly classifies > 80% of test content segments

## Assumptions

- BeliefTrackingService at `api/services/belief_tracking_service.py` is complete and functional
- Belief models at `api/models/belief_journey.py` are complete and validated
- Graphiti service is available for Neo4j persistence
- Avatar source of truth at `data/ground-truth/analytical-empath-avatar-source-of-truth.md` is canonical
- Skills will be stored in external skills-library (outside dionysus3-core)
- Avatar simulation uses Theory of Mind model built from:
  - Split Self Architecture (Shell = Iron Suit, Core = Bleeding Heart)
  - 5 Self-Sabotage Patterns with limiting beliefs
  - Voice of Market exact language
  - Core Obsession (rumination/replay loops)
  - Resistance to market-saturated phrases

## Dependencies

- `api/services/belief_tracking_service.py` - BeliefTrackingService singleton
- `api/models/belief_journey.py` - All Pydantic models
- `api/services/graphiti_service.py` - Graphiti Neo4j integration
- `data/ground-truth/analytical-empath-avatar-source-of-truth.md` - Avatar definition
- External skills-library for avatar simulation skills
