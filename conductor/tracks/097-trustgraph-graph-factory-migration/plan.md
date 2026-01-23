# Plan: Track 097 - TrustGraph Graph Factory Migration (CGR3 Replacement)

**Status:** Planned

## Phase 1: Inventory & Mapping (CGR3 -> TrustGraph)
- [ ] **Task 1.1**: Inventory CGR3 usage (services, tools, background workers). (branch: `097-cgr3-inventory`)
- [ ] **Task 1.2**: Review TrustGraph Graph Factory APIs and identify feature parity. (branch: `097-graph-factory-review`)
- [ ] **Task 1.3**: Map CGR3 capabilities to Graph Factory equivalents (retrieve-rank-reason, MACER loops, context graph queries). (branch: `097-feature-mapping`)

## Phase 2: Migration Design
- [ ] **Task 2.1**: Define new service boundary for Graph Factory (adapter/shim) in Dionysus. (branch: `097-graph-factory-adapter`)
- [ ] **Task 2.2**: Draft migration plan for CGR3 call sites (ContextDiscoveryService, BackgroundWorker, ModelReconstructionService, DiscoveryTools). (branch: `097-callsite-plan`)

## Phase 3: Implementation (CGR3 Replacement)
- [ ] **Task 3.1**: Implement Graph Factory adapter and replace CGR3 imports. (branch: `097-graph-factory-impl`)
- [ ] **Task 3.2**: Update call sites to use Graph Factory adapter. (branch: `097-graph-factory-callsite-updates`)
- [ ] **Task 3.3**: Remove/disable CGR3 dependency wiring after migration. (branch: `097-cgr3-deprecation`)

## Phase 4: Verification & Docs
- [ ] **Task 4.1**: Add/adjust tests for Graph Factory reasoning flows. (branch: `097-graph-factory-tests`)
- [ ] **Task 4.2**: Update docs/specs referencing CGR3/ToG-3. (branch: `097-graph-factory-docs`)

## Phase 5: Research Review (Post-migration Priority)
- [ ] **Task 5.1**: Review MemEvolve paper (`/Volumes/Asylum/repos/MemEvolve/2512.18746v1.pdf`). (branch: `097-research-memevolve`)
- [ ] **Task 5.2**: Review Nemori paper (`/Volumes/Asylum/repos/nemori/2508.03341v3.pdf`). (branch: `097-research-nemori`)
- [ ] **Task 5.3**: Review Context Graph paper (`/Volumes/Asylum/_Downloads/2406.11160v3.pdf`). (branch: `097-research-context-graph`)
- [ ] **Task 5.4**: Review ToBU/related paper (`/Volumes/Asylum/_Downloads/2412.05447v3.pdf`). (branch: `097-research-tobugraph`)
