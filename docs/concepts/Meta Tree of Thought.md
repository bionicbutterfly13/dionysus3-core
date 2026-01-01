# Meta Tree of Thought

**Category:** Cognitive Architecture
**Related:** [[Fractal Metacognition]], [[Neural Packets]], [[Attractor Basin Dynamics]]
**Status:** Active Implementation (041-meta-tot-engine)

## The Problem: How Do You Decide How to Decide?

Standard Tree of Thought (ToT) explores decision branches. You evaluate options A, B, C and pick the best.

But **who decides which branches to explore?**

That's the meta layer. And most systems hardcode it - breadth-first, depth-first, beam search. Fixed strategies for fluid problems.

Meta-ToT makes the branching strategy *itself* a decision variable.

## How It Works

### Layer 1: Traditional ToT
```
Question: "Should I refactor this codebase?"
├─ Branch A: Refactor now
├─ Branch B: Refactor incrementally
└─ Branch C: Don't refactor
```

### Layer 2: Meta-ToT
```
Meta-question: "How should I explore this decision space?"
├─ Strategy A: Evaluate all branches equally (breadth-first)
├─ Strategy B: Deep-dive one promising path (depth-first)
└─ Strategy C: Prune obviously bad branches early (best-first)
```

The meta layer evaluates **which evaluation strategy** fits the problem structure.

For infrastructure cleanup (see [[2025-12-31-infrastructure-liberation]]), we used Strategy C:
- Recognized Archon dependency as "obviously not serving us"
- Pruned the entire branch immediately
- No need to explore "what if we fix Archon integration"

## Active Inference Connection

Meta-ToT implements **active inference** at the reasoning layer:

1. **Prior belief:** System should be lean (low free energy)
2. **Observation:** 4GB RAM consumed by unused dependency (high surprise)
3. **Inference:** This doesn't match the prior
4. **Action:** Update world (remove dependency) rather than update belief

See: [[Attractor Basin Dynamics]] for how this connects to stable system states.

## Implementation in Dionysus

**Spec:** `specs/041-meta-tot-engine/`
**Service:** `api/services/meta_tot_decision.py`

```python
class MetaToTEngine:
    """
    MCTS-based reasoning with active inference integration.
    Selects branching strategy based on:
    - Problem complexity (entropy)
    - Time constraints
    - Confidence in priors
    """
```

The engine doesn't just solve problems. It **selects which problem-solving approach to use**, based on the problem's information structure.

## Why This Matters for Consciousness

Real metacognition isn't "thinking about thinking" in some vague philosophical sense.

It's **computational**: Your brain selects different reasoning strategies for different problem types.

- Chess: Deep search on high-value moves
- Navigation: Breadth-first exploration of routes
- Social dynamics: Pattern matching to prior experiences

Meta-ToT makes this explicit. You can *see* the strategy selection. You can *modify* it.

This is how [[Fractal Metacognition]] emerges - the same meta-reasoning pattern applies at every cognitive scale.

## SEO Knowledge Gap: "Meta Tree of Thought AI"

Current landscape:
- "Tree of thought prompting" → Static chain-of-thought extensions
- "Meta-learning" → Training models to learn faster (different concept)
- "Metacognitive AI" → Philosophy papers, no implementations

**The gap:** Nobody's publishing working code for adaptive reasoning strategy selection in production cognitive systems.

We are. This is it.

## Application to Analytical Empaths

The [[Replay Loop]] teaches analytical empaths to recognize *when they're using the wrong decision strategy*.

Not wrong *decisions*. Wrong **meta-strategy**.

Example:
- **Problem:** Relationship conflict
- **Wrong meta-strategy:** Deep logical analysis (depth-first search through "what did I do wrong")
- **Right meta-strategy:** Pattern recognition ("this feels like childhood attachment dynamics")

Meta-ToT formalizes this. It makes the meta-strategy *visible*.

Once visible, you can change it.

## Links

- Implementation: `specs/041-meta-tot-engine/spec.md`
- Related concepts: [[Fractal Metacognition]], [[Attractor Basin Dynamics]]
- Application: [[Replay Loop]]
- Real-world example: [[2025-12-31-infrastructure-liberation]]

## Research Citations

- Yao et al. (2023): "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"
- Friston (2010): "The free-energy principle: a unified brain theory?" (active inference foundation)
- Spec 041: MCTS + Active Inference integration

---

*This concept is part of the [[Multi-Tier Memory Architecture]] knowledge web. Each concept page feeds episodic and semantic memory tiers.*
