// ============================================================================
// MoSAEIC Core Schema - Neo4j Graph Structure
// Feature: 009-mosaeic-protocol (Neo4j-Only Architecture)
//
// MoSAEIC = Mindful Observation of Senses, Actions, Emotions, Impulses, Cognitions
//
// This schema replaces PostgreSQL five_window_captures table with graph nodes.
// All captures, patterns, and beliefs are stored directly in Neo4j.
// ============================================================================

// ----------------------------------------------------------------------------
// CONSTRAINTS (Run once during setup)
// ----------------------------------------------------------------------------

// Capture uniqueness
CREATE CONSTRAINT capture_id_unique IF NOT EXISTS
FOR (c:Capture) REQUIRE c.id IS UNIQUE;

// Pattern uniqueness
CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS
FOR (p:Pattern) REQUIRE p.id IS UNIQUE;

// Belief uniqueness
CREATE CONSTRAINT belief_id_unique IF NOT EXISTS
FOR (b:Belief) REQUIRE b.id IS UNIQUE;

// Session must exist (reference constraint)
CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.id IS UNIQUE;

// User must exist (reference constraint)
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

// ----------------------------------------------------------------------------
// INDEXES (Run once during setup)
// ----------------------------------------------------------------------------

// Capture indexes
CREATE INDEX capture_timestamp IF NOT EXISTS FOR (c:Capture) ON (c.timestamp);
CREATE INDEX capture_emotional_intensity IF NOT EXISTS FOR (c:Capture) ON (c.emotional_intensity);
CREATE INDEX capture_turning_point IF NOT EXISTS FOR (c:Capture) ON (c.turning_point);
CREATE INDEX capture_created_at IF NOT EXISTS FOR (c:Capture) ON (c.created_at);

// Pattern indexes
CREATE INDEX pattern_domain IF NOT EXISTS FOR (p:Pattern) ON (p.domain);
CREATE INDEX pattern_intervention_status IF NOT EXISTS FOR (p:Pattern) ON (p.intervention_status);
CREATE INDEX pattern_severity IF NOT EXISTS FOR (p:Pattern) ON (p.severity_score);
CREATE INDEX pattern_last_occurrence IF NOT EXISTS FOR (p:Pattern) ON (p.last_occurrence);

// Belief indexes
CREATE INDEX belief_domain IF NOT EXISTS FOR (b:Belief) ON (b.domain);
CREATE INDEX belief_type IF NOT EXISTS FOR (b:Belief) ON (b.type);
CREATE INDEX belief_adaptiveness IF NOT EXISTS FOR (b:Belief) ON (b.adaptiveness_score);

// ----------------------------------------------------------------------------
// NODE DEFINITIONS (Templates - actual creation via n8n workflows)
// ----------------------------------------------------------------------------

// ============================================================================
// CAPTURE NODE
// Replaces PostgreSQL five_window_captures table
// Stores episodic memory with correct 5 MoSAEIC windows
// ============================================================================
//
// Properties:
//   id: String (UUID)
//   timestamp: DateTime
//
//   // 5 MoSAEIC Windows (stored as JSON strings, parsed by application)
//   senses: String (JSON)
//     - interoceptive: String (internal body sensations)
//     - exteroceptive: String (external environment)
//     - bodyState: String (overall physical state)
//
//   actions: String (JSON)
//     - executed: String (what user actually did)
//     - motorOutput: String (physical movements, posture)
//
//   emotions: String (JSON)
//     - primary: String (dominant emotion)
//     - secondary: List[String] (other emotions present)
//     - valence: String (positive|negative|neutral)
//     - arousal: String (high|medium|low)
//
//   impulses: String (JSON)
//     - urges: String (what user wanted to do)
//     - avoidance: String (what user wanted to avoid)
//     - approach: String (what user was drawn toward)
//
//   cognitions: String (JSON)
//     - automaticThoughts: String (automatic appraisals)
//     - interpretations: String (meaning-making)
//     - predictions: String (what user expected to happen)
//     - coreBelief: String (extracted core belief for pattern detection)
//
//   // Metadata
//   emotional_intensity: Float (0.0-10.0)
//   turning_point: Boolean (default: false)
//   preserve_indefinitely: Boolean (default: false)
//   context: String (JSON - trigger context, environmental context)
//
//   created_at: DateTime

// Example Capture creation (via n8n workflow):
/*
CREATE (c:Capture {
    id: $capture_id,
    timestamp: datetime(),

    senses: $senses,
    actions: $actions,
    emotions: $emotions,
    impulses: $impulses,
    cognitions: $cognitions,

    emotional_intensity: $emotional_intensity,
    turning_point: CASE WHEN $emotional_intensity >= 8.5 THEN true ELSE false END,
    preserve_indefinitely: false,
    context: $context,

    created_at: datetime()
})
RETURN c
*/

// ============================================================================
// PATTERN NODE
// Maladaptive pattern detection - recurring negative beliefs/behaviors
// ============================================================================
//
// Properties:
//   id: String (UUID)
//   belief_content: String (the maladaptive belief text)
//   domain: String (self|relationships|work|world|health)
//
//   recurrence_count: Integer (how many times pattern detected)
//   severity_score: Float (0.0-1.0)
//   intervention_status: String (detected|queued|active|resolved)
//
//   first_detected: DateTime
//   last_occurrence: DateTime
//   created_at: DateTime

// Example Pattern creation:
/*
CREATE (p:Pattern {
    id: $pattern_id,
    belief_content: $belief_content,
    domain: $domain,

    recurrence_count: 1,
    severity_score: 0.1,
    intervention_status: 'detected',

    first_detected: datetime(),
    last_occurrence: datetime(),
    created_at: datetime()
})
RETURN p
*/

// Pattern recurrence update:
/*
MATCH (p:Pattern {id: $pattern_id})
SET p.recurrence_count = p.recurrence_count + 1,
    p.last_occurrence = datetime(),
    p.severity_score = CASE
        WHEN p.recurrence_count >= 5 THEN 0.9
        WHEN p.recurrence_count >= 3 THEN 0.7
        WHEN p.recurrence_count >= 2 THEN 0.5
        ELSE 0.3
    END,
    p.intervention_status = CASE
        WHEN p.recurrence_count >= 3 AND p.severity_score >= 0.7 THEN 'queued'
        ELSE p.intervention_status
    END
RETURN p
*/

// ============================================================================
// BELIEF NODE
// Rewritten beliefs (adaptive replacements for maladaptive patterns)
// ============================================================================
//
// Properties:
//   id: String (UUID)
//   content: String (the belief text)
//   type: String ('old'|'new') - old = maladaptive, new = adaptive rewrite
//   domain: String (self|relationships|work|world|health)
//
//   adaptiveness_score: Float (0.0-1.0) - prediction accuracy
//   prediction_count: Integer (total predictions made)
//   success_count: Integer (correct predictions)
//   failure_count: Integer (incorrect predictions)
//
//   created_at: DateTime
//   last_verified: DateTime

// Example Belief creation (during Phase 4 Rewrite):
/*
// First, create old belief from pattern
MATCH (p:Pattern {id: $pattern_id})
CREATE (old:Belief {
    id: randomUUID(),
    content: p.belief_content,
    type: 'old',
    domain: p.domain,
    adaptiveness_score: 0.0,
    prediction_count: 0,
    success_count: 0,
    failure_count: 0,
    created_at: datetime()
})
CREATE (p)-[:DRIVEN_BY]->(old)
RETURN old

// Then create new adaptive belief
CREATE (new:Belief {
    id: $new_belief_id,
    content: $new_belief_content,
    type: 'new',
    domain: $domain,
    adaptiveness_score: 0.5,  // Start neutral
    prediction_count: 0,
    success_count: 0,
    failure_count: 0,
    created_at: datetime()
})
WITH new
MATCH (old:Belief {id: $old_belief_id, type: 'old'})
CREATE (old)-[:REWRITTEN_TO]->(new)
RETURN new
*/

// Belief verification update (Phase 5):
/*
MATCH (b:Belief {id: $belief_id})
SET b.prediction_count = b.prediction_count + 1,
    b.success_count = CASE WHEN $prediction_correct THEN b.success_count + 1 ELSE b.success_count END,
    b.failure_count = CASE WHEN NOT $prediction_correct THEN b.failure_count + 1 ELSE b.failure_count END,
    b.adaptiveness_score = toFloat(b.success_count) / toFloat(b.prediction_count),
    b.last_verified = datetime()
RETURN b
*/

// ----------------------------------------------------------------------------
// RELATIONSHIP DEFINITIONS
// ----------------------------------------------------------------------------

// Session captures an episodic moment
// (:Session)-[:CAPTURED]->(:Capture)

// Capture exhibits a maladaptive pattern
// (:Capture)-[:EXHIBITS_PATTERN]->(:Pattern)

// Pattern is driven by an old belief
// (:Pattern)-[:DRIVEN_BY]->(:Belief {type: 'old'})

// Old belief is rewritten to new belief
// (:Belief {type: 'old'})-[:REWRITTEN_TO]->(:Belief {type: 'new'})

// User has sessions
// (:User)-[:HAS_SESSION]->(:Session)

// ----------------------------------------------------------------------------
// COMMON QUERIES
// ----------------------------------------------------------------------------

// Get all captures for a session
/*
MATCH (s:Session {id: $session_id})-[:CAPTURED]->(c:Capture)
RETURN c ORDER BY c.timestamp DESC
*/

// Get captures with high emotional intensity (potential turning points)
/*
MATCH (c:Capture)
WHERE c.emotional_intensity >= 8.0
RETURN c ORDER BY c.emotional_intensity DESC
LIMIT 50
*/

// Get decay candidates (old captures not preserved)
/*
MATCH (c:Capture)
WHERE c.preserve_indefinitely = false
  AND c.created_at < datetime() - duration({days: 180})
RETURN c.id, c.emotional_intensity, c.created_at
ORDER BY c.created_at ASC
*/

// Get patterns needing intervention
/*
MATCH (p:Pattern)
WHERE p.intervention_status = 'queued'
  AND p.recurrence_count >= 3
  AND p.severity_score >= 0.7
RETURN p ORDER BY p.severity_score DESC
*/

// Get belief rewrite success rate
/*
MATCH (old:Belief {type: 'old'})-[:REWRITTEN_TO]->(new:Belief {type: 'new'})
WHERE new.prediction_count > 0
RETURN old.content AS old_belief,
       new.content AS new_belief,
       new.adaptiveness_score AS success_rate,
       new.success_count,
       new.failure_count
*/

// Find captures that triggered a specific pattern
/*
MATCH (c:Capture)-[:EXHIBITS_PATTERN]->(p:Pattern {id: $pattern_id})
RETURN c ORDER BY c.timestamp DESC
*/
