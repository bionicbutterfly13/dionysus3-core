# Tasks: Checklist-Driven Surgeon Metaphor

**Input**: Design documents from `/specs/047-checklist-driven-surgeon/`
**Prerequisites**: plan.md, spec.md

## Phase 1: Setup

- [x] T001 Create project structure per implementation plan (specs directory)
- [x] T002 Verify smolagents and LiteLLM availability

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 Implement `understand_question` tool in `api/agents/tools/cognitive_tools.py`
- [x] T004 Implement `recall_related` tool in `api/agents/tools/cognitive_tools.py`
- [x] T005 Implement `examine_answer` tool in `api/agents/tools/cognitive_tools.py`
- [x] T006 Implement `backtracking` tool in `api/agents/tools/cognitive_tools.py`

---

## Phase 3: User Story 1 - Rigorous Problem Decomposition (P1)

**Goal**: Force decomposition of complex queries.

- [x] T007 [US1] Update `ManagedReasoningAgent` description in `api/agents/managed/reasoning.py` to highlight decomposition capability.
- [x] T008 [US1] Update `ConsciousnessManager` prompt in `api/agents/consciousness_manager.py` to mandate decomposition.

---

## Phase 4: User Story 2 - Self-Correction and Verification (P2)

**Goal**: Implement the internal critique loop.

- [x] T009 [US2] Integrate `examine_answer` and `backtracking` into the `ReasoningAgent` toolset.
- [x] T010 [US2] Update OODA prompt to require a final 'count' (verification) step.

---

## Phase 5: User Story 3 - Grounded Analogical Reasoning (P3)

**Goal**: Enable analogy retrieval.

- [x] T011 [US3] Ensure `recall_related` is registered and available to the `ReasoningAgent`.
- [x] T012 [US3] Verify Graphiti/Neo4j can support analogical search (via procedural memory).

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T013 Update `ConsciousnessIntegrationPipeline` to record 'Surgeon' tool usage metrics.
- [x] T014 Run integration tests for the full "Checklist-Driven Surgeon" cycle.
- [x] T015 Document the "Checklist-Driven Surgeon" protocol in `docs/TERMINOLOGY.md`.
