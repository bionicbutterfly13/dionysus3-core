# Research: Agent Bootstrap Recall

## Technical Decisions

### 1. Neo4j-Only Retrieval Strategy
- **Decision**: All recall is performed against Neo4j. Semantic search uses the `VectorSearchService` (which executes via n8n webhooks to the Neo4j vector index). Temporal search uses `GraphitiService` (Neo4j temporal knowledge graph).
- **Rationale**: PostgreSQL has been fully removed. Neo4j provides both the vector storage and the temporal relationships required for high-fidelity grounding.
- **Alternatives Considered**: Direct Neo4j Bolt connection (rejected; mandated webhook-only architecture for general services).

### 2. Hybrid Search Implementation
- **Decision**: Sequentially query `VectorSearchService` for top-5 semantic matches and `GraphitiService` for the last 5 successful `trajectory` episodes.
- **Rationale**: Vector search is optimized for similarity, while Graphiti's temporal engine is precise for sequential history.

### 3. Token Management & Summarization
- **Decision**: Use `tiktoken` for accurate token counting. If >2000 tokens, pass the raw context to a "Distiller" prompt using Claude HAIKU (via `api.services.claude`).
- **Rationale**: Claude HAIKU is fast and consistent with existing system-wide summarization patterns.

### 4. Integration Point
- **Decision**: Inject into `ConsciousnessManager.run_ooda_cycle` at the beginning of the method.
- **Rationale**: Single entry point for all agent hierarchies, ensuring universal coverage.

## Best Practices

### smolagents & Context
- Keep the `initial_context` dictionary flat where possible.
- Use Markdown headers (`## Past Context`) to help agents distinguish between new instructions and historical grounding.

### Error Handling
- Wrap the entire bootstrap call in a `try/except` with a 2s timeout. If it fails, log the error and proceed with an empty context rather than blocking the agent.