# Tasks: Project-Wide Distillation & Wisdom Extraction

**Input**: spec.md

## Phase 1: Fleet Processing (Archive)

- [ ] T001 Deploy DAEDALUS fleet for conversation archive distillation (709 files)
- [ ] T002 Analysts MUST use the `/research.agent` protocol from Context-Engineering to extract structured "Neuronal Packets" from conversations
- [ ] T003 Preserve "Provenance" (Session ID, Date, Agent Type)

## Phase 2: Folder Cleanup (014-028)

- [ ] T004 Use Explorer Agents to review and merge orphaned folders (014-028)
- [ ] T005 Explorer agents MUST identify "Redundancies" between Spec 014-028 and the active Dionysus 3 engine

## Phase 3: Consolidation

- [ ] T006 Implement a `WisdomConsolidator` that merges overlapping insights into unified `KnowledgeDomain` nodes in Neo4j
- [ ] T007 Consolidate extracted Neuronal Packets into Neo4j Knowledge Domains

## Phase 4: Finalization

- [ ] T008 Final system-wide distillation report and cleanup
