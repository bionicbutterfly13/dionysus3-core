# Feature Spec: Marketing Strategist Agent (Feature 050)

**Created**: 2025-12-31
**Status**: Draft
**Branch**: 050-marketing-strategist

## 1. Overview
Implement a specialized `smolagents.CodeAgent` designed specifically for the "Inner Architect" marketing pillar. This agent is grounded in the "Analytical Empath" audience research and the "21 Forbidden Email Frameworks" to generate high-conversion, authentic content.

## 2. Goals
- **Audience Grounding**: Permanently attach the "Analytical Empath" motivational map and "Crack" research to this agent's identity.
- **Framework Mastery**: Provide tools to retrieve and apply specific conversion templates (e.g., "Contrarian Truth").
- **Collaboration**: Register this agent as a "Managed Agent" under the `ConsciousnessManager`.
- **Outcome Tracking**: Automatically record generated content and its strategic rationale in the Knowledge Graph.

## 3. Implementation Details

### 3.1 Agent Definition (`api/agents/marketing_strategist.py`)
- Define `MarketingStrategistAgent`:
    - System Prompt: "You are a world-class Direct Response Architect specializing in the Analytical Empath avatar."
    - Tools: `recall_related`, `understand_question`, and a new `get_marketing_framework` tool.

### 3.2 Framework Service (`api/services/marketing_framework_service.py`)
- **`get_framework(template_id)`**: Retrieves specific templates from the `/assets` or research directories.

### 3.3 Integration
- Register `ManagedMarketingStrategist` in `api/agents/managed/marketing.py`.
- Inject into `ConsciousnessManager.orchestrator.managed_agents`.

## 4. Dependencies
- `api.services.llm_service`
- `api.services.graphiti_service`
- `api.agents.managed`

## 5. Testing Strategy
- **Scenario Test**: Ask the `ConsciousnessManager` to "Draft a New Year email for Analytical Empaths using the Contrarian Truth framework" and verify that it delegates to the `marketing_strategist`.

## 6. Success Criteria
- Agent successfully retrieves avatar insights from memory.
- Agent applies the correct marketing framework to its output.
- All drafts are stored in the `AutobiographicalService`.