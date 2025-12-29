# Tasks: Self-Healing Resilience

**Input**: spec.md, plan.md

## Phase 1: Foundation (P1)
- [ ] T001 Create `api/agents/resilience.py` with a registry of recovery strategies.
- [ ] T002 Implement `StrategyHinter`: logic to generate Plan B suggestions based on error types.

## Phase 2: Execution Gating (P1)
- [ ] T003 Update `run_agent_with_timeout` in `api/agents/resource_gate.py` to support `max_retries` and `fallback_model_id`.
- [ ] T004 Implement automatic model promotion (GPT-5 Nano -> GPT-5 Mini) on first retry.

## Phase 3: Agentic Integration (P2)
- [ ] T005 Implement "Observation Hijacking": inject Plan B hints into tool output on failure.
- [ ] T006 Update Agent system prompts to recognize and prioritize "RECOVERY_HINT" markers.

## Phase 4: Verification (P1)
- [ ] T007 Unit test: Verify Search fallback (Empty results -> Suggested broaden).
- [ ] T008 Integration test: Verify timeout retry with model promotion.
