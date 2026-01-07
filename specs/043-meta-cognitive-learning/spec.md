# Feature Spec: Meta-Cognitive Learning (Feature 043)

**Created**: 2025-12-31
**Status**: Draft
**Branch**: 043-meta-cognitive-learning

## 1. Overview
Implement an **Episodic Meta-Learning** system that allows Dionysus to learn from its own reasoning sessions. By recording "Cognitive Episodes" (Task -> Strategy -> Outcome) and retrieving them for similar future tasks, the system optimizes its tool usage, prompting strategies, and OODA execution over time.

This ports the core logic of `MetaCognitiveEpisodicLearner` from Dionysus 2.0 (`backend/services/enhanced_daedalus/meta_cognitive_integration.py`), adapted for Dionysus 3.0's Neo4j/Graphiti architecture.

## 2. Goals
- **Record Episodes**: Capture every significant OODA cycle as a `CognitiveEpisode` containing the task, context, tools used, and a success/surprise metric.
- **Episodic Retrieval**: Before starting a new task, retrieve the top-k most similar past episodes using vector search.
- **Strategy Optimization**: Inject "Lessons Learned" from past episodes into the `ReasoningAgent`'s context to guide tool selection (e.g., "Last time, `ContextExplorer` failed for this query type; try `UnderstandQuestion` first").
- **Self-Correction**: Use "Surprise" (prediction error) as a training signal to update the importance/confidence of specific strategies.

## 3. Implementation Details

### 3.1 Data Models (`api/models/meta_cognition.py`)
Define Pydantic models for:
- `CognitiveEpisode`:
    - `id`: UUID
    - `task_embedding`: Vector (for retrieval)
    - `task_description`: str
    - `strategy_used`: List[ToolCall] or Description
    - `outcome`: Success/Failure/Partial
    - `surprise_score`: float (0.0-1.0)
    - `learned_lesson`: str (Optional textual insight)

### 3.2 Service Layer (`api/services/meta_cognitive_service.py`)
Implement `MetaCognitiveLearner`:
- **`record_episode(context, decision, result)`**: Persists the episode to Neo4j.
    - *Neo4j Schema*: Nodes `(:CognitiveEpisode)`, linked to `(:TaskCluster)`.
- **`retrieve_relevant_episodes(task_query)`**: Uses Graphiti or Neo4j Vector Index to find similar past tasks.
- **`synthesize_strategy(episodes)`**: Generates a prompt injection summarizing "what worked" and "what failed" in similar contexts.

### 3.3 Integration (`api/agents/consciousness_manager.py`)
Modify `_run_ooda_cycle`:
1.  **PRE-OODA**: Call `MetaCognitiveLearner.retrieve_relevant_episodes(task)`.
2.  **INJECTION**: Add `past_lessons` to the `ReasoningAgent`'s system prompt or context.
3.  **POST-OODA**: Calculate `surprise` (confidence vs. actual outcome) and call `MetaCognitiveLearner.record_episode`.

## 4. Dependencies
- `api.services.graphiti_service`: For vector indexing/search via Neo4j.
- `smolagents`: For agent context manipulation.

## 5. Testing Strategy
- **Unit Tests**: `tests/unit/test_meta_cognition.py` mocking the persistence layer.
- **Integration Tests**: Run a sequence of similar tasks and verify that the second task references the first task's episode.

## 6. Success Criteria
- System persists episodes to Neo4j.
- System retrieves relevant episodes for semantically similar tasks.
- `ConsciousnessManager` logs show "Injecting meta-cognitive lessons" during execution.
