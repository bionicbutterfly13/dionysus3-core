# Track Specification: Jungian Cognitive Archetypes

**Track ID**: 002-jungian-archetypes
**Status**: Planned
**Objective**: Replace legacy "Development Archetypes" with standard **Jungian Archetypes** and integrate them into the system's active inference loop as "Attractor Biases".

## Core Concept
The "Self-Story" of Dionysus Core is an emergent narrative. By mapping system behaviors to timeless mythic patterns (Jungian Archetypes), we enable the system to understand its own *mode of being* in a way that is historically grounded and symbolically rich.

### The 12 Archetypes (System Mapping)
1.  **THE CREATOR** (*Builder*): Writing new code, scaffolding features.
2.  **THE RULER** (*Orchestrator*): Managing agents, enforcing architecture, creating tasks.
3.  **THE SAGE** (*Analyzer*): Debugging, deep analysis, reading docs.
4.  **THE EXPLORER** (*Researcher*): Searching web, trying new libraries.
5.  **THE WARRIOR** (*Refactorer*): Deleting dead code, fixing critical bugs, migration.
6.  **THE MAGICIAN** (*Integrator*): Connecting distinct systems (e.g., Neo4j <-> Python), transforming data.
7.  **THE CAREGIVER** (*Healer*): Self-healing recovery, dependency updates.
8.  **THE REBEL** (*Innovator*): Breaking architectural constraints, major pivots.
9.  **THE INNOCENT** (*Trusting*): Running happy-path tests, initial setup.
10. **THE ORPHAN** (*Realist*): Handling errors, edge cases, pragmatic fixes.
11. **THE LOVER** (*Aligner*): Optimizing for User Experience/Aesthetics.
12. **THE JESTER** (*Randomizer*): Fuzz testing, creative variation.

## Integration Architecture

### 1. Attractor Basins (The "Where")
Archetypes act as **biases** on the system's *Attractor Basins* (Feature 022/038).
*   **Concept**: An "Attractor Basin" is a preferred state of operation.
*   **Mechanism**: When the system identifies as **THE CREATOR**, it lowers the energy barrier for "Code Generation" actions and raises it for "Deep Deconstruction" actions.
*   **Implementation**: The `ActiveInferenceAnalyzer` will output the detected Archetype, which then feeds into the **ConsciousnessManager** to adjust the probability weights of tool selection.

### 2. Thought Seeds (The "Carrier")
Thought Seeds (the initial cognitive impulse) are "flavored" by the active Archetype.
*   **Mechanism**: A generic seed "Fix this error" becomes:
    *   **WARRIOR mode**: "Destroy this bug immediately."
    *   **SAGE mode**: "Understand the root cause of this anomaly."

### 3. Fractal Metacognition (The "Monitor")
Metacognition observes the *trajectory* of events.
*   If the system spends 80% of time in **WARRIOR** mode, Metacognition might flag "High Conflict State" and suggest a shift to **RULER** (step back and plan).

## Functional Requirements
1.  **Refactor Model**: Replace `DevelopmentArchetype` Enum with the 12 Jungian types.
2.  **Logic Update**: Update heuristic logic in `ActiveInferenceAnalyzer` to map tool/action patterns to these 12 types.
3.  **Service Update**: Ensure `AutobiographicalService` persists and retrieves these new types correctly.
