# Feature Specification: Complete Placeholder Implementations

**Feature Branch**: `057-complete-placeholder-implementations`
**Created**: 2026-01-06
**Status**: Draft
**Input**: User description: "Complete missing implementations identified in codebase audit:

1. Meta-evolution metrics (api/services/meta_evolution_service.py) - currently mocked energy/basin counts
2. Active inference / Meta-ToT placeholder probabilities (api/core/engine/meta_tot.py) - replace placeholders with real implementations
3. EpistemicFieldService tests (tests/unit/test_epistemic_field_service.py) - all skipped/TODO
4. Beautiful Loop OODA integration tests (tests/integration/test_beautiful_loop_ooda.py) - all skipped/TODO
5. Stub scripts: scripts/ghl_sync.py fetch_all_emails() stub and scripts/store_metacognition_memory.py demo/mock

This is a technical debt cleanup feature to replace mocks, placeholders, and TODO tests with production-ready implementations that integrate with the existing active inference, attractor basin, and OODA loop architecture."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate System Health Metrics (Priority: P1)

As a system operator monitoring Dionysus cognitive health, I need accurate real-time metrics for energy levels and active attractor basins so that I can detect degraded performance states and trigger corrective actions.

**Why this priority**: Core monitoring capability for autonomous cognitive system. Without real metrics, the system flies blind and cannot self-regulate or trigger meta-evolution cycles effectively.

**Independent Test**: Can be fully tested by querying SystemMoment snapshots and verifying energy_level and active_basins_count reflect actual system state (not hardcoded values), delivering accurate cognitive health visibility.

**Acceptance Scenarios**:

1. **Given** the system has processed 10 cognitive episodes with varying surprise scores, **When** `capture_system_moment()` is called, **Then** energy_level reflects computed free energy across active basins (not 100.0 placeholder)
2. **Given** three attractor basins (cognitive_science, consciousness, systems_theory) are currently active with depth > 0.3, **When** system moment is captured, **Then** active_basins_count = 3 (not 5 placeholder)
3. **Given** no active basins exist (all depths below threshold), **When** system moment is captured, **Then** active_basins_count = 0 and energy_level reflects high uncertainty state

---

### User Story 2 - Real Active Inference Scoring (Priority: P1)

As the Meta-ToT reasoning engine, I need real probability distributions and precision vectors from the active inference model service so that thoughtseed competition accurately reflects expected free energy and selects optimal cognitive paths.

**Why this priority**: Core to reasoning quality. Placeholder probabilities make thoughtseed selection arbitrary, undermining the entire active inference architecture. This blocks effective OODA decision-making.

**Independent Test**: Can be tested by generating thoughtseeds with different contents, verifying scores differ based on actual model predictions (not placeholder values), and confirming winning thoughtseed has demonstrably lower EFE.

**Acceptance Scenarios**:

1. **Given** a parent ThoughtNode with content "User wants authentication", **When** three child nodes are expanded with candidate contents ["OAuth2", "JWT sessions", "Magic links"], **Then** each child receives a unique score from active inference wrapper (not identical placeholder scores)
2. **Given** a thoughtseed aligned with current goal_vector, **When** scored via active inference, **Then** score.expected_free_energy is computed from real precision-weighted prediction errors (not hardcoded)
3. **Given** two thoughtseeds with different alignment to goal_vector, **When** both are scored, **Then** the better-aligned thoughtseed has measurably lower EFE (difference > 0.1)

---

### User Story 3 - Validated Epistemic Field Measurement (Priority: P2)

As a consciousness researcher validating the Beautiful Loop implementation, I need comprehensive test coverage for EpistemicFieldService so that I can verify recursive sharing depth, luminosity factors, and aware/transparent process classification work correctly.

**Why this priority**: Required for research validation and publication. Without tests, epistemic depth measurement (a novel contribution) cannot be scientifically validated or debugged when issues arise.

**Independent Test**: Can be tested by running pytest on test_epistemic_field_service.py and achieving >90% coverage with all tests passing, delivering confidence in epistemic state computation accuracy.

**Acceptance Scenarios**:

1. **Given** EpistemicFieldService is initialized with a precision profile, **When** `get_epistemic_state()` is called, **Then** it returns EpistemicState with computed depth_score in [0, 1] range
2. **Given** three cognitive layers are bidirectionally sharing precision information, **When** recursive sharing depth is tracked, **Then** sharing_depth = 3 (not hardcoded)
3. **Given** a cognitive process is bound to conscious awareness, **When** `classify_process()` is called, **Then** it returns "aware" (not "transparent")
4. **Given** focused attention state vs diffuse attention state, **When** depth scores are compared, **Then** effect size d > 0.8 (statistically significant differentiation)

---

### User Story 4 - Validated Beautiful Loop OODA Integration (Priority: P2)

As a developer maintaining the OODA loop architecture, I need comprehensive integration tests for Beautiful Loop so that I can verify precision profiles correctly propagate through OBSERVE→ORIENT→DECIDE→ACT phases without introducing performance overhead.

**Why this priority**: Prevents regressions in core cognitive loop. Beautiful Loop integration spans multiple agents and services; without integration tests, changes to one component can silently break cross-component coordination.

**Independent Test**: Can be tested by running integration test suite and verifying complete OODA cycle executes with precision profile updates, events emitted, and performance overhead <10%, delivering confidence in production stability.

**Acceptance Scenarios**:

1. **Given** a PrecisionProfile with specific modality weights, **When** PerceptionAgent enters OBSERVE phase, **Then** observations are weighted by modality precision from the profile
2. **Given** ReasoningAgent in ORIENT phase, **When** multiple inference candidates are generated, **Then** each respects layer precision weights from current profile
3. **Given** a complete OODA cycle (OBSERVE→ORIENT→DECIDE→ACT), **When** cycle completes, **Then** four events are emitted: PrecisionForecastEvent, PrecisionErrorEvent, PrecisionUpdateEvent, BindingCompletedEvent
4. **Given** baseline OODA cycle time without Beautiful Loop, **When** Beautiful Loop is active, **Then** overhead is <10% of baseline cycle time

---

### User Story 5 - Production-Ready GHL Email Sync (Priority: P3)

As a marketing automation operator, I need the GHL sync script to fetch all emails from the IAS Group Long Nurture Workflow so that I can analyze nurture sequence content and identify conversion bottlenecks.

**Why this priority**: Lower priority - operational convenience feature for marketing analysis, not core cognitive functionality. Can be deferred if higher-priority items need more effort.

**Independent Test**: Can be tested by running `python scripts/ghl_sync.py` and verifying it returns a list of email objects with subject/body/sequence_position fields from the specified workflow.

**Acceptance Scenarios**:

1. **Given** valid GHL API credentials and location ID, **When** `fetch_all_emails()` is called, **Then** it returns a list of email templates from the specified workflow (not empty stub)
2. **Given** the IAS Group Long Nurture Workflow has 8 emails, **When** sync completes, **Then** exactly 8 email objects are returned with complete content
3. **Given** GHL API returns an error, **When** `fetch_all_emails()` is called, **Then** it raises a descriptive exception (not silent failure)

---

### User Story 6 - Production-Ready Metacognition Storage (Priority: P3)

As a system integrator deploying metacognition theory, I need the storage script to use real service calls (not mocks) so that episodic events, semantic concepts, and procedural patterns persist correctly across memory tiers.

**Why this priority**: Lower priority - demonstrates storage patterns but doesn't block core functionality. Current mock implementation serves as useful documentation; production integration can follow after core features stabilize.

**Independent Test**: Can be tested by running `python scripts/store_metacognition_memory.py` and verifying entities/relationships appear in Graphiti, episodic events in HOT tier, and procedural patterns accessible to agents.

**Acceptance Scenarios**:

1. **Given** the script calls `store_semantic()`, **When** execution completes, **Then** 6 entities (Declarative Metacognition, Procedural Metacognition, etc.) exist in Graphiti knowledge graph
2. **Given** the script calls `store_episodic()`, **When** execution completes, **Then** 3 episodic events with timestamps are stored in multi-tier HOT tier
3. **Given** the script calls `store_procedural()`, **When** execution completes, **Then** 5 procedural patterns are accessible via HOT tier with TTL=3600 seconds

---

### Edge Cases

- What happens when active inference wrapper returns None or error during thoughtseed scoring?
- How does system handle zero active basins (cold start / amnesia scenario)?
- What if GHL API rate limits prevent fetching all emails in one call?
- How does Beautiful Loop behave when precision profile is all zeros (complete uncertainty)?
- What happens if EpistemicFieldService receives negative or >1.0 luminosity factors?
- How does metacognition storage handle duplicate entities in Graphiti?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Meta-evolution service MUST compute real energy_level from current free energy distribution across active attractor basins (replacing 100.0 placeholder in `api/services/meta_evolution_service.py:116`)
- **FR-002**: Meta-evolution service MUST compute real active_basins_count by querying basin depths from attractor basin service (replacing hardcoded 5 in `api/services/meta_evolution_service.py:117`)
- **FR-003**: Meta-ToT engine MUST call active inference model service to get real probability distributions when scoring thoughtseeds (replacing TODO comment in `api/core/engine/meta_tot.py:62`)
- **FR-004**: Meta-ToT engine MUST use precision-weighted prediction errors from active inference wrapper to compute expected free energy scores
- **FR-005**: EpistemicFieldService MUST implement all methods referenced in test_epistemic_field_service.py (get_epistemic_state, track_sharing_depth, compute_depth_score, classify_process)
- **FR-006**: All 22 tests in test_epistemic_field_service.py MUST be un-skipped and pass with >90% code coverage
- **FR-007**: Beautiful Loop OODA integration MUST implement all event emissions: PrecisionForecastEvent, PrecisionErrorEvent, PrecisionUpdateEvent, BindingCompletedEvent
- **FR-008**: All 36 tests in test_beautiful_loop_ooda.py MUST be un-skipped and pass with >90% code coverage
- **FR-009**: scripts/ghl_sync.py MUST implement fetch_all_emails() function to retrieve email templates from GHL API
- **FR-010**: scripts/store_metacognition_memory.py MUST replace mock storage calls with real service calls to Graphiti and multi-tier memory service
- **FR-011**: System MUST validate energy_level is in reasonable range [0, 10] and log warning if outside bounds
- **FR-012**: System MUST handle missing active inference scores gracefully (fallback to neutral score, not crash)

### Key Entities

- **SystemMoment**: Snapshot of system state at a specific timestamp, including energy_level (float), active_basins_count (int), total_memories_count (int), timestamp (datetime)
- **ThoughtNode**: MCTS node in Meta-ToT tree, including content (str), score (ActiveInferenceScore), parent_id (str), children_ids (list), depth (int)
- **ActiveInferenceScore**: Output from active inference scoring, including expected_free_energy (float), precision_vector (list[float]), prediction_error (float)
- **EpistemicState**: Output from epistemic field measurement, including depth_score (float), sharing_depth (int), luminosity_factors (dict), process_classification (str: "aware"|"transparent")
- **PrecisionProfile**: Configuration object for Beautiful Loop, including modality_weights (dict), layer_precisions (dict), meta_precision (float)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Meta-evolution service captures system moments with energy_level variance >0 across 10 consecutive snapshots (proving real computation, not placeholder)
- **SC-002**: Meta-ToT thoughtseed selection demonstrates >70% alignment with manually annotated "optimal" paths in 20 test scenarios
- **SC-003**: EpistemicFieldService test suite achieves >90% code coverage with all 22 tests passing
- **SC-004**: Beautiful Loop OODA integration test suite achieves >90% code coverage with all 36 tests passing and measured overhead <10%
- **SC-005**: EpistemicFieldService correctly differentiates focused vs diffuse attention states with Cohen's d effect size >0.8
- **SC-006**: GHL sync script successfully retrieves all emails from IAS workflow (8+ emails) within 30 seconds
- **SC-007**: Metacognition storage script persists 6+ entities and 7+ relationships to Graphiti with zero data loss
- **SC-008**: All implementations follow TDD methodology (tests written before implementation)
- **SC-009**: Zero new pytest.skip() or TODO comments introduced during implementation
- **SC-010**: System continues to pass all existing tests (no regressions)

## Assumptions

1. Active inference wrapper API exists and is accessible (`api.core.engine.active_inference.get_active_inference_wrapper()`)
2. Attractor basin service provides depth measurements for active basins
3. GHL API credentials are configured in environment variables
4. Graphiti service is operational and can accept entity/relationship additions
5. Multi-tier memory service (HOT tier) is deployed and accessible
6. Beautiful Loop models (HyperModelService, BayesianBinder, etc.) are already implemented
7. Test infrastructure supports async tests with pytest-asyncio
8. Existing OODA loop agents (PerceptionAgent, ReasoningAgent, MetacognitionAgent) are operational

## Dependencies

- **Upstream**: Active inference model service (for probability distributions)
- **Upstream**: Attractor basin service (for depth measurements)
- **Upstream**: Graphiti service (for knowledge graph storage)
- **Upstream**: Multi-tier memory service (for HOT tier storage)
- **Upstream**: Beautiful Loop services (HyperModelService, BayesianBinder, EpistemicFieldService)
- **Parallel**: GHL API access (for email sync)
- **Parallel**: Smolagents OODA architecture (for Beautiful Loop integration)

## Out of Scope

- Refactoring or redesigning existing active inference architecture
- Adding new features beyond completing existing placeholders
- Performance optimization beyond measuring overhead
- UI/dashboard for visualizing metrics
- Automated deployment pipelines
- Documentation beyond inline comments
- IAS curriculum outreach (user explicitly deferred this)

## Risks

1. **Active inference API instability**: If wrapper API changes frequently, thoughtseed scoring may break
   - *Mitigation*: Use interface/protocol pattern to decouple from implementation
2. **GHL API rate limits**: Fetching many emails may hit API throttling
   - *Mitigation*: Implement pagination and exponential backoff
3. **Test interdependencies**: Beautiful Loop tests may require full system stack running
   - *Mitigation*: Use comprehensive mocking for external dependencies
4. **Precision profile misconfiguration**: Invalid precision values could cause divide-by-zero or NaN propagation
   - *Mitigation*: Add validation and normalization at profile creation
5. **Graphiti schema conflicts**: New entities may conflict with existing graph structure
   - *Mitigation*: Query existing entities before insertion, use upsert pattern
