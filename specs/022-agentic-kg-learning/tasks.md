# Tasks: Agentic Knowledge Graph Learning Loop

**Input**: spec.md, plan.md

## Phase 1: Extraction Agent/Tool (P1)
- [ ] T001 Implement relationship extraction tool/agent using LLM with dynamic relation types and confidences
- [ ] T002 Include provenance (source doc, run id, model id) in outputs

## Phase 2: Attractor Basins (P1)
- [ ] T003 Implement basin store (concept clusters, strengths, related basins)
- [ ] T004 Feed basin context into extraction prompts; update strengths on each run

## Phase 3: Cognition-Base Learning (P2)
- [ ] T005 Record successful patterns/strategies; implement priority boosts
- [ ] T006 Apply boosts to subsequent extraction runs

## Phase 4: Graph Storage & Review (P1)
- [ ] T007 Write relationships to Graphiti/Neo4j with confidence and dynamic types
- [ ] T008 Route low-confidence edges to human review queue

## Phase 5: Evaluation Hooks (P2)
- [ ] T009 Add batch evaluation hooks (precision proxy or review rate) and logging

## Phase 6: Testing (P1/P2)
- [ ] T010 Test dynamic relation type creation and storage
- [ ] T011 Test basin strengthening across multiple docs
- [ ] T012 Test learning boosts affecting subsequent runs

## Phase 7: Docs (P3)
- [ ] T013 Add usage doc snippet and expected outputs
