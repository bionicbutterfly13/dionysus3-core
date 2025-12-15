// Neo4j Schema for Remote Persistence Safety Framework
// Feature: 002-remote-persistence-safety
// Date: 2025-12-14
//
// Run this file against Neo4j to initialize the schema:
//   cat neo4j-schema.cypher | cypher-shell -u neo4j -p <password> -a bolt://72.61.78.89:7687

// ============================================================================
// CONSTRAINTS (Uniqueness)
// ============================================================================

// Memory nodes must have unique IDs
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE;

// Session nodes must have unique IDs
CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.id IS UNIQUE;

// Project nodes must have unique IDs
CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.id IS UNIQUE;

// ============================================================================
// INDEXES (Query Performance)
// ============================================================================

// Vector index for semantic similarity search
// Uses 768 dimensions to match nomic-embed-text model
CREATE VECTOR INDEX memory_embedding IF NOT EXISTS
FOR (m:Memory) ON (m.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
}};

// Full-text search on memory content and tags
CREATE FULLTEXT INDEX memory_content_fulltext IF NOT EXISTS
FOR (n:Memory) ON EACH [n.content];

// Composite index for project + type filtered queries
CREATE INDEX memory_project_type IF NOT EXISTS
FOR (m:Memory) ON (m.source_project, m.memory_type);

// Date range queries on memories
CREATE INDEX memory_created_at IF NOT EXISTS
FOR (m:Memory) ON (m.created_at);

// Session date range queries
CREATE INDEX session_dates IF NOT EXISTS
FOR (s:Session) ON (s.started_at, s.ended_at);

// Project lookup by name
CREATE INDEX project_name IF NOT EXISTS
FOR (p:Project) ON (p.name);

// Sync version for conflict detection
CREATE INDEX memory_sync_version IF NOT EXISTS
FOR (m:Memory) ON (m.sync_version);

// ============================================================================
// INITIAL DATA (Projects)
// ============================================================================

// Create known projects
MERGE (p:Project {id: 'dionysus-core'})
SET p.name = 'Dionysus Core',
    p.description = 'AGI memory system core',
    p.created_at = datetime();

MERGE (p:Project {id: 'inner-architect-companion'})
SET p.name = 'Inner Architect Companion',
    p.description = 'IAS coaching application',
    p.created_at = datetime();

MERGE (p:Project {id: 'dionysus-memory'})
SET p.name = 'Dionysus Memory',
    p.description = 'Memory persistence and consolidation',
    p.created_at = datetime();

// ============================================================================
// EXAMPLE QUERIES (For Testing)
// ============================================================================

// -- Query: Get all memories for a session
// MATCH (m:Memory)-[:BELONGS_TO]->(s:Session {id: $session_id})
// RETURN m
// ORDER BY m.created_at DESC;

// -- Query: Semantic search with vector similarity
// MATCH (m:Memory)
// WHERE m.source_project = $project_id
// CALL db.index.vector.queryNodes('memory_embedding', 10, $query_vector)
// YIELD node, score
// RETURN node.id, node.content, score
// ORDER BY score DESC;

// -- Query: Cross-project memories by date range
// MATCH (m:Memory)
// WHERE m.created_at >= datetime($start_date)
//   AND m.created_at <= datetime($end_date)
// RETURN m.source_project, count(m) as memory_count, collect(m.id) as memory_ids
// ORDER BY memory_count DESC;

// -- Query: Get session timeline with memory counts
// MATCH (s:Session)-[:PART_OF]->(p:Project {id: $project_id})
// OPTIONAL MATCH (m:Memory)-[:BELONGS_TO]->(s)
// RETURN s.id, s.started_at, s.ended_at, s.summary, count(m) as memory_count
// ORDER BY s.started_at DESC;

// -- Query: Find memories referencing another memory
// MATCH (m1:Memory)-[r:REFERENCES]->(m2:Memory {id: $memory_id})
// RETURN m1, r.context;

// ============================================================================
// MERGE OPERATIONS (Idempotent Sync)
// ============================================================================

// -- Sync a memory from local to remote (idempotent)
// MERGE (m:Memory {id: $memory_id})
// ON CREATE SET
//     m.content = $content,
//     m.memory_type = $memory_type,
//     m.importance = $importance,
//     m.embedding = $embedding,
//     m.source_project = $project_id,
//     m.session_id = $session_id,
//     m.tags = $tags,
//     m.sync_version = $sync_version,
//     m.created_at = datetime($created_at),
//     m.updated_at = datetime($updated_at)
// ON MATCH SET
//     m.content = CASE WHEN $sync_version > m.sync_version THEN $content ELSE m.content END,
//     m.memory_type = CASE WHEN $sync_version > m.sync_version THEN $memory_type ELSE m.memory_type END,
//     m.importance = CASE WHEN $sync_version > m.sync_version THEN $importance ELSE m.importance END,
//     m.embedding = CASE WHEN $sync_version > m.sync_version THEN $embedding ELSE m.embedding END,
//     m.tags = CASE WHEN $sync_version > m.sync_version THEN $tags ELSE m.tags END,
//     m.sync_version = CASE WHEN $sync_version > m.sync_version THEN $sync_version ELSE m.sync_version END,
//     m.updated_at = CASE WHEN $sync_version > m.sync_version THEN datetime($updated_at) ELSE m.updated_at END
// RETURN m;

// -- Create session relationship
// MATCH (m:Memory {id: $memory_id})
// MERGE (s:Session {id: $session_id})
// ON CREATE SET
//     s.project_id = $project_id,
//     s.started_at = datetime($session_started),
//     s.memory_count = 1
// ON MATCH SET
//     s.memory_count = s.memory_count + 1
// MERGE (m)-[:BELONGS_TO]->(s);

// -- Create project relationship
// MATCH (m:Memory {id: $memory_id})
// MATCH (p:Project {id: $project_id})
// MERGE (m)-[:TAGGED_WITH]->(p);

// ============================================================================
// RECOVERY QUERIES
// ============================================================================

// -- Bootstrap recovery: Get all memories for a project
// MATCH (m:Memory)
// WHERE m.source_project = $project_id
// RETURN m {
//     .id, .content, .memory_type, .importance, .embedding,
//     .source_project, .session_id, .tags, .sync_version,
//     .created_at, .updated_at
// }
// ORDER BY m.created_at ASC;

// -- Bootstrap recovery: Get all memories (full backup)
// MATCH (m:Memory)
// OPTIONAL MATCH (m)-[:BELONGS_TO]->(s:Session)
// RETURN m {
//     .id, .content, .memory_type, .importance, .embedding,
//     .source_project, .session_id, .tags, .sync_version,
//     .created_at, .updated_at,
//     session_summary: s.summary
// }
// ORDER BY m.source_project, m.created_at ASC;

// -- Get sync conflicts (remote has higher version)
// MATCH (m:Memory)
// WHERE m.sync_version > $local_max_version
// RETURN m.id, m.sync_version, m.updated_at;

// ============================================================================
// DESTRUCTION DETECTION QUERIES
// ============================================================================

// -- Count recent deletes (for alerting)
// // Run this after delete operations to check for rapid deletion patterns
// // If this returns > 10, trigger alert
//
// -- Note: Neo4j doesn't track deletes natively.
// -- We track via SyncEvent in PostgreSQL instead.
// -- This query checks for sudden drops in memory count:
//
// MATCH (p:Project {id: $project_id})
// OPTIONAL MATCH (m:Memory {source_project: $project_id})
// WITH p, count(m) as current_count
// WHERE current_count < $expected_minimum
// RETURN p.id, current_count, $expected_minimum as expected;

// ============================================================================
// MAINTENANCE QUERIES
// ============================================================================

// -- Get database statistics
// CALL apoc.meta.stats() YIELD labels, relTypes
// RETURN labels, relTypes;

// -- Check index status
// SHOW INDEXES;

// -- Check constraint status
// SHOW CONSTRAINTS;
