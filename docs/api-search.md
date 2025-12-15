# Semantic Search API Documentation

**Feature**: 003-semantic-search
**Version**: 1.0.0
**Last Updated**: 2025-12-15

## Overview

The Semantic Search API provides vector similarity search for memories using Neo4j + embeddings from Ollama. This enables intelligent recall based on semantic meaning rather than keyword matching.

Key capabilities:
- Vector similarity search using 768-dimensional embeddings
- Hybrid search combining keyword and semantic matching
- Filtering by project, session, date range, and memory type
- MCP tool for context injection into Claude conversations

## Architecture

```
Query Text → EmbeddingService → Ollama (nomic-embed-text)
                                     ↓
                               768-dim embedding
                                     ↓
                              Neo4j Vector Index
                                     ↓
                              Ranked Results
```

---

## REST API Endpoints

### Semantic Search

#### POST /api/memory/semantic-search

Search memories using vector similarity.

**Request:**
```json
{
  "query": "How did we implement rate limiting?",
  "top_k": 10,
  "threshold": 0.7,
  "filters": {
    "project_id": "dionysus-core",
    "session_id": "sess-123",
    "memory_types": ["semantic", "procedural"]
  }
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Natural language search query |
| `top_k` | int | No | 10 | Maximum results to return |
| `threshold` | float | No | 0.7 | Minimum similarity score (0.0-1.0) |
| `filters.project_id` | string | No | - | Filter by project |
| `filters.session_id` | string | No | - | Filter by session |
| `filters.memory_types` | array | No | - | Filter by types: episodic, semantic, procedural, strategic |
| `filters.from_date` | datetime | No | - | Filter memories created after |
| `filters.to_date` | datetime | No | - | Filter memories created before |

**Response:**
```json
{
  "query": "How did we implement rate limiting?",
  "results": [
    {
      "id": "mem-001",
      "content": "Implemented token bucket algorithm for request throttling with 100 req/min limit",
      "memory_type": "procedural",
      "importance": 0.8,
      "similarity_score": 0.92,
      "session_id": "sess-abc",
      "project_id": "dionysus-core",
      "created_at": "2025-12-14T10:30:00Z"
    },
    {
      "id": "mem-002",
      "content": "Rate limiting prevents API abuse by rejecting requests over threshold",
      "memory_type": "semantic",
      "importance": 0.7,
      "similarity_score": 0.85,
      "session_id": "sess-def",
      "project_id": "dionysus-core",
      "created_at": "2025-12-13T15:00:00Z"
    }
  ],
  "count": 2,
  "total_time_ms": 45
}
```

#### GET /api/memory/semantic-search/health

Check semantic search service health.

**Response:**
```json
{
  "status": "healthy",
  "embedding_service": {
    "available": true,
    "model": "nomic-embed-text",
    "dimensions": 768
  },
  "vector_index": {
    "available": true,
    "index_name": "memory_embedding_index"
  }
}
```

### Hybrid Search

#### POST /api/memory/hybrid-search

Search using combined keyword and semantic matching.

**Request:**
```json
{
  "query": "rate limiting token bucket",
  "top_k": 10,
  "threshold": 0.5,
  "keyword_weight": 0.3,
  "filters": {
    "project_id": "dionysus-core"
  }
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (used for both keyword and semantic) |
| `top_k` | int | No | 10 | Maximum results to return |
| `threshold` | float | No | 0.5 | Minimum combined score |
| `keyword_weight` | float | No | 0.3 | Weight for keyword matching (0.0=pure semantic, 1.0=pure keyword) |
| `filters` | object | No | - | Same filters as semantic search |

**Scoring Formula:**
```
combined_score = (semantic_score * (1.0 - keyword_weight)) + (keyword_score * keyword_weight)
```

**Response:**
```json
{
  "query": "rate limiting token bucket",
  "results": [
    {
      "id": "mem-001",
      "content": "Implemented token bucket algorithm for rate limiting",
      "similarity_score": 0.95,
      "keyword_match": true,
      "combined_score": 0.97
    }
  ],
  "count": 1,
  "total_time_ms": 52
}
```

### Find Similar

#### POST /api/memory/find-similar

Find memories similar to an existing memory.

**Request:**
```json
{
  "memory_id": "mem-001",
  "top_k": 5,
  "threshold": 0.7,
  "exclude_self": true
}
```

**Response:**
```json
{
  "source_memory_id": "mem-001",
  "similar_memories": [...],
  "count": 4
}
```

---

## MCP Tools

### semantic_recall

Recall semantically relevant memories for context injection.

```python
# MCP call
result = await semantic_recall(
    query="How did we implement rate limiting?",
    top_k=5,
    threshold=0.7,
    project_id="dionysus-core",
    session_id=None,
    memory_types=["procedural", "semantic"],
    weight_by_importance=True
)
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Natural language query |
| `top_k` | int | No | 5 | Maximum memories to return |
| `threshold` | float | No | 0.7 | Minimum similarity score (0.0-1.0) |
| `project_id` | string | No | - | Filter by project |
| `session_id` | string | No | - | Filter by session |
| `memory_types` | array | No | - | Filter by types |
| `weight_by_importance` | bool | No | True | Boost results by importance score |

**Returns:** Formatted string for context injection

**Example Output:**
```markdown
## Relevant Memories (2 found)
Query: "How did we implement rate limiting?"

### Memory 1 (relevance: 92%)
**Type**: procedural | **Importance**: 80%
**Project**: dionysus-core
**Session**: sess-abc...

Implemented token bucket algorithm for request throttling with 100 req/min limit

### Memory 2 (relevance: 85%)
**Type**: semantic | **Importance**: 70%
**Project**: dionysus-core

Rate limiting prevents API abuse by rejecting requests over threshold

---
*Retrieved in 45ms*
```

**Use Cases:**
- Find relevant past context for current task
- Recall how something was done before
- Get background information from previous sessions
- Find related decisions or implementations

---

## Neo4j Vector Index

### Index Schema

```cypher
CREATE VECTOR INDEX memory_embedding_index IF NOT EXISTS
FOR (m:Memory) ON (m.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
};
```

### Vector Search Query

```cypher
CALL db.index.vector.queryNodes(
  'memory_embedding_index',
  $top_k,
  $query_embedding
) YIELD node, score
WHERE score >= $threshold
RETURN node, score
ORDER BY score DESC
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "EMBEDDING_FAILED",
  "details": {}
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `EMBEDDING_FAILED` | Ollama embedding generation failed |
| `VECTOR_INDEX_UNAVAILABLE` | Neo4j vector index not available |
| `INVALID_QUERY` | Query string is empty or invalid |
| `INVALID_THRESHOLD` | Threshold must be between 0.0 and 1.0 |
| `INVALID_TOP_K` | top_k must be positive integer |
| `SEARCH_TIMEOUT` | Search operation timed out |

---

## Configuration

### Environment Variables

```bash
# Ollama (embedding generation)
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Neo4j (vector index)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>

# Search defaults
SEMANTIC_SEARCH_TOP_K=10
SEMANTIC_SEARCH_THRESHOLD=0.7
EMBEDDING_DIMENSIONS=768
```

---

## Usage Examples

### Python SDK

```python
from api.services.vector_search import VectorSearchService, SearchFilters

search = VectorSearchService()

# Basic semantic search
response = await search.semantic_search(
    query="rate limiting implementation",
    top_k=5,
    threshold=0.7
)

# Filtered search
filters = SearchFilters(
    project_id="dionysus-core",
    memory_types=["procedural", "semantic"]
)
response = await search.semantic_search(
    query="authentication flow",
    filters=filters
)

# Hybrid search
response = await search.hybrid_search(
    query="token bucket algorithm",
    keyword_weight=0.4  # 40% keyword, 60% semantic
)

# Find similar memories
similar = await search.find_similar_memories(
    memory_id="mem-001",
    top_k=5
)
```

### cURL

```bash
# Semantic search
curl -X POST http://localhost:8000/api/memory/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "rate limiting implementation",
    "top_k": 5,
    "threshold": 0.7
  }'

# Hybrid search
curl -X POST http://localhost:8000/api/memory/hybrid-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "token bucket",
    "keyword_weight": 0.3
  }'

# Health check
curl http://localhost:8000/api/memory/semantic-search/health
```

### MCP Tool (Claude)

```
Use the semantic_recall tool:
- query: "How did we implement rate limiting?"
- top_k: 5
- project_id: "dionysus-core"
```

---

## Performance Considerations

### Embedding Generation
- ~50-100ms per query via Ollama
- Batch embedding available for multiple queries
- Model: nomic-embed-text (768 dimensions)

### Vector Search
- Neo4j HNSW index for approximate nearest neighbor
- O(log n) search complexity
- Recommended: top_k <= 50 for optimal performance

### Caching
- Consider caching embeddings for frequent queries
- Results are not cached by default

---

## Migration

### From Keyword Search

The semantic search complements existing keyword search:

| Aspect | Keyword Search | Semantic Search |
|--------|----------------|-----------------|
| Matching | Exact/fuzzy text | Meaning similarity |
| Use case | Known terms | Conceptual queries |
| Speed | Faster | Slightly slower |
| Results | Precise matches | Related concepts |

**Recommendation:** Use hybrid search with `keyword_weight=0.3` for best results.
