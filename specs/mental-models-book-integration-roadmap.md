# Mental Models Book Integration — Context & Conductor Pointer

**Purpose:** High-level context for (1) integrating neuroadaptive-scaffolding with dionysus3-core, (2) maturing that base, and (3) implementing chapters of *Mental Models and Their Dynamics, Adaptation, and Control* (van Ments & Treur, Springer 2022) using Dionysus as the canonical codebase.

---

## Conductor is mandatory

**All work for this effort is tracked and executed via Conductor.**

- **Source of truth for tasks:** `conductor/tracks/096-mental-models-book-integration/plan.md`  
  Tasks use `[ ]` / `[~]` / `[x]` and commit SHAs. No parallel checklist lives in this file.
- **Workflow:** `conductor/workflow.md` — Standard Task Workflow (select from plan, mark [~], red-green-refactor, commit, git notes, update plan with [x] + SHA).
- **Constraints:** `.conductor/constraints.md` — Pre-code read, inlet/outlet, memory stack, no orphan code.
- **Track spec:** `conductor/tracks/096-mental-models-book-integration/spec.md` — Requirements, acceptance criteria, and integration surface.

This doc is **context only**. It does not replace the track’s `plan.md` or the Conductor workflow.

---

## Integration surface (what lives where)

- **Canonical base:** dionysus3-core (API, Memory stack, ConsciousnessManager, Thoughtseeds). Persistence and memory flows follow `.conductor/constraints.md`.
- **Adopted into Dionysus:** ANC (Context/Narrative/Attention, Attend/Ignore), three-level Use/Adaptivity/Control, W/T/H self-modeling, NarrativeState + MentalAction + precision, narrative pipeline. Implement under `api/`; no second repo at runtime.
- **Neuroadaptive-scaffolding:** Upstream reference (pymdp, anc, neuroadaptive_demo). Production runs in Dionysus; neuroadaptive informs design and tests only (or as optional submodule).

---

## Book-chapter order (dependency guidance)

Base = dionysus3-core after the integration tasks in track 096’s plan (unified types, ANC in Dionysus, three-level + narrative pipeline, W/T/H).

| Phase | Chapters | Focus |
|-------|----------|--------|
| D.1 | Ch1 | Three-level architecture (Use / Adaptivity / Control), reflection, MentalModel |
| D.2 | Ch2 | Self-modeling networks (W/T/H, Hebbian, excitability, metaplasticity) |
| D.3 | Ch3 | Learning of a mental model (e.g. driver) |
| D.4 | Ch4 | Metacognition over multiple mental models |
| D.5 | Ch6 or Ch5 | Counterfactual thinking or Flashbacks; align with 064/066 where applicable |

Later chapters (Ch5, Ch7–Ch20) are scheduled in the track’s plan as follow-on phases. **Per-chapter work is broken down in the track’s plan.md, not here.**

---

## References

- **Track:** `conductor/tracks/096-mental-models-book-integration/` (spec.md, plan.md)
- **Conductor:** `conductor/workflow.md`, `.conductor/constraints.md`, `conductor/tracks.md`
- **Existing specs:** `specs/030-neuronal-packet-mental-models/spec.md`; `conductor/tracks/095-comp-neuro-gold-standard/` (comp-neuro gold standard)
- **Book:** van Ments & Treur (eds.), *Mental Models and Their Dynamics, Adaptation, and Control*, Springer 2022; neuroadaptive-scaffolding `research/chapter1_complete.txt`, `chapter2_complete.txt`
