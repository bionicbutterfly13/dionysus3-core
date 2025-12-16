// Neo4j Schema: Mental Model ↔ Identity/Worldview Integration
// Feature: 005-mental-models (US6)
// FRs: FR-014, FR-015, FR-020
//
// Extends neo4j-mental-models.cypher with:
//   - (:MentalModel)-[:INFORMS_IDENTITY]->(:IdentityAspect)
//   - (:MentalModel)-[:SHAPES_WORLDVIEW]->(:WorldviewPrimitive)
//   - Error history tracking on relationships

// ============================================================================
// CONSTRAINTS
// ============================================================================

// IdentityAspect nodes must have unique IDs
CREATE CONSTRAINT identity_aspect_id_unique IF NOT EXISTS
FOR (i:IdentityAspect) REQUIRE i.id IS UNIQUE;

// WorldviewPrimitive nodes must have unique IDs
CREATE CONSTRAINT worldview_primitive_id_unique IF NOT EXISTS
FOR (w:WorldviewPrimitive) REQUIRE w.id IS UNIQUE;

// ============================================================================
// INDEXES
// ============================================================================

// Index on identity aspect type
CREATE INDEX identity_aspect_type IF NOT EXISTS
FOR (i:IdentityAspect) ON (i.aspect_type);

// Index on worldview category
CREATE INDEX worldview_category IF NOT EXISTS
FOR (w:WorldviewPrimitive) ON (w.category);

// Index on worldview confidence for filtering
CREATE INDEX worldview_confidence IF NOT EXISTS
FOR (w:WorldviewPrimitive) ON (w.confidence);

// ============================================================================
// NODE LABELS
// ============================================================================

// IdentityAspect: Component of self-concept
// Properties:
//   id: UUID (primary key, from PostgreSQL)
//   aspect_type: 'self_concept' | 'purpose' | 'boundary' | 'agency' | 'values'
//   content: String (the identity statement)
//   stability: Float (0.0-1.0)
//   created_at: DateTime
//   updated_at: DateTime

// WorldviewPrimitive: Belief that filters perception
// Properties:
//   id: UUID (primary key, from PostgreSQL)
//   category: String (e.g., 'technology', 'economics', 'relationships')
//   belief: String (the belief statement)
//   confidence: Float (0.0-1.0) - updated by prediction errors
//   emotional_valence: Float (-1.0 to 1.0)
//   created_at: DateTime
//   updated_at: DateTime

// ============================================================================
// RELATIONSHIPS
// ============================================================================

// (MentalModel {domain:'self'})-[:INFORMS_IDENTITY]->(IdentityAspect)
// Properties:
//   strength: Float (0.0-1.0) - how strongly the model informs this aspect
//   link_type: 'informs' | 'challenges' | 'extends'
//   error_history: Float[] - recent prediction errors
//   created_at: DateTime
//   updated_at: DateTime

// (MentalModel {domain:'world'})-[:SHAPES_WORLDVIEW]->(WorldviewPrimitive)
// Properties:
//   strength: Float (0.0-1.0) - relationship strength
//   link_type: 'supports' | 'contradicts' | 'extends'
//   error_history: Float[] - recent prediction errors (for precision calc)
//   confidence_delta: Float - cumulative confidence change applied
//   created_at: DateTime
//   updated_at: DateTime

// (Prediction)-[:AFFECTS]->(WorldviewPrimitive)
// Properties:
//   delta: Float - confidence change caused by this prediction
//   error: Float - prediction error
//   resolved_at: DateTime

// ============================================================================
// SYNC QUERIES: PostgreSQL → Neo4j (via n8n)
// ============================================================================

// -- Sync IdentityAspect from PostgreSQL
// MERGE (i:IdentityAspect {id: $id})
// ON CREATE SET
//     i.aspect_type = $aspect_type,
//     i.content = $content,
//     i.stability = $stability,
//     i.created_at = datetime($created_at)
// ON MATCH SET
//     i.content = $content,
//     i.stability = $stability,
//     i.updated_at = datetime()
// RETURN i;

// -- Sync WorldviewPrimitive from PostgreSQL
// MERGE (w:WorldviewPrimitive {id: $id})
// ON CREATE SET
//     w.category = $category,
//     w.belief = $belief,
//     w.confidence = $confidence,
//     w.emotional_valence = $emotional_valence,
//     w.created_at = datetime($created_at)
// ON MATCH SET
//     w.belief = $belief,
//     w.confidence = $confidence,
//     w.emotional_valence = $emotional_valence,
//     w.updated_at = datetime()
// RETURN w;

// ============================================================================
// LINK CREATION QUERIES
// ============================================================================

// -- Create INFORMS_IDENTITY relationship (self-domain models)
// MATCH (m:MentalModel {id: $model_id, domain: 'self'})
// MATCH (i:IdentityAspect {id: $identity_id})
// MERGE (m)-[r:INFORMS_IDENTITY]->(i)
// ON CREATE SET
//     r.strength = $strength,
//     r.link_type = $link_type,
//     r.error_history = [],
//     r.created_at = datetime()
// ON MATCH SET
//     r.strength = $strength,
//     r.updated_at = datetime()
// RETURN r;

// -- Create SHAPES_WORLDVIEW relationship (world-domain models)
// MATCH (m:MentalModel {id: $model_id, domain: 'world'})
// MATCH (w:WorldviewPrimitive {id: $worldview_id})
// MERGE (m)-[r:SHAPES_WORLDVIEW]->(w)
// ON CREATE SET
//     r.strength = $strength,
//     r.link_type = $link_type,
//     r.error_history = [],
//     r.confidence_delta = 0.0,
//     r.created_at = datetime()
// ON MATCH SET
//     r.strength = $strength,
//     r.updated_at = datetime()
// RETURN r;

// ============================================================================
// PREDICTION ERROR PROPAGATION (FR-016, FR-017)
// ============================================================================

// -- Record prediction error and update worldview confidence
// -- Called when prediction is resolved via n8n webhook
// MATCH (m:MentalModel {id: $model_id})-[r:SHAPES_WORLDVIEW]->(wp:WorldviewPrimitive)
// SET r.error_history = r.error_history + [$prediction_error]
// WITH m, r, wp
// // Keep only last 10 errors for precision calculation
// SET r.error_history = r.error_history[-10..]
// WITH wp, r,
//      size(r.error_history) as error_count,
//      reduce(s=0.0, e IN r.error_history | s + e) / size(r.error_history) as avg_error
// // Only update if we have enough evidence (threshold = 5)
// WHERE error_count >= 5
// // Calculate precision-weighted update
// WITH wp, r, avg_error,
//      // Variance approximation using range
//      reduce(min_e=1.0, e IN r.error_history | CASE WHEN e < min_e THEN e ELSE min_e END) as min_error,
//      reduce(max_e=0.0, e IN r.error_history | CASE WHEN e > max_e THEN e ELSE max_e END) as max_error
// WITH wp, r, avg_error, (max_error - min_error) / 4.0 as approx_variance
// WITH wp, r, avg_error / (1 + approx_variance) as precision_weighted_error,
//      CASE
//          WHEN wp.confidence > 0.8 THEN 0.05
//          WHEN wp.confidence > 0.5 THEN 0.1
//          ELSE 0.2
//      END as learning_rate
// // Apply update
// SET wp.confidence = wp.confidence * (1 - learning_rate * precision_weighted_error),
//     wp.updated_at = datetime(),
//     r.confidence_delta = r.confidence_delta + (wp.confidence * learning_rate * precision_weighted_error)
// RETURN wp.id, wp.confidence, r.confidence_delta;

// ============================================================================
// QUERY: Models influencing identity
// ============================================================================

// MATCH (m:MentalModel {status: 'active'})-[r:INFORMS_IDENTITY]->(i:IdentityAspect)
// WHERE m.domain = 'self'
// RETURN m.id as model_id, m.name as model_name,
//        i.id as identity_id, i.aspect_type,
//        r.strength, r.link_type,
//        size(r.error_history) as error_count
// ORDER BY r.strength DESC;

// ============================================================================
// QUERY: Worldview beliefs shaped by models
// ============================================================================

// MATCH (m:MentalModel {status: 'active'})-[r:SHAPES_WORLDVIEW]->(w:WorldviewPrimitive)
// WHERE m.domain = 'world'
// RETURN m.id as model_id, m.name as model_name,
//        w.id as worldview_id, w.category, w.belief, w.confidence,
//        r.strength, r.confidence_delta,
//        size(r.error_history) as error_count
// ORDER BY w.confidence DESC;

// ============================================================================
// QUERY: Find worldviews needing update (accumulated errors)
// ============================================================================

// MATCH (m:MentalModel)-[r:SHAPES_WORLDVIEW]->(w:WorldviewPrimitive)
// WHERE size(r.error_history) >= 5
// WITH w, collect({model: m.name, errors: r.error_history}) as model_errors
// RETURN w.id, w.category, w.belief, w.confidence, model_errors
// ORDER BY w.confidence ASC;
