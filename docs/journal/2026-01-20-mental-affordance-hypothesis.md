# The Mental Affordance Hypothesis: Extending Perception-Action Theory to Internal Cognition

**Date:** 2026-01-20
**Tags:** #ultrathink #affordances #mcclelland #cisek #embodied-cognition #active-inference

## Executive Summary
This report helps reconcile the implementations of Feature 071 (Cisek Competition) and Feature 072 (Attendabilia). It critiques McClelland's "Menu" metaphor for mental affordances, favoring a **Distributed Control** model where "mental" actions are grounded in reused sensorimotor loops.

### Core Debate
*   **McClelland (MAH)**: We perceive "mental affordances" (attendability, countability) which presents a "Menu" for a deliberative subject to choose from.
*   **Critique (Bruineberg/van den Herik)**: The "Menu" implies a Cartesian homunculus. Instead, **Action Selection IS Competition** (Cisek). There is no "decider" separate from the competition of affordances.

### Architectural Implications for Dionysus
1.  **Distributed Control**: Our `resolve_competition` methods (in `ArousalSystemService`) must not be "utility calculators" for a separate agent, but the *actual mechanism of selection* via mutual inhibition.
2.  **Continuity**: Feature 072's "Attention" is not a separate "mental" realm but a **covert action** using the same OODA loops.
3.  **Identity as Affordance Landscape**: Transformational work involved changing the *landscape* of what is salient (potentiated), not just "reframing" thoughts.

## Full Report

### Theoretical Foundations
**Affordances in Ecological Psychology**
Gibson (1966) introduced affordances as direct action possibilities, neither objective nor subjective but relational. The "sandwich model" (Perception -> Cognition -> Action) is rejected in favor of an integrated loop.

**The Affordance Competition Hypothesis (ACH)**
Cisek & Kalaska propose parallel specification of multiple potential actions. Selection emerges from distributed competition, not serial decision-making.

**McClelland's Mental Affordance Hypothesis (MAH)**
Extends affordances to include:
*   **Attention**: Covertly concentrating.
*   **Counting**: Internal enumeration.
*   **Imagination**: Mental simulation.

Claims these satisfy Opportunity, Perceptibility, and Potentiation conditions.

### Critical Analysis: The Cartesian Problem
**The Homuncular Menu Metaphor**: McClelland's "Menu" implies a selector after perception. ACH rejects this; competition *is* selection.
**The Phenomenology Problem**: We don't experience a menu; we respond to solicitations (Dreyfus & Kelly).
**The Covert/Overt Distinction**: Fails to track Mental/Bodily. "Covert" attention may involve microsaccades. Counting is grounded in finger representations (neural reuse).

### Alternative Framework: Embodied Mental Action
**Distributed Control**: Control emerges from self-organization (like bird flocks), not a controller module.
**Neural Reuse**: "Mental" actions recycle sensorimotor circuits.
**Epistemic Foraging**: Attention/Imagination are acts of Active Inference to reduce uncertainty (Free Energy Principle).

### Applications
**AI Systems**: Should model cognition as distributed competition among affordance-related patterns, not symbolic rule systems.
**Coaching**: "Identity Transformation" is restructuring the affordance landscape—making new mental actions (e.g., "imagining success") perceptible and potentiated.

---
*Synthesized from User Ultrathink Session*
