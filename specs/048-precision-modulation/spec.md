# Feature Spec: Dynamic Precision Modulation (Feature 048)

**Created**: 2025-12-31
**Status**: Draft
**Branch**: 048-precision-modulation

## 1. Overview
Implement the "Mental Zoom Lens" as defined in the *Metacognitive Particles* paper. Precision represents the inverse variance of the agent's internal world model. By dynamically modulating precision based on prediction error (Surprise), the system can switch between **High-Curiosity (Zoom Out)** and **High-Focus (Zoom In)** modes.

## 2. Goals
- **Surprise-Driven Tuning**: Automatically lower precision when Surprise is high (to encourage exploration) and raise it when Surprise is low (to favor execution).
- **Precision-Weighted EFE**: Update the `EFEEngine` to weight Uncertainty vs. Goal Divergence based on the current precision state.
- **Metacognitive Control**: Provide a tool for the `MetacognitionAgent` to manually set precision targets for sub-agents.
- **Persistence**: Store the current precision state in the Knowledge Graph.

## 3. Implementation Details

### 3.1 Precision Logic (`api/services/metaplasticity_service.py`)
- **`update_precision(agent_id, surprise_score)`**:
    - *Formula*: `new_precision = current_precision * (1.0 - (surprise_score - 0.5) * alpha)`
    - Clamp precision between [0.1, 5.0].

### 3.2 EFE Regularization (`api/services/efe_engine.py`)
- **`calculate_precision_weighted_efe(...)`**:
    - *Weighted Formula*: `EFE = (1/Precision) * Uncertainty + (Precision) * GoalDivergence`.

### 3.3 Metacognitive Tool (`api/agents/tools/cognitive_tools.py`)
- **`set_mental_focus(precision_level)`**: Allows an agent to manually override its precision state.

## 4. Dependencies
- `api.services.efe_engine`
- `api.agents.consciousness_manager` (for the OODA surprise hook)

## 5. Testing Strategy
- **Unit Tests**: Verify that as Surprise increases, Precision decreases (Zoom Out).
- **Scenario Test**: Mock a "confusing" context and verify the agent's EFE selection shifts toward epistemic (exploratory) actions.

## 6. Success Criteria
- Each managed agent maintains an independent precision state.
- Precision values are updated at the end of every OODA cycle.
- The `MetacognitionAgent` can successfully "Zoom In" or "Zoom Out" sub-agents.