# Track 094: Dynamical Cognition Synergy (Enhanced)

## Phase 0: Source Review + Architecture Audit
- [x] (branch: 094-phase0-inventory) Inventory existing memory/graph/active-inference components (attractor basins, neural packets, worldview/identity, CGR3 usage) and record in `conductor/tracks/094-dynamical-cognition-synergy/inventory.md`. (d17df58)
- [ ] (branch: 094-phase0-research) Review local papers/repos (Nemori, MemEvolve, AutoSchemaKG, Graphiti, TrustGraph, Context-Graph, TobuGraph, Decision Trace) and summarize integration deltas in inventory.
- [ ] (branch: 094-phase0-ingest-rules) Validate ingestion rules for Neo4j/Graphiti/Nemori protocols and document gaps in inventory + docs.

## Phase 1: Memory Manifesto + Pipeline Governance
- [ ] (branch: 094-phase1-manifesto) Draft unified `specs/MEMORY_MANIFESTO.md` superseding prior memory docs.
- [ ] (branch: 094-phase1-pipeline) Document mandatory memory pipeline (step-by-step) + restricted access rules in `docs/memory-pipeline.md`.
- [ ] (branch: 094-phase1-docs) Update CLAUDE.md, GEMINI.md, and other docs to reference the new manifesto; remove/flag obsolete manifestos if present.

## Phase 2: Attractor Basins + Neural Packets Alignment
- [ ] (branch: 094-phase2-basin-map) Map current attractor basin implementation + integration points; note label/schema drift.
- [ ] (branch: 094-phase2-basin-role) Define target role for attractor basins in memory + active inference loops; document in `conductor/tracks/094-dynamical-cognition-synergy/attractor_basin_role.md`.
- [ ] (branch: 094-phase2-neural-packets) Repair architecture usage of neural packets / neural fields / mental models; update code + docs.
- [ ] (branch: 094-phase2-tests) Add tests for basin label usage, ThoughtSeed basin linkage, and neural packet/mental model integration (TDD red/green/refactor).

## Phase 3: Active Inference Formalization (Core Math)
- [ ] (branch: 094-phase3-aiblocks) Align active inference math with factorized A/B models + VFE inference.
- [ ] (branch: 094-phase3-prediction-error) Integrate prediction error/surprisal propagation across services.
- [ ] (branch: 094-phase3-tests) Add unit tests for formal inference + arousal/confidence loops.

## Phase 4: Graph Migration Planning (CGR3 -> Graph Factory/TrustGraph)
- [ ] (branch: 094-phase4-cgr3-map) Locate CGR3 usage and map features for migration.
- [ ] (branch: 094-phase4-migration-plan) Create migration plan to Graph Factory/TrustGraph with feature parity notes.
- [ ] (branch: 094-phase4-hybrid-review) Assess TobuGraph + Context-Graph hybrid viability and document recommendation.

## Phase 5: Integration of External Tooling
- [ ] (branch: 094-phase5-tooling) Determine how AutoSchemaKG, Graphiti, Nemori, MemEvolve, SmolAgents contribute to pipeline.
- [ ] (branch: 094-phase5-smolagents) Audit existing SmolAgents usage and propose integration alignment.
- [ ] (branch: 094-phase5-tests-docs) Add/adjust tests and docs for tool synergy.

## Execution Notes
- TDD is mandatory: write failing tests before implementation.
- Use git notes for each completed task and update plan with commit SHAs.
- Update `docs/journal/` after each completed feature/milestone.
- If any old implementation is removed, add mandatory notifications in `GEMINI.md` and `CLAUDE.md`.
