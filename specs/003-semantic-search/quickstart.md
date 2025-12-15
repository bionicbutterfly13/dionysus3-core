# Semantic Search Quickstart

Get up and running with semantic memory search in 5 minutes.

## Prerequisites

1. **Ollama running** with nomic-embed-text model:
   ```bash
   ollama pull nomic-embed-text
   ollama serve  # If not already running
   ```

2. **Neo4j database** with vector index:
   ```bash
   # Run the migration
   python -m api.migrations.run_migration migrations/005_create_vector_index.cypher
   ```

3. **Memories with embeddings** stored in Neo4j

## Quick Test

### Via REST API

```bash
# Health check
curl http://localhost:8000/api/memory/semantic-search/health

# Basic search
curl -X POST http://localhost:8000/api/memory/semantic-search \
  -H "Content-Type: application/json" \
  -d '{"query": "rate limiting"}'
```

### Via Python

```python
from api.services.vector_search import get_vector_search_service

search = get_vector_search_service()

# Basic search
response = await search.semantic_search(
    query="How did we implement rate limiting?"
)

for result in response.results:
    print(f"[{result.similarity_score:.0%}] {result.content[:100]}...")
```

### Via MCP Tool (Claude)

```
Use semantic_recall with:
- query: "rate limiting implementation"
- top_k: 5
```

## Common Use Cases

### 1. Find Related Context

```python
# "What do we know about authentication?"
response = await search.semantic_search(
    query="authentication and user login",
    top_k=10
)
```

### 2. Project-Specific Search

```python
from api.services.vector_search import SearchFilters

filters = SearchFilters(project_id="dionysus-core")
response = await search.semantic_search(
    query="API design decisions",
    filters=filters
)
```

### 3. Session Recall

```python
filters = SearchFilters(session_id="sess-abc123")
response = await search.semantic_search(
    query="what did we discuss",
    filters=filters
)
```

### 4. Hybrid Search (Keyword + Semantic)

```python
# Good for known terms + semantic expansion
response = await search.hybrid_search(
    query="token bucket rate limit",
    keyword_weight=0.4  # 40% keyword, 60% semantic
)
```

### 5. Find Similar Memories

```python
# Find memories similar to an existing one
similar = await search.find_similar_memories(
    memory_id="mem-001",
    top_k=5
)
```

## Tuning Parameters

| Parameter | Default | Range | When to Adjust |
|-----------|---------|-------|----------------|
| `threshold` | 0.7 | 0.0-1.0 | Lower for broader results, higher for precision |
| `top_k` | 10 | 1-100 | More results = more context but slower |
| `keyword_weight` | 0.3 | 0.0-1.0 | Higher for exact term matching |

## Troubleshooting

### "Embedding service unavailable"

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify model is installed
ollama list | grep nomic-embed-text
```

### "Vector index not found"

```bash
# Run the migration
cypher-shell -u neo4j -p <password> -f migrations/005_create_vector_index.cypher

# Verify index exists
SHOW INDEXES WHERE name = 'memory_embedding_index'
```

### "No results found"

- Lower the threshold (try 0.5)
- Check if memories have embeddings (`m.embedding IS NOT NULL`)
- Verify project/session filters are correct

## Next Steps

- [Full API Documentation](../../docs/api-search.md)
- [Feature Specification](./spec.md)
- [Integration Tests](../../tests/integration/test_semantic_search.py)
