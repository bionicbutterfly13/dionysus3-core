# Feature Spec: Active Inference Planning & Policy Generation (Feature 046)

**Created**: 2025-12-31
**Status**: Draft
**Branch**: 046-active-inference-planning

## 1. Overview
Extend the Dionysus 3.0 Active Inference engine from single-step scoring to **Multi-Step Policy Planning**. This allows agents to evaluate sequences of tools and internal actions (Policies) by calculating their cumulative **Expected Free Energy (EFE)** across a lookahead horizon.

Based on principles from Dionysus 2.0 `ActiveInferenceService` but optimized for cognitive action selection in a multi-agent system.

## 2. Goals
- **Policy Generation**: Generate candidate sequences of actions (e.g., [Recall, Understand, Reason, Examine]).
- **Outcome Simulation**: Predict the likely state of context after each step in a policy.
- **Path EFE Calculation**: Sum the EFE (Uncertainty + Goal Divergence) across all steps in a path.
- **Optimal Policy Selection**: Pick the sequence that minimizes total Path EFE.
- **Integration**: Provide a tool for the `ReasoningAgent` to explicitly plan its next N steps.

## 3. Implementation Details

### 3.1 Policy Model (`api/models/policy.py`)
- `ActionStep`: A single action (tool + params).
- `Policy`: A sequence of `ActionStep`s.
- `PolicyEvaluation`: Contains the `path_efe`, `confidence`, and `simulated_trace`.

### 3.2 Action Planner Service (`api/services/action_planner_service.py`)
- **`generate_policies(task, context)`**: Uses LLM to propose 3-5 logical action sequences.
- **`evaluate_policy(policy, context, goal)`**: 
    - Recursively simulates outcomes.
    - Uses `EFEEngine` to score each simulated step.
- **`select_best_policy(task, context, goal)`**: Orchestrates the above.

### 3.3 Integration into OODA
Add an `active_planner` tool to the `ReasoningAgent` so it can say "I will plan my approach first" and get a ranked list of strategic paths.

## 4. Dependencies
- `api.services.efe_engine` (for scoring).
- `api.services.llm_service` (for simulation).
- `smolagents` (for tool definitions).

## 5. Testing Strategy
- **Unit Tests**: Verify that Path EFE correctly sums step EFEs.
- **Scenario Tests**: Provide a "confusing" task and verify that the planner selects a policy starting with `UnderstandQuestion` over a direct `Reason`.

## 6. Success Criteria
- System generates multi-step plans with explicit EFE scores.
- Plans starting with epistemic tools (Recall/Understand) are favored when uncertainty is high.
- The `ReasoningAgent` can call the `active_planner` tool successfully.