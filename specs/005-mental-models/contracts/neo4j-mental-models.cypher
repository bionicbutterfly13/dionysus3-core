// Neo4j Schema Extension for Mental Models
// Feature: 005-mental-models
// Integration with existing Memory graph
//
// Run after neo4j-schema.cypher is applied:
//   cat neo4j-mental-models.cypher | cypher-shell -u neo4j -p <password> -a bolt://72.61.78.89:7687

// ============================================================================
// CONSTRAINTS
// ============================================================================

// MentalModel nodes must have unique IDs
CREATE CONSTRAINT mental_model_id_unique IF NOT EXISTS
FOR (m:MentalModel) REQUIRE m.id IS UNIQUE;

// MentalModel names should be unique
CREATE CONSTRAINT mental_model_name_unique IF NOT EXISTS
FOR (m:MentalModel) REQUIRE m.name IS UNIQUE;

// Basin (memory cluster) nodes must have unique IDs
CREATE CONSTRAINT basin_id_unique IF NOT EXISTS
FOR (b:Basin) REQUIRE b.id IS UNIQUE;

// Prediction nodes must have unique IDs
CREATE CONSTRAINT prediction_id_unique IF NOT EXISTS
FOR (p:Prediction) REQUIRE p.id IS UNIQUE;

// ============================================================================
// INDEXES
// ============================================================================

// Index on model domain for filtering
CREATE INDEX mental_model_domain IF NOT EXISTS
FOR (m:MentalModel) ON (m.domain);

// Index on model status for active model queries
CREATE INDEX mental_model_status IF NOT EXISTS
FOR (m:MentalModel) ON (m.status);

// Composite index for domain + status
CREATE INDEX mental_model_domain_status IF NOT EXISTS
FOR (m:MentalModel) ON (m.domain, m.status);

// Index on prediction resolution status
CREATE INDEX prediction_resolved IF NOT EXISTS
FOR (p:Prediction) ON (p.resolved_at);

// Index on basin centroid for similarity queries
CREATE VECTOR INDEX basin_centroid IF NOT EXISTS
FOR (b:Basin) ON (b.centroid_embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
}};

// ============================================================================
// NODE LABELS
// ============================================================================

// MentalModel: Structured combination of basins for prediction
// Properties:
//   id: UUID (primary key)
//   name: String (unique)
//   domain: 'user' | 'self' | 'world' | 'task_specific'
//   status: 'draft' | 'active' | 'deprecated'
//   description: String (optional)
//   prediction_accuracy: Float (0.0-1.0)
//   revision_count: Integer
//   prediction_templates: JSON array of {trigger, predict, suggest}
//   created_at: DateTime
//   updated_at: DateTime

// Basin: Memory cluster (attractor basin)
// Properties:
//   id: UUID (primary key)
//   name: String
//   centroid_embedding: Float[768] (average of member memories)
//   member_count: Integer
//   coherence: Float (0.0-1.0) - how tightly clustered
//   created_at: DateTime
//   updated_at: DateTime

// Prediction: Model prediction instance
// Properties:
//   id: UUID (primary key)
//   prediction: JSON (the actual prediction content)
//   confidence: Float (0.0-1.0)
//   context: JSON (what triggered the prediction)
//   observation: JSON (actual outcome, filled on resolution)
//   prediction_error: Float (0.0-1.0, filled on resolution)
//   resolved_at: DateTime (null if unresolved)
//   created_at: DateTime

// ============================================================================
// RELATIONSHIPS
// ============================================================================

// (MentalModel)-[:HAS_BASIN {weight: Float, role: String}]->(Basin)
// - weight: importance of this basin to the model (0.0-1.0)
// - role: 'core' | 'supporting' | 'contextual'

// (Basin)-[:CONTAINS]->(Memory)
// - Links basins to their constituent memories

// (MentalModel)-[:GENERATED]->(Prediction)
// - Links models to their predictions

// (Prediction)-[:ABOUT]->(Memory)
// - Links predictions to relevant memories (optional)

// (MentalModel)-[:TARGETS_DOMAIN]->(Project)
// - Links domain-specific models to their project context

// (Basin)-[:RELATED_TO {strength: Float, type: String}]->(Basin)
// - Inter-basin relationships
// - type: 'reinforces' | 'contradicts' | 'extends'

// ============================================================================
// EXAMPLE MODEL CREATION
// ============================================================================

// -- Create a mental model from existing memory clusters
// MATCH (m1:Memory), (m2:Memory)
// WHERE m1.tags CONTAINS 'work-stress' AND m2.tags CONTAINS 'productivity'
// WITH collect(DISTINCT m1) + collect(DISTINCT m2) as memories
//
// // Create basin from memories
// CREATE (b:Basin {
//     id: randomUUID(),
//     name: 'Work Stress Patterns',
//     member_count: size(memories),
//     created_at: datetime()
// })
// WITH b, memories
// UNWIND memories as mem
// CREATE (b)-[:CONTAINS]->(mem)
//
// // Create the model
// CREATE (model:MentalModel {
//     id: randomUUID(),
//     name: 'User Work Patterns',
//     domain: 'user',
//     status: 'draft',
//     prediction_accuracy: 0.5,
//     revision_count: 0,
//     prediction_templates: [
//         '{"trigger": "deadline mention", "predict": "time pressure", "suggest": "help prioritize"}'
//     ],
//     created_at: datetime(),
//     updated_at: datetime()
// })
// CREATE (model)-[:HAS_BASIN {weight: 1.0, role: 'core'}]->(b)
// RETURN model;

// ============================================================================
// QUERY: Get active models for domain
// ============================================================================

// MATCH (m:MentalModel {domain: $domain, status: 'active'})
// OPTIONAL MATCH (m)-[r:HAS_BASIN]->(b:Basin)
// RETURN m {
//     .id, .name, .domain, .status, .prediction_accuracy,
//     basins: collect({id: b.id, name: b.name, weight: r.weight, role: r.role})
// }
// ORDER BY m.prediction_accuracy DESC;

// ============================================================================
// QUERY: Find relevant models for context
// ============================================================================

// -- Given a context embedding, find models with similar basins
// MATCH (m:MentalModel {status: 'active'})-[:HAS_BASIN]->(b:Basin)
// CALL db.index.vector.queryNodes('basin_centroid', 5, $context_embedding)
// YIELD node, score
// WHERE node = b
// WITH m, max(score) as relevance
// RETURN m {.id, .name, .domain, relevance: relevance}
// ORDER BY relevance DESC
// LIMIT 5;

// ============================================================================
// QUERY: Generate prediction
// ============================================================================

// MATCH (m:MentalModel {id: $model_id, status: 'active'})
// CREATE (p:Prediction {
//     id: randomUUID(),
//     prediction: $prediction,
//     confidence: $confidence,
//     context: $context,
//     created_at: datetime()
// })
// CREATE (m)-[:GENERATED]->(p)
// RETURN p;

// ============================================================================
// QUERY: Resolve prediction
// ============================================================================

// MATCH (p:Prediction {id: $prediction_id})
// WHERE p.resolved_at IS NULL
// SET p.observation = $observation,
//     p.prediction_error = $error,
//     p.resolved_at = datetime()
// WITH p
// MATCH (m:MentalModel)-[:GENERATED]->(p)
// // Update model accuracy (EMA: 0.9 * old + 0.1 * (1 - error))
// SET m.prediction_accuracy = 0.9 * m.prediction_accuracy + 0.1 * (1 - $error),
//     m.updated_at = datetime()
// RETURN m.prediction_accuracy;

// ============================================================================
// QUERY: Create basin from memories
// ============================================================================

// -- Group memories by semantic similarity to create a basin
// MATCH (m:Memory)
// WHERE m.source_project = $project_id
//   AND m.memory_type IN ['insight', 'pattern', 'observation']
// CALL db.index.vector.queryNodes('memory_embedding', 20, $seed_embedding)
// YIELD node, score
// WHERE node = m AND score > 0.7
// WITH collect(node) as cluster_memories, avg(score) as coherence
//
// CREATE (b:Basin {
//     id: randomUUID(),
//     name: $basin_name,
//     member_count: size(cluster_memories),
//     coherence: coherence,
//     created_at: datetime()
// })
// WITH b, cluster_memories
// UNWIND cluster_memories as mem
// CREATE (b)-[:CONTAINS]->(mem)
// // Calculate centroid from member embeddings
// WITH b, collect(mem.embedding) as embeddings
// SET b.centroid_embedding = reduce(
//     acc = [0.0] * 768,
//     e IN embeddings |
//     [i IN range(0, 767) | acc[i] + e[i] / size(embeddings)]
// )
// RETURN b;

// ============================================================================
// SYNC: PostgreSQL to Neo4j
// ============================================================================

// -- Sync a model from PostgreSQL to Neo4j
// MERGE (m:MentalModel {id: $model_id})
// ON CREATE SET
//     m.name = $name,
//     m.domain = $domain,
//     m.status = $status,
//     m.description = $description,
//     m.prediction_accuracy = $prediction_accuracy,
//     m.revision_count = $revision_count,
//     m.prediction_templates = $prediction_templates,
//     m.created_at = datetime($created_at)
// ON MATCH SET
//     m.name = $name,
//     m.domain = $domain,
//     m.status = $status,
//     m.description = $description,
//     m.prediction_accuracy = $prediction_accuracy,
//     m.revision_count = $revision_count,
//     m.prediction_templates = $prediction_templates,
//     m.updated_at = datetime()
// RETURN m;

// -- Sync basin relationships
// MATCH (m:MentalModel {id: $model_id})
// UNWIND $basin_ids as basin_id
// MERGE (b:Basin {id: basin_id})
// MERGE (m)-[:HAS_BASIN]->(b)
// RETURN m, collect(b) as basins;
