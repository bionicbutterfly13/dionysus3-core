# Technical Requirements - Feature 051: ToM Active Inference Integration

## Overview
Integrate Theory-of-Mind hypothesis generation with Dionysus active inference for Analytical Empath empathy modeling.

## Functional Requirements Summary

### ToM Hypothesis Generation (FR-001 to FR-008)
- Generate 7 hypotheses per interaction
- Round-robin diversity: Belief, Desire, Intention, Emotion, Thought
- Inputs: user utterance + conversation context + social memory
- Convert to ThoughtSeed format with layer assignment
- Tiered storage: 30-day debug + indefinite learning corpus (winners + high-surprise losers)
- Graceful degradation on LLM failure

### Active Inference Selection (FR-009 to FR-014)
- Calculate EFE for each hypothesis: `EFE = (1/Precision) × Uncertainty + Precision × Divergence`
- Extract prediction probabilities from confidence distributions
- Generate thought vectors from embeddings
- Retrieve goal vectors from active backlog
- Winner-take-all: select min(EFE)
- Use MetaplasticityService precision registry

### Response Validation (FR-015 to FR-020)
- Empathy score: alignment with ToM hypothesis (0.0-1.0)
- Coherence score: consistency with context (0.0-1.0)
- Utility: `0.8 × Empathy + 0.2 × Coherence`
- Iterative refinement: max 3 attempts, threshold 0.9
- Generate critique for low-utility responses
- Fallback with quality warning on failure

### Social Memory Integration (FR-021 to FR-028)
- LLM-powered preference extraction
- Emotional marker detection: type, intensity, context, evidence
- Store UserPreference entities in Graphiti
- Store EmotionalState entities with temporal relationships
- Bootstrap recall integration
- Temporal fact evolution for changing preferences
- User data deletion capability (GDPR)

### Identity Coherence Monitoring (FR-029 to FR-034)
- Before Identity alignment scoring
- After Identity alignment scoring
- Monitor every 5 interactions
- Generate IDENTITY_MISALIGNMENT issue when < 0.7
- Perry Belcher voice validation (5th grade reading level)
- IAS curriculum alignment (9 lessons, 3 phases)

### Basin Activation (FR-035 to FR-038)
- Activate basins from winning hypothesis
- Strength modulation: `confidence × 0.5`
- Basin transitions for high-EFE hypotheses
- Hebbian learning for co-activation

### Observability (FR-039 to FR-044)
- Metrics: latency (p50, p95, p99), hypothesis counts, scores
- Structured logs: LLM failures, degradation, quality warnings
- INFO-level winning hypothesis details
- Basin activation success rate metrics

## Data Models

### ToMHypothesis
```python
mental_state_type: Enum[Belief, Desire, Intention, Emotion, Thought]
description: str
confidence: float (0.0-1.0)
type_focus: str
neuronal_packet: dict
created_at: datetime
user_id: UUID
```

### ThoughtSeedToM
```python
layer: Enum[conceptual, metacognitive, abstract, perceptual]
activation_level: float (0.0-1.0)
efe_score: float
precision: float
thought_content: str
parent_hypothesis_id: UUID
```

### EmpathyValidation
```python
empathy_score: float (0.0-1.0)
coherence_score: float (0.0-1.0)
utility_score: float (0.0-1.0)
critique: str | None
refinement_count: int
hypothesis_id: UUID
response_text: str
```

### UserPreference (Graphiti)
```python
preference_key: str
preference_value: str
timestamp: datetime
evidence: str
source: Enum[LLM, direct]
user_id: UUID
```

### EmotionalState (Graphiti)
```python
emotion_type: str
intensity: float (0.0-1.0)
timestamp: datetime
context: str
evidence: str
source: Enum[LLM, direct]
user_id: UUID
```

## Integration Points

### Perception Agent
- Add ToMHypothesisTool to managed tools
- Tool generates 7 hypotheses on invocation
- Returns list of ToMHypothesis objects

### EFE Engine
- Extend to score ToM hypotheses
- Input: List[ToMHypothesis], goal_vector, precision
- Output: winning_hypothesis_id, efe_scores

### Graphiti Service
- Create UserPreference entity type
- Create EmotionalState entity type
- Add temporal relationship support

### Metacognition Patterns
- Add IdentityCoherencePattern to storage
- Trigger every 5 interactions
- Generate control actions on violation

### Bootstrap Recall
- Retrieve UserPreference entities for context
- Retrieve EmotionalState history
- Include in social memory summary

## Success Criteria Targets

| ID | Metric | Target | Validation Method |
|----|--------|--------|-------------------|
| SC-001 | Empathy quality improvement | 40% | Human rater comparison |
| SC-002 | Validation pass rate | 90% within 3 attempts | Automated test |
| SC-003 | ToM generation latency | <2s (p95) | Benchmark script |
| SC-004 | Social memory accuracy | 85% | User confirmation test |
| SC-005 | Identity violation reduction | 60% | Monitoring logs |
| SC-006 | "Response felt off" incidents | 50% reduction | User feedback |
| SC-007 | Concurrent interactions | 500 without degradation | Load test |
| SC-008 | Basin stability | ≥0.8 in 80% cases | Basin metrics |
| SC-009 | Refinement effectiveness | 0.15 utility gain/iteration | Automated test |
| SC-010 | "System understands me" | 30% increase | User survey |

## Architecture Constraints

1. **Async/Await**: All service methods must be async
2. **Pydantic v2**: Use BaseModel for all models
3. **No Direct Neo4j**: Only via Graphiti wrapper
4. **Precision Registry**: Use MetaplasticityService, no hardcoded values
5. **ManagedAgent Pattern**: Follow smolagents Tool class structure
6. **LLM Calls**: Use litellm router, implement timeouts
7. **Error Handling**: Graceful degradation required (FR-005)

## Testing Requirements

### Unit Tests
- Each service: 1 test file
- Each FR: ≥1 test case
- Mock external dependencies (LLM, Graphiti)
- Test graceful degradation paths

### Integration Tests
- End-to-end: utterance → ToM → EFE → validation → response
- Social memory persistence and recall
- Identity coherence violation detection
- Load test: 500 concurrent (SC-007)

### Performance Tests
- Latency benchmark: verify SC-003
- Validation pass rate: verify SC-002
- Memory accuracy: verify SC-004

## Dependencies

### Existing Services (Extend)
- `api/services/efe_engine.py`
- `api/services/thoughtseed_integration.py`
- `api/services/graphiti_service.py`
- `api/services/metaplasticity_service.py`
- `api/services/bootstrap_recall_service.py`
- `api/services/metacognition_patterns_storage.py`

### New Services (Create)
- `api/services/tom_active_inference.py`
- `api/services/social_memory_integration.py`
- `api/services/response_validation.py`

### New Models (Create)
- `api/models/tom_hypothesis.py`
- `api/models/empathy_validation.py`

### New Tools (Create)
- `api/agents/tools/tom_hypothesis_generator.py`

## Configuration

### Environment Variables
```bash
# LLM settings
OPENAI_API_KEY=sk-...
LLM_TIMEOUT=30  # seconds
LLM_MAX_RETRIES=3

# ToM settings
TOM_HYPOTHESIS_COUNT=7
TOM_VALIDATION_THRESHOLD=0.9
TOM_MAX_REFINEMENTS=3
TOM_SHORT_TERM_RETENTION_DAYS=30
TOM_SURPRISE_THRESHOLD=0.7

# Identity settings
IDENTITY_CHECK_INTERVAL=5  # interactions
IDENTITY_ALIGNMENT_THRESHOLD=0.7
```

## Deployment Considerations

1. **Monitoring**: Set up alerts for SC-003 latency violations
2. **Storage**: Monitor short-term hypothesis storage growth (30-day TTL)
3. **LLM Costs**: Track token usage for 7 hypotheses per interaction
4. **Graceful Degradation**: Ensure fallback responses maintain quality
5. **User Data**: Implement deletion workflow for GDPR compliance
