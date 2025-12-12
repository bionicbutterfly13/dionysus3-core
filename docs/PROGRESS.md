# Progress Log

## 2025-12-09 (feature/codex-mcp-integration)
- Swapped LLM provider to OpenAI-first; default model now `gpt-5-mini` (aliased by OpenAI, currently `gpt-5-mini-2025-08-07`). Anthropic only if explicitly configured.
- Made MCP embeddings pluggable with Ollama default; added embedding dimension normalization and new env vars (EMBEDDINGS_PROVIDER, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, OPENAI_EMBED_MODEL, EMBEDDING_DIM).
- Added AGE feature guard via `AGE_AVAILABLE` env; consciousness/basin/thoughtseed tools short-circuit when AGE is unavailable (for Supabase/Render).
- Wired `/ias/recall` to vector search via DB function `search_similar_memories`, with automatic fallback to Postgres FTS (`search_memories_text`) if vector path fails.
- Added `.env.local` entries for DATABASE_URL, OpenAI, embeddings, and AGE toggle.
- Production note (from Claude): EMBEDDINGS_PROVIDER=openai, OPENAI_EMBED_MODEL=text-embedding-3-small, EMBEDDING_DIM=1536. Schema currently uses vector(768) and needs widening to match if we adopt this in production.
- Updated MCP OpenAI embedding path to pass `dimensions=EMBEDDING_DIM` (default 768) so we stay compatible with current schema.
- Resolved MCP import shadow by explicitly importing MCP SDK modules via adjusted sys.path to avoid local package name collision.

Next actions
- Replace recall fallback with MCP `search_memories`/`fast_recall` integration.
- Resolve MCP import shadow (`from mcp.server import Server` vs package name) so MCP server starts cleanly.
- Add AGE guards to remaining AGE-dependent paths if new features are exposed, and ensure Supabase uses `schema-supabase.sql`.
- Update compose to run API+MCP with Postgres/AGE+Ollama; provide Render profile without AGE.
