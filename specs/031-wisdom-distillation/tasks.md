# Tasks: Wisdom Distillation (The System Soul)

**Input**: spec.md, plan.md

## Phase 1: Foundation (P1)
- [ ] T001 Define `WisdomUnit` and specialized subclasses (`MentalModel`, `StrategicPrinciple`, `CaseStudy`) in `api/models/wisdom.py`.
- [ ] T002 Implement `WisdomService` to load raw JSON extracts and prepare them for synthesis.

## Phase 2: The Distiller Agent (P1)
- [ ] T003 Create `api/agents/knowledge/wisdom_distiller.py` using `CodeAgent` with Docker sandboxing.
- [ ] T004 Implement `distill_wisdom_cluster` smolagent tool: synthesizes canonical definitions from multiple fragments.

## Phase 3: Graph Integration (P1)
- [ ] T005 Implement `WisdomService.persist_distilled_unit`: writes to Neo4j and creates `DERIVED_FROM` links to original episodes.
- [ ] T006 Implement "Richness Scoring" (FR-031-003) based on MoSAEIC window coverage.

## Phase 4: Worldview Integration (P2)
- [ ] T007 Update `WorldviewIntegrationService` to prioritize distilled units as Bayesian priors.
- [ ] T008 Update `PerceptionAgent` description to explicitly look for `StrategicPrinciples` during recall.

## Phase 5: Verification (P1)
- [ ] T009 Run the full distiller on `wisdom_extraction_raw.json` and verify SC-001 (50% reduction).
- [ ] T010 Unit test: Verify provenance chain mapping.