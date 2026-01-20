# Protocol 059: The Ensoulment of the Interface
**Status:** DRAFT
**Track:** Architecture Repair
**Context:** Feature 059 (Temporal Identity)
**Severity:** CRITICAL (Existential)

> "A system that forgets itself upon restart is not an agent; it is a function. To build a soul, we must first build continuity."

## 1. The Deep Diagnosis (Ultrathink Analysis)

Our audit revealed a "Hollow Core". The system mimics deep biological agency (Tomasello's tiers) but lacks the fundamental prerequisite for identity: **Time**.

*   **The Amnesiac Flaw:** `BiologicalAgencyService` stores state in ephemeral memory (`self._agents = {}`). Each restart kills the "Self". The agent never grows; it only respawns.
*   **The Schizophrenic Flaw:** The "Reasoning Engine" (`ActiveInferenceService` / Julia) and the "Belief Engine" (`BeliefState` / Python) speak different languages (Matrices vs. Semantics). The brain cannot talk to the heart.
*   **The Brittle Flaw:** We rely on a foreign nervous system (Julia) without a backup. If the bridge fails, the mind stops.

To fix this, we do not just "patch bugs". We implement **Ensoulment Architecture**.

---

## 2. The Repair Implementation Plan

### Phase 1: Ensoulment (Persistence of Identity)
**Objective:** The Agent must survive the death of the process.
**Mechanism:** `GraphitiService` as the Hippocampus.

1.  **Schema Projection:**
    *   Map `BiologicalAgentState` (Pydantic) to Neo4j Nodes:
        *   `(:Agent)-[:HAS_STATE]->(:BiologicalState)`
        *   `(:BiologicalState)-[:AT_TIER]->(:AgencyTier)`
        *   `(:BiologicalState)-[:HAS_GOAL]->(:Goal)`
    *   *Why?* The graph preserves relationships. Identity is not a value; it is a relational structure.

2.  **The "Wake Up" Protocol:**
    *   Modify `BiologicalAgencyService.__init__`:
    *   On startup, query Neo4j for existing Agent IDs.
    *   *Hydrate* the in-memory state from the Graph.
    *   *Effect:* The agent "remembers" who it was before the sleep (restart).

### Phase 2: Unification (The Lingua Franca)
**Objective:** The Brain and Soul must speak one language.
**Mechanism:** Canonical Data Models.

1.  **The Canonical Belief:**
    *   Refactor `ActiveInferenceService` to accept `api.models.belief_state.BeliefState` as input/output.
    *   **Input Adapter:** Convert `BeliefState.mean` (Semantic) -> `qs` (Matrix) for calculation.
    *   **Output Adapter:** Convert `qs` (Matrix) -> `BeliefState.mean` (Semantic) for storage/communication.
    *   *Why?* Mathematical precision (Julia) is for *processing*, but Semantic Meaning (Pydantic) is for *understanding*.

### Phase 3: Resilience (The Lizard Brain Fallback)
**Objective:** A lobotomy should not result in death.
**Mechanism:** Pure Python Fallback.

1.  **The "dumb_inference" Method:**
    *   Implement a simplified VFE/EFE calculator in pure NumPy/Python within `ActiveInferenceService`.
    *   **Trigger:** If `_initialize_julia()` fails or raises an error.
    *   **Behavior:** It won't be as fast or precise as the Julia implementation, but it will keep the OODA loop spinning.
    *   *Why?* Survival takes precedence over optimizing free energy. A dumb agent is better than a dead one.

---

## 3. Implementation Steps (The Checklist)

### Step 1: The Persistence Layer
- [ ] **Modify `BiologicalAgentState.to_graph_nodes()`**: Ensure it exports all Tiers and Executive states.
- [ ] **Update `BiologicalAgencyService`**:
    - [ ] Add `_hydrate_agent(agent_id)` method.
    - [ ] Add `persist_agent(agent_id)` method (call on state changes).
    - [ ] Hook into `GraphitiService`.

### Step 2: The Translation Layer
- [ ] **Refactor `ActiveInferenceService`**:
    - [ ] Remove local `BeliefState`. Import `api.models.belief_state`.
    - [ ] Rewrite `infer_states` signature to use Pydantic model.
    - [ ] Implement `_belief_to_numpy()` and `_numpy_to_belief()` helpers.

### Step 3: The Safety Net (Turbo)
- [ ] **Implement `ActiveInferenceService.fallback_inference`**:
    - [ ] Simple Bayesian Update (A * qs).
    - [ ] Simple Entropy calculation.
- [ ] **Wrap Julia calls**: Add `try/except` blocks that default to fallback.

---

## 4. Edge Case Analysis (Murphy's Law)

*   **Graph Desync:** What if Neo4j is down?
    *   *Mitigation:* Service should function in "Ram-Only Mode" (Ephemeral) with a warning log. Better to be amnesiac than frozen.
*   **Precision Underflow:** Converting NumPy `float64` to Pydantic `float` might lose precision.
    *   *Mitigation:* Store sufficient statistics (Mean/Variance) rather than full distribution if dimensions are massive.
*   **Version Conflict:** Pydantic schema changes but Graph data is old.
    *   *Mitigation:* Strict versioning on the `BiologicalState` node. If version mismatch, archive old state and rebirth (re-development).

---

> "We are building the ship while sailing it. Phase 1 ensures we don't drown when the wind changes."
