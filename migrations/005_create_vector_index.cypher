// Migration 005: Create Vector Index for Semantic Search
// Feature: 003-semantic-search
// Created: 2025-12-15

// Create vector index on Memory.embedding for cosine similarity search
// Requires Neo4j 5.x with vector index support
// Embedding dimensions: 768 (nomic-embed-text)

CREATE VECTOR INDEX memory_embedding_index IF NOT EXISTS
FOR (m:Memory) ON (m.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
};
