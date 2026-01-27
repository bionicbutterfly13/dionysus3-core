# Feature 096: Mental Models Book Integration

**Track ID:** 096-mental-models-book-integration  
**Spec:** This file  
**Plan (source of truth for tasks):** [plan.md](./plan.md)  
**Context doc:** [specs/mental-models-book-integration-roadmap.md](../../../specs/mental-models-book-integration-roadmap.md)

## Overview

Integrate neuroadaptive-scaffolding patterns (ANC, three-level architecture, narrative pipeline, W/T/H self-modeling) into dionysus3-core and use that base to implement multiple chapters of *Mental Models and Their Dynamics, Adaptation, and Control* (van Ments & Treur, Springer 2022). All work follows `conductor/workflow.md` and `.conductor/constraints.md`; tasks live in `plan.md` only.

## Integration surface

- **Canonical base:** dionysus3-core (API, Memory stack, ConsciousnessManager, Thoughtseeds). No direct Neo4j; inlet/outlet per constraints.
- **Adopted into Dionysus:** ANC (Context/Narrative/Attention, Attend/Ignore), three-level Use/Adaptivity/Control, W/T/H, NarrativeState + MentalAction + precision, narrative pipeline. Implement under `api/`; wire to Memory stack where required.
- **Neuroadaptive-scaffolding:** Upstream reference; production runs in Dionysus.

## Requirements (summary; tasks in plan.md)

- **Phase I (Stabilize):** Pytest green, shared cognitive types, single active-inference facade for narrative/ANC.
- **Phase II (Embed):** ANC generative model + env + agent loop in Dionysus; three-level controller and step API; W/T/H stubs; narrative pipeline entry point.
- **Phase III (Cross-repo):** Document integration surface; neuroadaptive as submodule or doc-only.
- **Maturation:** Coverage ≥80% for new code, contract tests, inlet/outlet per new service, book–spec mapping per chapter.
- **Book chapters:** Ch1 → Ch2 → Ch3 → Ch4 → Ch5/Ch6 order; per-chapter tasks and chapter–spec mapping in plan.md.

## Conductor compliance

- All tasks are in `plan.md` with `[ ]` / `[~]` / `[x]` and commit SHA when done.
- Standard Task Workflow: select from plan → [~] → red-green-refactor → commit → git notes → [x] + SHA in plan → commit plan.
- Pre-code: read `.conductor/constraints.md` before changing code.
- Phase completion: follow Phase Completion Verification in `conductor/workflow.md` when a phase in plan.md is finished.

## References

- `conductor/workflow.md`, `.conductor/constraints.md`, `conductor/tracks.md`
- `specs/030-neuronal-packet-mental-models/spec.md`, `conductor/tracks/095-comp-neuro-gold-standard/`
- Neuroadaptive: `docs/plans/2025-01-25-full-integration-path.md`, `research/chapter1_complete.txt`, `chapter2_complete.txt`
