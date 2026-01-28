# Synergy Plan: The Integrated Mind
**Feature:** 069-hexis-subconscious-integration
**Status:** Architecture Design

## The Vision
We are not just "installing" Letta or Hexis. We are absorbing their *patterns* into Dionysus's superior native architecture. 
- **Letta** provides the **Interface** (Structured Memory Blocks).
- **Hexis** provides the **Motivation** (Drives/Needs).
- **Dionysus** provides the **Memory** (Graphiti/Nemori/MemEvolve).

## The Core Concept: "Living Context"
Instead of static text strings (Letta's default), our Memory Blocks are **Dynamic Viewports** into the underlying Knowledge Graph.
The `DreamService` acts as the **renderer**, converting raw Graph data into structured "Guidance" for the agent.

### 1. The Ontology Fusion
We combine the best of all three:

| Concept | Source | Dionysus Native Implementation |
| :--- | :--- | :--- |
| **Deep Persistence** | Dionysus | `Graphiti` (Nodes/Edges with `valid_at`) |
| **Identity** | Cognee | `identity_utils.py` (Deterministic UUID5) |
| **Narrative** | Nemori | `DevelopmentEpisode` (The River) |
| **Motivation** | Hexis | `DriveState` (Survival, Curiosity, Rest) |
| **Presentation** | Letta | `MemoryBlock` (Guidance, Context, Pending) |

### 2. The "Dream" Cycle (Hydration Engine)
The `DreamService` is the heartbeat of this integration. It runs offline (or on demand) to "hydrate" the blocks.

**The Workflow:**
1.  **Observe:** Read recent `TrajectoryData` (MemEvolve audit logs).
2.  **Feel:** Decay/Boost `DriveStates` (Hexis).
3.  **Dream (Maintenance):**
    *   **Cluster:** Update `Neighborhood` centroids.
    *   **Prune:** Archive low-confidence nodes.
4.  **Render (Guidance):**
    *   **`core_directives`**: Static system prompt.
    *   **`project_context`**: Query Graphiti for `(:Project {active: true})`.
    *   **`pending_items`**: Query Graphiti for `(:Task {status: 'open'})`.
    *   **`guidance`**: Synthesized advice based on **Starved Drives** + **Stuck Patterns**.

### 3. The Interface (SuperMemory)
The client (Claude/Cursor) requests `fetch_guidance.py`.
- It receives the **Rendered Blocks** (Markdown).
- It injects them into `active_context.md`.
- **Result:** The agent "wakes up" with deep context, specific goals, and emotional attunement, without carrying the heavy load of querying the DB itself.

## Implementation Steps
1.  **Standardize Blocks:** Initialize `SubconsciousState` with the standard Letta block keys (`core_directives`, `project_context`, etc.).
2.  **Dynamic Hydration:** Update `DreamService.generate_guidance()` to fill these blocks intelligently.
### 4. The Powerhouse Synergy (Ultrathink)
**Hexis** stores beliefs in tables. **Dionysus** stores them in Time.

| Feature | Hexis (Static) | Dionysus (Temporal Graph) |
| :--- | :--- | :--- |
| **Worldview** | `SELECT * FROM worldview` | `MATCH (i:Identity)-[:BELIEVES]->(b:Belief) WHERE b.valid_at = NOW` |
| **Evolution** | Overwrites old beliefs | Maintains history: `(:Belief {valid_to: 2025})` |
| **Goals** | `status='completed'` | `(:Goal)-[:EVOLVED_INTO]->(:Goal)` |
| **Spontaneous** | Random SQL `ORDER BY RANDOM()` | **Graph Walk**: Weighted traversal of semantic adjacency |

**Graphiti Implementation:**
- `Worldview` items become nodes with the label `(:Worldview)`.
- `Goals` become nodes with `(:Goal)`.
- **Spontaneous Recall** uses Graphiti's `search()` with `temporal_weight=0.2` (low recency bias) to find "deep cuts".

