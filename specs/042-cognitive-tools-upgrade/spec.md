# Feature Spec: Port Research-Validated Cognitive Tools (Feature 042)

**Created**: 2025-12-31  
**Status**: Draft  
**Branch**: 042-cognitive-tools-upgrade

## 1. Overview
Port the research-validated cognitive tools from Dionysus 2.0 (`backend/services/enhanced_daedalus/cognitive_tools_implementation.py`) to Dionysus 3.0. These tools utilize specific prompt engineering techniques proven to improve reasoning accuracy by up to 62.5% (according to D2 documentation/research).

## 2. Goals
- Implement `UnderstandQuestionTool`: Decomposes complex problems.
- Implement `RecallRelatedTool`: Uses analogical reasoning.
- Implement `ExamineAnswerTool`: self-correction and verification.
- Implement `BacktrackingTool`: Error recovery and alternative path exploration.
- Integrate these tools into the `ConsciousnessManager` for agent use.
- Expose these tools via MCP for external use.

## 3. Implementation Details

### 3.1 Tool Implementation (`api/agents/tools/cognitive_tools.py`)
Refactor the existing `cognitive_tools.py` to include the following classes, inheriting from `smolagents.Tool`:

*   **`UnderstandQuestionTool`**:
    *   **Input**: `question` (str), `context` (str, optional).
    *   **Output**: Structured decomposition of the problem.
    *   **Logic**: Uses the specific "You are a mathematical reasoning assistant..." prompt from D2.

*   **`RecallRelatedTool`**:
    *   **Input**: `question` (str), `context` (str, optional).
    *   **Output**: Analogous examples.
    *   **Logic**: Uses the "You are a retrieval assistant..." prompt from D2.

*   **`ExamineAnswerTool`**:
    *   **Input**: `question` (str), `current_reasoning` (str), `context` (str, optional).
    *   **Output**: Critique and verification of the reasoning.
    *   **Logic**: Uses the "You are an expert mathematical assistant..." prompt from D2.

*   **`BacktrackingTool`**:
    *   **Input**: `question` (str), `current_reasoning` (str), `context` (str, optional).
    *   **Output**: Alternative strategy.
    *   **Logic**: Uses the "You are a careful problem-solving assistant..." prompt from D2.

### 3.2 Agent Integration (`api/agents/consciousness_manager.py`)
*   Register the new tool instances in `_initialize_agents`.
*   Ensure the `ReasoningAgent` has access to these tools.

### 3.3 MCP Integration (`dionysus_mcp/tools/cognitive.py` & `server.py`)
*   Create `dionysus_mcp/tools/cognitive.py` to wrap the internal tool logic for MCP.
*   Register tools in `dionysus_mcp/server.py`:
    *   `cognitive_understand`
    *   `cognitive_recall`
    *   `cognitive_examine`
    *   `cognitive_backtrack`

## 4. Dependencies
*   `smolagents` (for `Tool` base class).
*   `api.services.llm_service` (for executing the prompts).

## 5. Testing Strategy
*   **Unit Tests**: `tests/unit/test_cognitive_tools.py` verifying prompt generation and mock LLM responses.
*   **Integration Tests**: Verify tools can be called via `ConsciousnessManager` and MCP.

## 6. Success Criteria
*   All 4 tools implemented with D2 prompts preserved.
*   Tools accessible via `ConsciousnessManager`.
*   Tools accessible via MCP.
*   Unit tests passing.

## 7. Non-Functional Requirements
*   **Prompt Fidelity**: The prompts must match the D2 implementation exactly (or as close as possible) to preserve the "research-validated" benefits.
*   **Performance**: Tool execution should introduce minimal overhead beyond the LLM call itself.