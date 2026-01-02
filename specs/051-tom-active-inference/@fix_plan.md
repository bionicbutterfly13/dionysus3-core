# Task Queue - Feature 051: ToM Active Inference Integration

## Current Task
> **SETUP-001: Create Pydantic models for ToM entities**
> Create `api/models/tom_hypothesis.py` with ToMHypothesis, ThoughtSeedToM models per spec.md Key Entities section. Include mental_state_type enum, confidence field, neuronal_packet dict.
>
> Acceptance: Models import without error, validate with pytest fixture

## Backlog

### Phase 1: Core ToM Infrastructure (P1 - Priority Tasks)

#### Models & Types
- [ ] SETUP-002: Create EmpathyValidation model in `api/models/empathy_validation.py`
- [ ] SETUP-003: Create UserPreference and EmotionalState models for Graphiti entities

#### ToM Hypothesis Generation (FR-001 to FR-008)
- [ ] TOM-001: Create ToMHypothesisTool class skeleton in `api/agents/tools/tom_hypothesis_generator.py`
- [ ] TOM-002: Implement round-robin mental state type cycling (Belief/Desire/Intention/Emotion/Thought)
- [ ] TOM-003: Create LLM prompt template for hypothesis generation with MetaMind-style format
- [ ] TOM-004: Implement hypothesis generation with user utterance + context + social memory inputs
- [ ] TOM-005: Add confidence score extraction from LLM response
- [ ] TOM-006: Implement ToM → ThoughtSeed conversion (layer assignment based on mental_state_type)
- [ ] TOM-007: Add activation level assignment from confidence scores
- [ ] TOM-008: Implement hypothesis persistence (short-term: all, long-term: winners + high-surprise)
- [ ] TOM-009: Add 30-day automatic expiration for short-term hypothesis storage
- [ ] TOM-010: Add graceful degradation when LLM calls fail (FR-005)

#### Active Inference Selection (FR-009 to FR-014)
- [ ] EFE-001: Create ToMActiveInferenceService in `api/services/tom_active_inference.py`
- [ ] EFE-002: Implement prediction probability extraction from ToM hypothesis confidence
- [ ] EFE-003: Implement thought vector generation from hypothesis embeddings
- [ ] EFE-004: Add user goal vector retrieval from active goal backlog
- [ ] EFE-005: Integrate with existing EFEEngine.calculate_efe() for each hypothesis
- [ ] EFE-006: Implement winner selection via min(EFE) across all 7 hypotheses
- [ ] EFE-007: Add precision modulation from MetaplasticityService registry

### Phase 2: Quality Validation (P2 - Quality Gates)

#### Response Validation (FR-015 to FR-020)
- [ ] VAL-001: Create ResponseValidationService in `api/services/response_validation.py`
- [ ] VAL-002: Implement empathy score calculation (alignment with ToM hypothesis)
- [ ] VAL-003: Implement coherence score calculation (consistency with context)
- [ ] VAL-004: Add utility score computation (0.8 * empathy + 0.2 * coherence)
- [ ] VAL-005: Implement iterative refinement loop (max 3 attempts, threshold 0.9)
- [ ] VAL-006: Add critique generation for low-utility responses
- [ ] VAL-007: Implement response optimization based on critique
- [ ] VAL-008: Add fallback handling when validation fails after 3 attempts

### Phase 3: Social Memory Persistence (P3 - Session Continuity)

#### Social Memory Integration (FR-021 to FR-028)
- [ ] MEM-001: Create SocialMemoryIntegrationService in `api/services/social_memory_integration.py`
- [ ] MEM-002: Implement LLM-powered user preference extraction from utterances
- [ ] MEM-003: Implement emotional marker detection (type, intensity, context, evidence)
- [ ] MEM-004: Add UserPreference entity creation in Graphiti with timestamp
- [ ] MEM-005: Add EmotionalState entity creation in Graphiti with temporal relationships
- [ ] MEM-006: Integrate preference/emotion retrieval into bootstrap recall service
- [ ] MEM-007: Implement temporal fact evolution for changing preferences
- [ ] MEM-008: Add user data deletion endpoint (GDPR compliance, FR-024 to FR-025)

### Phase 4: Identity Coherence Monitoring (P4 - Brand Alignment)

#### Identity Coherence (FR-029 to FR-034)
- [ ] ID-001: Create IdentityCoherencePattern in metacognition_patterns_storage.py
- [ ] ID-002: Implement Before Identity alignment scoring
- [ ] ID-003: Implement After Identity alignment scoring
- [ ] ID-004: Add monitoring trigger every 5 interactions (from clarification Q1)
- [ ] ID-005: Implement IDENTITY_MISALIGNMENT issue generation (threshold < 0.7)
- [ ] ID-006: Add Perry Belcher voice validation (5th grade reading level check)
- [ ] ID-007: Add IAS curriculum principle alignment check (9 lessons, 3 phases)

### Phase 5: Basin Activation & Integration (P1 Extension)

#### Basin Integration (FR-035 to FR-038)
- [ ] BASIN-001: Integrate ToM winner with existing activate_basins_from_winner()
- [ ] BASIN-002: Implement basin activation strength modulation (confidence * 0.5)
- [ ] BASIN-003: Add basin transition logic for high-EFE hypotheses
- [ ] BASIN-004: Implement Hebbian learning for ToM basin co-activation

### Phase 6: Observability (Cross-cutting)

#### Metrics & Logging (FR-039 to FR-044)
- [ ] OBS-001: Add ToM hypothesis generation latency metrics (p50, p95, p99)
- [ ] OBS-002: Add hypothesis count and win rate metrics
- [ ] OBS-003: Add empathy/coherence/utility score metrics
- [ ] OBS-004: Add structured logging for LLM failures and graceful degradation
- [ ] OBS-005: Add INFO-level logging for winning hypothesis details
- [ ] OBS-006: Add basin activation success rate metrics

### Phase 7: Integration & Testing

#### Integration Tests
- [ ] TEST-001: Create end-to-end test: user utterance → ToM → EFE → response
- [ ] TEST-002: Test graceful degradation path when LLM fails
- [ ] TEST-003: Test social memory persistence and recall
- [ ] TEST-004: Test identity coherence violation detection
- [ ] TEST-005: Validate SC-003: <2s latency for ToM generation
- [ ] TEST-006: Validate SC-002: 90% pass rate within 3 refinements
- [ ] TEST-007: Load test SC-007: 500 concurrent interactions

#### Tool Integration
- [ ] INT-001: Add ToMHypothesisTool to Perception Agent managed tools
- [ ] INT-002: Update ConsciousnessManager to route ToM hypotheses to EFE selection
- [ ] INT-003: Integrate validation service into response generation pipeline
- [ ] INT-004: Wire social memory extraction into EventBus consciousness integration

## Completed
_Tasks completed will be moved here with completion timestamp_

## Discovered
_Tasks found during implementation will be added here_

## Blocked
_Tasks that can't proceed - document blocker_

---

## Task Breakdown Strategy

**Atomic Task Size**: Each task = 2-5 minutes focused work
**Dependencies**: Tasks ordered to minimize blocking
**Testing**: Every service gets unit test task before integration
**Validation**: Each FR maps to 1-3 implementation tasks

**Total Tasks**: ~70 atomic tasks
**Estimated Completion**: 4-6 hours of Ralph autonomous execution (assuming 3-4 min avg per task)

## Current Phase: Phase 1 (P1 Core Infrastructure)
**Next Milestone**: ToM hypothesis generation working end-to-end with EFE selection
