# Plan: 096 — Mental Models Book Integration

**Track ID:** 096-mental-models-book-integration  
**Spec:** [spec.md](./spec.md)  
**Workflow:** `conductor/workflow.md` — use Standard Task Workflow. Pre-code: read `.conductor/constraints.md`.

Tasks are the **source of truth**. Use `[ ]` / `[~]` / `[x]` and append 7-char commit SHA when done (e.g. `[x] Fix BeliefState import [a1b2c3d]`).

---

## Phase 1: Stabilize and unify interfaces

### P1.1: Test suite and shared types
- [x] **T096-001** Fix pytest collection: resolve `BeliefState` import in `scripts/verification/test_active_inference_integration.py`; gate or move Julia-dependent verification so pytest runs without Julia. [0ea6937]
- [ ] **T096-002** Define shared cognitive types in Dionysus: NarrativeState, MentalAction, MetacognitiveDecision, ArchitectureStep-shaped result (e.g. in `api/models/cognitive.py` or extend existing). Mirror neuroadaptive contracts.
- [ ] **T096-003** Single active-inference facade: choose (a) pymdp-only narrative/ANC adapter or (b) extend ActiveInferenceService with narrative mode (tags + precision → NarrativeInferenceResult). Implement and add minimal tests.

### P1.2: Optional neuroadaptive fix (external repo)
- [ ] **T096-004** *(Optional)* In neuroadaptive-scaffolding, add `NeuralPacket` (content, tags, precision) and `NeuralPacketizer` to `neuroadaptive_demo/packets.py` so cognitive_architecture/pipeline/active_inference_adapter import correctly. If work stays in Dionysus only, document “implement from neuroadaptive patterns” and skip.

---

## Phase 2: Embed ANC and three-level in Dionysus

### P2.1: ANC core
- [ ] **T096-005** Port ANC generative model: `build_anc_model()` (Context/Narrative/Attention, Attend/Ignore, Sensory/Proprioception) into `api/services/` or `api/agents/anc/`. No direct Neo4j; use pymdp or ActiveInferenceService under the hood.
- [ ] **T096-006** Port ANC environment and agent loop: ANCEnvironment (Attend → true sensory, Ignore → Null), ANCAgent-style loop (infer_states → infer_policies → sample_action → env.step) wired to the shared inference facade.
- [ ] **T096-007** Add unit tests for ANC generative model and env/agent loop; meet coverage target for new code.

### P2.2: Three-level and narrative
- [ ] **T096-008** Implement MetacognitiveController.decide(uncertainty) → MetacognitiveDecision(action, plasticity_gate) and ContextGate.is_open(signal). Expose one “architecture step” API returning (gate_open, decision, reasoning, self_model_state, mental_model_topics).
- [ ] **T096-009** Add W/T/H-state components (or equivalent): WStateManager, TStateTracker, HStateController under `api/services/` or anc, aligned with Spec 030 / metaplasticity where it exists. Prefer delegation to existing services.
- [ ] **T096-010** Add narrative pipeline entry point: text → packetize → infer(state, action, surprisal) → apply precision → mental_model update and/or MemoryBasinRouter.route_memory. Persist step summaries in architecture-step shape. Document inlet/outlet per constraints.
- [ ] **T096-011** Add integration/contract tests for architecture-step API and narrative pipeline.

---

## Phase 3: Cross-repo and maturation

### P3.1: Docs and conductor
- [ ] **T096-012** Document integration surface in Dionysus (e.g. in `docs/` or this track): what is canonical, what is adopted from neuroadaptive, what is reference-only.
- [ ] **T096-013** Decide and document: neuroadaptive-scaffolding as git submodule under `research/` or `lib/`, or external repo with “implement from neuroadaptive patterns” in specs.
- [ ] **T096-014** Ensure all new services (ANC, W/T/H, narrative pipeline) have inlet/outlet documentation and are wired per `.conductor/constraints.md`. Verify no orphan code.

### P3.2: Maturation gates
- [ ] **T096-015** Pytest green: all tests collect and run; Julia/optional backends gated so CI passes without them.
- [ ] **T096-016** Coverage ≥80% for new ANC/three-level/narrative modules; contract tests for new HTTP/Graphiti contracts as needed.
- [ ] **T096-017** Add “Chapter N → Implementation” mapping in this track’s spec or plan for each implemented chapter (concepts, files, assumptions).

---

## Phase 4: Book chapters (after Phase 1–3)

*Per-chapter tasks below are placeholders. Expand in plan when starting each chapter; each task follows Standard Task Workflow.*

### Ch1 — Three-level architecture
- [ ] **T096-101** Implement Level 1 (Use) and reflection principles; MentalModel abstraction; tests and Ch1→implementation mapping.
- [ ] **T096-102** Stubs or integration points for Level 2 (Adaptivity) and Level 3 (Control) per Ch1.

### Ch2 — Self-modeling networks
- [ ] **T096-201** Implement W/T/H fully per Ch2; Hebbian and excitability and metaplasticity wired; B/D updates and stress-blocking; tests and Ch2→implementation mapping.

### Ch3–Ch6 (follow-on)
- [ ] **T096-301** Ch3: Learning of a mental model (e.g. driver) using Ch1–2 base.
- [ ] **T096-401** Ch4: Metacognition over multiple mental models.
- [ ] **T096-501** Ch5 or Ch6: Counterfactual thinking or Flashbacks; align with 064/066 where applicable.

*(Later chapters Ch7–Ch20 to be added as new tasks when preceding phases are done.)*

---

## Phase completion

When a phase is finished, run **Phase Completion Verification** per `conductor/workflow.md`: test coverage for phase scope, run full test suite, manual verification plan, checkpoint commit, git notes, update plan with phase checkpoint SHA.
