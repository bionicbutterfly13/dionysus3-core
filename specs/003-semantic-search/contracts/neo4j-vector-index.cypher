// Feature 003: Semantic Search
// Neo4j Vector Index Schema
// Created: 2025-12-15

// =============================================================================
// Vector Index for Memory Embeddings
// =============================================================================

// Create vector index on Memory.embedding field
// Uses nomic-embed-text dimensions (768) with cosine similarity
CREATE VECTOR INDEX memory_embedding_index IF NOT EXISTS
FOR (m:Memory) ON (m.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
};

// =============================================================================
// Verification Queries
// =============================================================================

// Check if vector index exists
SHOW INDEXES
WHERE name = 'memory_embedding_index';

// Check index status
SHOW INDEXES
WHERE name = 'memory_embedding_index'
RETURN name, state, populationPercent;

// =============================================================================
// Example Semantic Search Query
// =============================================================================

// Replace $query_embedding with actual 768-dim vector from Ollama
// MATCH (m:Memory)
// WHERE m.project_id = $project_id
// WITH m, vector.similarity.cosine(m.embedding, $query_embedding) AS score
// WHERE score >= $threshold
// RETURN m.id, m.content, m.memory_type, m.importance, score
// ORDER BY score DESC
// LIMIT $top_k;

// =============================================================================
// Index Management
// =============================================================================

// Drop index if needed (use with caution)
// DROP INDEX memory_embedding_index IF EXISTS;

// Reindex (after schema changes)
// DROP INDEX memory_embedding_index IF EXISTS;
// CREATE VECTOR INDEX memory_embedding_index ...
