# Implementation Plan: Context Engineering Upgrades

**Branch**: `037-context-engineering-upgrades` | **Date**: 2025-12-30 | **Spec**: [specs/037-context-engineering-upgrades/*.md]

This plan implements critical reliability, intelligence, and efficiency upgrades derived from the `Context-Engineering` framework and `smolagents` native patterns. It addresses fragility in the Heartbeat loop (SchemaContext), lack of recursive thought structure (Fractal Thoughts), monitoring gaps (Neural Field Metrics), and stability issues (Native Callbacks).

## I. Architecture & Design

### 1. SchemaContext (Reliability)
- **Problem**: Heartbeat decisions use raw LLM calls with fragile string parsing.
- **Solution**: Implement `SchemaContext` wrapper that enforces `HeartbeatDecision` Pydantic model via validation loops and schema-augmented prompts.
- **Components**:
    - `api/utils/schema_context.py`: Core wrapper class.
    - `HeartbeatDecision` (updated): Pydantic model with `json_schema_extra` for strict validation.
    - `HeartbeatService`: Updated to use `SchemaContext.query()` instead of `chat_completion`.

### 2. Fractal Metacognition (Intelligence)
- **Problem**: Thoughts are flat; no way to model "thinking about X" structurally.
- **Solution**: Update `ThoughtSeed` to support recursive "Link by Reference" persistence.
- **Components**:
    - `ThoughtSeed` model: Add optional `child_thought_ids: List[str]` field.
    - `MetacognitionAgent`: Update prompt to output recursive structures (parent/child relationships).

### 3. Native Callbacks (Stability)
- **Problem**: `agent.step_callbacks = [...]` monkey-patching is non-idiomatic and fragile.
- **Solution**: Use `smolagents.CallbackRegistry` pattern.
- **Components**:
    - `api/agents/consciousness_manager.py`: Refactor initialization to use `CallbackRegistry.register`.
    - `MoSAEIC` hooks: Ensure they are compatible with the `(step, **kwargs)` signature.

### 4. Neural Field Metrics (Efficiency)
- **Problem**: No metric for "spinning" (high output, low info) or "drift" (hallucination).
- **Solution**: Calculate `compression` (tokens_in/tokens_out) and `resonance` (embedding similarity).
- **Components**:
    - `ContextStreamService`: Add `compression` and `resonance` calculation logic.
    - `FlowState`: Update enum thresholds based on new metrics.

## II. Implementation Phases

### Phase 1: Native Callbacks (Stability) - P3
Refactor the callback system first to ensure observability remains stable during later changes.
- Create `api/utils/callbacks.py` helper if needed.
- Update `ConsciousnessManager` to use `CallbackRegistry`.
- Verify audit logging works.

### Phase 2: SchemaContext (Reliability) - P1
Implement the core reliability wrapper.
- Create `SchemaContext` class.
- Define `HeartbeatDecisionSchema` via Pydantic.
- Refactor `HeartbeatService` to use it.
- **Validation**: Mock test with invalid JSON to verify retry logic.

### Phase 3: Neural Field Metrics (Efficiency) - P2
Add efficiency monitoring.
- Update `ContextStreamService` with `compression` (Input/Output ratio) and `resonance` (SentenceTransformer similarity).
- **Clarification**: `compression` = `tokens_in / tokens_out` (High score = high compression/concise summary).

### Phase 4: Fractal Thoughts (Intelligence) - P2
Enable recursive thinking.
- Update `ThoughtSeed` model.
- Update `MetacognitionAgent` prompt.
- **Persistence**: Store child IDs in parent node metadata.

### Phase 5: Verification & Polish
- Run full integration tests.
- Verify observability in `dionysus_mcp`.

## III. Testing Strategy

- **Unit Tests**:
    - `test_schema_context.py`: Verify validation retry logic and timeout handling.
    - `test_neural_metrics.py`: Verify compression/resonance calculations on known text pairs.
- **Integration Tests**:
    - `test_heartbeat_reliability.py`: Trigger heartbeat with mock "bad" LLM to ensure recovery.
    - `test_fractal_persistence.py`: Create parent/child thoughts and verify retrieval.

## IV. Risks & Mitigation

- **Risk**: Schema validation loops might increase latency.
- **Mitigation**: Use `gpt-5-nano` (fast model) and set a strict 5s-10s timeout per attempt.
- **Risk**: Recursive thoughts might complicate graph queries.
- **Mitigation**: Use "Link by Reference" (flat nodes with ID lists) for V1 to keep Neo4j schema simple.
