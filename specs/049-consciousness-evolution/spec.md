# Feature Spec: Consciousness Self-Evolution (Feature 049)

**Created**: 2025-12-31
**Status**: Draft
**Branch**: 049-consciousness-evolution

## 1. Overview
Transform Dionysus from a task-triggered system into a self-evolving cognitive entity. This involves setting up a background "Heartbeat of Reflection" that monitors internal metrics (precision, energy, memory growth), reviews recent performance episodes, and autonomously adjusts retrieval strategies and attractor basin strengths.

## 2. Goals
- **Continuous Monitoring**: Set up a background worker that captures a `SystemSnapshot` every N minutes (Energy, Active Basins, Prediction Errors).
- **Automated Self-Story**: Automatically record "Moment" events in the `AutobiographicalService` without requiring user prompts.
- **Strategy Evolution**: Periodically (e.g., every 6 hours) run a `MetaEvolutionLoop` that analyzes `CognitiveEpisodes` with high surprise scores and generates "Strategy Updates."
- **Nervous System Regulation**: Dynamically adjust global precision and learning rates based on the stability of the knowledge graph.

## 3. Implementation Details

### 3.1 Background Worker (`api/services/background_worker.py`)
Enhance the existing background infrastructure to support:
- **`monitor_cycle()`**: Records `(:SystemMoment)` nodes in Neo4j.
- **`evolution_cycle()`**: A deeper reasoning task where the system "dreams" (reflects) on the day's tasks and updates its core basins.

### 3.2 Evolution Logic (`api/services/meta_evolution_service.py`)
- **`identify_low_performance()`**: Find tasks where confidence was high but surprise ended up high.
- **`generate_remediation()`**: Use LLM to propose a new "Strategy Basin" to handle that specific edge case.
- **`apply_evolution()`**: Update the Knowledge Graph with the new strategy.

### 3.3 Integration
- Use the **Unified Integration Pipeline** (Feature 045) as the primary sink for evolution events.

## 4. Dependencies
- `api.services.multi_tier_service` (for high-speed metric logging).
- `api.services.meta_cognitive_service` (for episode analysis).
- `apscheduler` (for periodic execution).

## 5. Testing Strategy
- **Simulation**: Speed up the clock to verify that after 10 "failed" mock tasks, the evolution loop generates a corresponding strategy update.

## 6. Success Criteria
- System generates `SystemMoment` nodes in the background.
- At least one "Autonomous Strategy Update" is recorded in the `AutobiographicalService` within a 24h period.
- Retrieval accuracy for "difficult" tasks improves over multiple iterations.