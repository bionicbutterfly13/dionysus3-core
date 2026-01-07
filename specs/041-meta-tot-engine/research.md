# Research Notes: Meta-ToT Engine Integration

## Decision: Port D2 Meta-ToT structure as the baseline
**Rationale**: The D2 implementation includes the required features (active inference currency, CPA domains, MCTS/POMCP, basin modulation). It maps cleanly to D3's cognition/basin architecture with minimal external dependencies.
**Alternatives considered**: Rebuilding from scratch or using third-party Meta-ToT repo. Both would require reintroducing core Dionysus-specific coupling and would lose D2 feature parity.

## Decision: Use D3 LLM service for candidate generation with deterministic fallback
**Rationale**: D3 already has `chat_completion` with OpenAI/Ollama fallback. A deterministic fallback keeps Meta-ToT functional when credentials are missing.
**Alternatives considered**: Hard dependency on external LLM calls (rejected due to operational fragility).

## Decision: Trace storage via Neo4j with in-process fallback
**Rationale**: D3 already stores execution traces and autobiographical memory in Neo4j. Persisting Meta-ToT traces aligns with queryable history requirements. A fallback keeps local runs safe if Neo4j is unavailable.
**Alternatives considered**: Local file persistence only (rejected due to queryability needs).

## Decision: Thresholded activation based on complexity + uncertainty
**Rationale**: Prevents unnecessary compute for simple tasks while enabling deeper reasoning for complex planning and strategy creation.
**Alternatives considered**: Always-on Meta-ToT (rejected for performance cost), manual-only activation (rejected for consistency).

## Decision: Expose Meta-ToT via smolagents tool + optional MCP tool
**Rationale**: Tool exposure satisfies agent workflows and allows centralized orchestration. MCP tooling keeps reasoning services accessible to other agents.
**Alternatives considered**: API-only access (rejected as less direct for agent workflows).
