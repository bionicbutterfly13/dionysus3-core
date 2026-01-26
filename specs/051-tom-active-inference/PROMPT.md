# Feature 051: ToM Active Inference Integration - Ralph Instructions

## Goal
Integrate MetaMind's Theory-of-Mind (ToM) hypothesis generation pipeline with Dionysus's active inference architecture to enable empathetic mental state modeling for [LEGACY_AVATAR_HOLDER] users. The system generates 7 ToM hypotheses per interaction, selects winners via EFE minimization, validates responses for empathy/coherence, persists social memory to Graphiti, and monitors identity coherence alignment.

## Current State
- ✅ Specification complete (44 functional requirements across 6 domains)
- ✅ Clarifications resolved (5 key decisions documented)
- ✅ Active inference foundation exists (EFE engine, thoughtseed competition, basin activation)
- ✅ Graphiti temporal knowledge graph operational
- ⏸️ Implementation not started (awaiting task generation)

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI (async/await)
- **Agent Framework**: smolagents v2 (ManagedAgent pattern)
- **Memory**: Graphiti temporal knowledge graph (Neo4j backend)
- **Active Inference**: Existing EFE engine, Meta-ToT MCTS
- **LLM**: OpenAI API (GPT-4 for ToM generation, validation)
- **Testing**: pytest with asyncio support
- **Key Dependencies**:
  - `api/services/efe_engine.py` - Expected Free Energy calculation
  - `api/services/thoughtseed_integration.py` - ThoughtSeed conversion
  - `api/services/graphiti_service.py` - Temporal knowledge graph
  - `api/services/metaplasticity_service.py` - Precision registry

## Working Rules
1. **Read `@fix_plan.md`** for current task from Backlog
2. **Complete ONE task** per iteration (2-5 min focused work)
3. **Test-first**: Write/update tests before implementation
4. **Run validation** after each change:
   ```bash
   python -m pytest tests/unit/test_tom_*.py -v
   ```
5. **Commit atomically** with:
   ```bash
   git add . && git commit -m "ralph: [task description]"
   ```
6. **Update `@fix_plan.md`**: Move completed task to Completed section
7. **If blocked**: Document in Blocked section with reason, move to next task

## Task Completion Criteria
Every task MUST satisfy:
- [ ] Code implemented and follows existing patterns
- [ ] Unit tests written and passing
- [ ] No import errors or syntax issues
- [ ] Changes committed to git
- [ ] `@fix_plan.md` updated (Current Task → Completed)
- [ ] If new FR implemented, acceptance criteria from spec.md validated

## Implementation Priorities (P1 → P4)
Follow spec.md user story priorities:
- **P1**: ToM hypothesis generation + EFE selection (FR-001 to FR-014) - CORE VALUE
- **P2**: Response validation (empathy/coherence) (FR-015 to FR-020) - QUALITY GATE
- **P3**: Social memory persistence (FR-021 to FR-028) - SESSION CONTINUITY
- **P4**: Identity coherence monitoring (FR-029 to FR-034) - BRAND ALIGNMENT

## Anti-Patterns (DO NOT)
- ❌ Skip writing tests ("I'll add tests later")
- ❌ Batch multiple FRs into one task ("Implement FR-001 through FR-010")
- ❌ Leave uncommitted changes at task end
- ❌ Work on tasks not in Current Task section of `@fix_plan.md`
- ❌ Copy-paste from MetaMind repo without adapting to Dionysus patterns
- ❌ Create new files without checking existing services first
- ❌ Hardcode values that should use precision registry or basin activation
- ❌ Skip graceful degradation error handling (FR-005)
- ❌ Implement without reading related existing code first

## Quality Gates
Before marking task complete:
1. **Pattern Alignment**: Does code follow smolagents ManagedAgent pattern?
2. **Active Inference Integration**: Does ToM use EFE engine, not Shannon IG?
3. **Graphiti Integration**: Are entities created with proper temporal relationships?
4. **Error Handling**: Is graceful degradation implemented (FR-005)?
5. **Observability**: Are metrics/logs emitted per FR-039 to FR-044?
6. **Test Coverage**: Do tests validate acceptance criteria from spec.md?

## Exit Detection
Ralph stops when:
- All P1 tasks completed and tested ✅
- All P2 tasks completed and tested ✅
- All P3 tasks completed and tested ✅
- All P4 tasks completed and tested ✅
- Integration tests pass end-to-end
- Success criteria SC-001 through SC-010 validated

## Key File Locations
```
api/
├── agents/
│   └── tools/
│       └── tom_hypothesis_generator.py          # NEW: ToM tool for Perception Agent
├── services/
│   ├── efe_engine.py                            # EXTEND: Add ToM hypothesis scoring
│   ├── thoughtseed_integration.py               # EXTEND: ToM → ThoughtSeed conversion
│   ├── graphiti_service.py                      # EXTEND: UserPreference, EmotionalState entities
│   ├── metacognition_patterns_storage.py        # EXTEND: IdentityCoherencePattern
│   ├── tom_active_inference.py                  # NEW: ToM + Active Inference integration
│   ├── social_memory_integration.py             # NEW: Preference/emotion extraction
│   └── response_validation.py                   # NEW: Empathy/coherence validation
├── models/
│   ├── tom_hypothesis.py                        # NEW: Pydantic models for ToM entities
│   └── empathy_validation.py                    # NEW: Validation result models
└── routers/
    └── tom.py                                   # NEW: ToM endpoints (optional, for testing)

tests/unit/
├── test_tom_hypothesis_generator.py             # NEW
├── test_tom_active_inference.py                 # NEW
├── test_social_memory_integration.py            # NEW
├── test_response_validation.py                  # NEW
└── test_identity_coherence_monitoring.py        # NEW
```

## Architectural Constraints
1. **No Direct Neo4j Access**: All graph operations via Graphiti service wrapper
2. **Async/Await Required**: All service methods must be async
3. **Pydantic v2 Models**: Use BaseModel for all data structures
4. **ManagedAgent Pattern**: ToM tool must follow smolagents Tool class pattern
5. **Precision Registry**: Use `MetaplasticityService.get_agent_precision()` not hardcoded values
6. **Basin Activation**: Use existing `activate_basins_from_winner()` mechanism
7. **LLM Calls**: Use `litellm` router, implement timeouts and retries

## Development Commands
```bash
# Run unit tests
python -m pytest tests/unit/test_tom_*.py -v

# Run specific test
python -m pytest tests/unit/test_tom_hypothesis_generator.py::test_generate_hypotheses -v

# Check imports
python -c "from api.services.tom_active_inference import ToMActiveInferenceService"

# Run feature integration test (when ready)
python -m pytest tests/integration/test_tom_integration.py -v

# Format code
black api/services/tom_*.py api/models/tom_*.py

# Type check
mypy api/services/tom_active_inference.py
```

## Reference Documentation
- Feature Spec: `specs/051-tom-active-inference/spec.md` (44 FRs, 10 success criteria)
- Clarifications: See spec.md "Clarifications" section (5 key decisions)
- Active Inference: `docs/garden/content/concepts/precision-weighting.md`
- ThoughtSeeds: `docs/garden/content/concepts/thoughtseed-competition.md`
- Graphiti: `api/services/graphiti_service.py` (existing patterns)
- EFE Engine: `api/services/efe_engine.py` (winner selection logic)

## Success Metrics (from spec.md SC-001 to SC-010)
Track progress toward:
- 40% empathy quality improvement (SC-001)
- 90% validation pass rate (SC-002)
- <2s ToM generation latency (SC-003)
- 85% social memory accuracy (SC-004)
- 60% reduction in identity violations (SC-005)
