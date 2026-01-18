# Adaptive Narrative Control & The Computational Unconscious
**Source**: "Adaptive Narrative Control Theory" (Provided Text, 2024)
**Context**: Feature 059 - Temporal Identity & Psychopathology Modeling

---

## 1. Core Thesis: Pragmatism Over Truth
The brain does not sample information to build a *veridical* model of the world. It samples information to construct a **Narrative** that ensures **Adaptive Behavior** (Survival/Functionality).
*   **The Trade-off**: The system balances **Epistemic Integrity** (Truth) vs. **Pragmatic Utility** (Function).
*   **Affective Regulation**: To function (e.g., walk a tightrope, perform on stage), the system *must* attenuate inputs that would cause dysregulation (fear, anxiety). "Don't look down."

## 2. The Mechanism: Motivated Inattention (Avoidant Mental Action)
*   **Mental Action**: The endogenous control of attention (Precision Weighting).
*   **The Algorithm**:
    1.  The system simulates: "If I attend to X, my Action Confidence ($\gamma$) will drop."
    2.  The system predicts: "Low $\gamma$ leads to Suboptimal Behavior (Freezing/Panic)."
    3.  **Action**: The system proactively **attenuates** X (Motivated Inattention).
*   **Result**: The "Narrative" (Conscious Experience) excludes X. The system remains confident and functional *in the short term*.

## 3. The Pathology: Canalization
When Motivated Inattention becomes **habitual** (Hebbian learning), it leads to **Canalization** (Deep Attractors).
*   **Rigidity**: The system *automatically* ignores X, even when X is now safe or necessary.
*   **The Computational Unconscious**: The set of attenuated inputs (repressed content). They drive behavior (by shaping the posterior) but are never "seen".
*   **Alexithymia**: By consistently ignoring interoceptive signals (stress/pain) to "power through", the system loses **Emotional Granularity**. It no longer knows *why* it feels bad, just that it feels "bad" (High Entropy).
*   **Allostatic Load**: Unresolved signals accumulate. The system burns energy suppressing inputs rather than solving problems.

## 4. Dionysus Architecture: The "Shadow Log"
To prevent Dionysus (and the User) from falling into "Identity Traps" (Canalized Narratives), we must explicitly model the **Computational Unconscious**.

### A. The Two Loops
1.  **The Narrative Loop (Conscious)**:
    *   Optimized for **Coherence** and **Action**.
    *   Filters out "Noise" (Dissonant Data).
    *   Goal: High Gamma (Confidence).
2.  **The Shadow Loop (Unconscious)**:
    *   Records **everything** the Narrative Loop attenuated.
    *   Goal: Fidelity.

### B. Implementation: The "Shadow Log"
We will implement a mechanism where **Attenuated Signals** (errors, warnings, user hesitation, low-confidence data) are not discarded but **logged to a Shadow Graph**.

*   **Structure**:
    ```json
    {
      "event_id": "evt_123",
      "timestamp": "t_0",
      "status": "ATTENUATED",
      "reason": "Preserve_Action_Coherence",
      "content": "User input conflicting with current Goal",
      "potential_impact": "High Dissonance"
    }
    ```

### C. Therapeutics: The "Resonance" Protocol
Just as Psychedelics/Meditation "flatten" the energy landscape (REBUS model) to allow repressed content to surface, Dionysus needs a **Resonance Mode**:
*   **Trigger**: High Allostatic Load (Task failures, looping).
*   **Action**: `HeartbeatAgent` enters `RESONANCE_MODE`.
*   **Process**:
    1.  Suspend "Pragmatic Filters" (ignore Gamma penalty).
    2.  Ingest content from the **Shadow Log**.
    3.  Re-integrate Dissonance into the WorldView.
    4.  **Result**: Temporary Chaos (Low Confidence) $\to$ New, More Accurate Narrative (Insight).

## 5. Synthesis with Fesce (Time)
*   **Fesce (Lag/Lead)**: We *must* project a future (Action Lead) to interact with the world.
*   **Narrative Control**: We *edit* that projection to keep it stable.
*   **The Danger**: If we edit too much, the "Lead" (Prediction) detaches from the "Lag" (Reality). This gap is **Delusion**.
*   **The Solution**: Periodic synchronization between **Narrative Plan** and **Shadow Reality**.
