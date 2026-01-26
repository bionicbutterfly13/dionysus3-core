# Fractal Metacognition & Meta-ToT Pattern Audit

**Date:** 2026-01-25  
**Context:** Fractal metacognition, Meta Tree of Thought (041), actor-judge vs CPA domains  
**Focus:** We have fractal metacognition and Meta-ToT; Meta-ToT may have been forced from an original **actor-judge** (generator + critic) pattern to the current **CPA domain-phase** pattern set.

---

## 1. What We Have

### Fractal metacognition

- **Concept:** The *same* reasoning pattern applies at every cognitive scale (code → architecture → life). Self-similar meta-questions.
- **Docs:** `docs/concepts/Fractal Metacognition.md`, links from Multi-Tier Memory, Neural Packets, Replay Loop, Meta Tree of Thought.
- **Implementation:** `MetacognitionAgent` (hierarchical ThoughtSeeds, parent/child); `api/services/fractal_reflection_tracer.py`; `context_packaging` / `priors` (Phase 4); `specs/037-context-engineering-upgrades/02_fractal_thoughts.md` (recursive ThoughtSeed containment).

### Meta Tree of Thought (Meta-ToT)

- **Spec:** `specs/041-meta-tot-engine/`. MCTS-style expansion, active-inference scoring, thresholded activation.
- **Implementation:** `api/services/meta_tot_engine.py` (primary), `api/services/meta_tot_decision.py`, `meta_tot_trace_service`. Used by `ConsciousnessManager` when `coordination_plan.mode == "meta_tot"`.
- **Alternative:** `api/core/engine/meta_tot.py` — older engine with `ThoughtNode`, `expand_node`, `score_thought`, `select_best_branch`. Uses `ActiveInferenceWrapper`; no CPA domains. Still present but not the main workflow path.

---

## 2. Original vs Current Pattern

### Original: actor–judge (generator + critic)

From D2 `meta_tot_integration_conversation.json` and related design:

- **Primary agent:** Generates initial responses / architectural intentions / thought candidates.
- **Meta agent:** Critiques and improves prompts; refines thoughtseeds from evaluated outputs.
- **Data flow:** `Language Model ↔ Meta Agent ↔ Tree of Thoughts`.
- **Feedback:** Evaluated thoughts → Meta agent → improved prompts → next generation.

So the **original** Meta-ToT was **actor–judge**: one generates, one evaluates/critiques. Classic ToT “proposer + evaluator” style.

### Current: CPA domain phases

- **Pattern:** Cycled **CPA (Creative Problem Solving) domain phases**: explore → challenge → evolve → integrate. Depth cycles over `cpa_domains[depth % 4]`.
- **Node types:** ROOT, SEARCH, EXPLORATION, CHALLENGE, EVOLUTION, INTEGRATION, OUTCOME, LEAF. Map from domains via `_domain_to_node_type`.
- **Expansion:** Single LLM call per node (`_generate_candidates`) produces “reasoning branches” for that domain. **Scoring** is via `ActiveInferenceState` (prediction error, free energy), not a separate judge/critic model.
- **Strategies:** `SURPRISE_MAXIMIZATION` (explore, challenge), `FREE_ENERGY_MINIMIZATION` (evolve, integrate).

There is **no** distinct “Meta agent” or judge; the “evaluate” step is active-inference scoring, not a separate critic. The **pattern set** is CPA domains + exploration strategies, not actor–judge.

### Shift

Meta-ToT was **forced** (or evolved) from **actor–judge** to **CPA domain-phase** expansion. The generator+critic loop is absent in the current implementation; we have domain-cycled generation + unified scoring instead.

---

## 3. Fractal Metacognition ↔ Meta-ToT

- **Fractal metacognition:** Same meta-pattern at every scale. “Does this serve the purpose?” at code, system, and life level.
- **Actor–judge as fractal:** Propose vs evaluate is a **meta** pattern that can apply at multiple scales (e.g. Reasoning proposes, Metacognition evaluates).
- **CPA domains:** Also a meta-level structure (how to explore the thought space) but **phase-based** (explore/challenge/evolve/integrate) rather than **role-based** (generator vs critic).

So we have two different “meta” designs: **role-based** (actor–judge) and **phase-based** (CPA). The current codebase implements the latter.

---

## 4. Where This Lives in Code

| Component | Location | Pattern |
|-----------|----------|---------|
| Meta-ToT engine (active) | `api/services/meta_tot_engine.py` | CPA domains, single LLM expand, active-inference scoring |
| Meta-ToT core (legacy) | `api/core/engine/meta_tot.py` | ThoughtNode, expand_node, score_thought, no CPA |
| Meta-ToT decision | `api/services/meta_tot_decision.py` | Thresholded Meta-ToT activation |
| Fractal metacognition | `api/agents/metacognition_agent.py`, `fractal_reflection_tracer`, context_packaging, 037 | Hierarchical ThoughtSeeds, recursive containment |
| D2 reference (actor–judge) | `Dionysus-2.0/meta_tot_integration_conversation.json` | Primary + Meta agent, generator + critic |

---

## 5. Recommendations

1. **Document the delta:** Keep this audit (and references to `meta_tot_integration_conversation.json`) so the actor–judge → CPA shift is explicit.
2. **Optionally restore actor–judge:** If we want the original “Primary generates + Meta critiques” loop, we could:
   - Add an explicit **critic** step (e.g. MetacognitionAgent or a dedicated judge) that scores or revises branches **after** generation, and feed that back into the next expansion.
   - Hybrid: retain CPA **domains** for structure, but add a **critic** phase (e.g. “challenge” or “evolve” implemented as generator + judge).
3. **Fractal alignment:** If we restore actor–judge, frame it as **fractal**: same propose/critique pattern at ToT level and at OODA level (e.g. Reasoning vs Metacognition).
4. **Spec updates:** Consider updating `specs/041-meta-tot-engine/spec.md` to note the original actor–judge design, the current CPA-domain implementation, and any decision to restore, hybridize, or keep as-is.

---

## 6. Links

- [Fractal Metacognition](../concepts/Fractal%20Metacognition.md)
- [Meta Tree of Thought](../concepts/Meta%20Tree%20of%20Thought.md)
- [041 Meta-ToT Spec](../../specs/041-meta-tot-engine/spec.md)
- D2: `meta_tot_integration_conversation.json`, `backend/src/services/enhanced_meta_tot_active_inference.py`

---

## User Notes

<!-- Add your permanent notes here. -->
