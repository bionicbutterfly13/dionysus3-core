// ============================================================================
// MoSAEIC Narrative Profile Schema - Neo4j Graph Structure
// Feature: 009-mosaeic-protocol (Neo4j-Only Architecture)
//
// User Narrative Profile nodes from Step 1 therapeutic work:
// - SelfConcept: Orchid classification, neurotype, sensory style
// - Aspect: Boardroom model members (Protector, Inner CEO, etc.)
// - ThreatPrediction: Core threat predictions with silenced aspects
//
// Temporal versioning handled by Graphiti (valid_from/valid_to)
// ============================================================================

// ----------------------------------------------------------------------------
// CONSTRAINTS (Run once during setup)
// ----------------------------------------------------------------------------

// SelfConcept uniqueness
CREATE CONSTRAINT selfconcept_id_unique IF NOT EXISTS
FOR (sc:SelfConcept) REQUIRE sc.id IS UNIQUE;

// Aspect uniqueness
CREATE CONSTRAINT aspect_id_unique IF NOT EXISTS
FOR (a:Aspect) REQUIRE a.id IS UNIQUE;

// ThreatPrediction uniqueness
CREATE CONSTRAINT threatprediction_id_unique IF NOT EXISTS
FOR (tp:ThreatPrediction) REQUIRE tp.id IS UNIQUE;

// ----------------------------------------------------------------------------
// INDEXES (Run once during setup)
// ----------------------------------------------------------------------------

// SelfConcept indexes
CREATE INDEX selfconcept_type IF NOT EXISTS FOR (sc:SelfConcept) ON (sc.type);
CREATE INDEX selfconcept_version IF NOT EXISTS FOR (sc:SelfConcept) ON (sc.version);
CREATE INDEX selfconcept_valid_from IF NOT EXISTS FOR (sc:SelfConcept) ON (sc.valid_from);
CREATE INDEX selfconcept_valid_to IF NOT EXISTS FOR (sc:SelfConcept) ON (sc.valid_to);

// Aspect indexes
CREATE INDEX aspect_name IF NOT EXISTS FOR (a:Aspect) ON (a.name);
CREATE INDEX aspect_status IF NOT EXISTS FOR (a:Aspect) ON (a.status);

// ThreatPrediction indexes
CREATE INDEX threatprediction_domain IF NOT EXISTS FOR (tp:ThreatPrediction) ON (tp.domain);
CREATE INDEX threatprediction_active IF NOT EXISTS FOR (tp:ThreatPrediction) ON (tp.active);

// ----------------------------------------------------------------------------
// NODE DEFINITIONS (Templates - actual creation via n8n workflows)
// ----------------------------------------------------------------------------

// ============================================================================
// SELFCONCEPT NODE
// User's self-understanding from Step 1 narrative work
// Temporal versioning: valid_from/valid_to managed by Graphiti
// ============================================================================
//
// Properties:
//   id: String (UUID)
//   type: String ('Orchid'|'Boardroom'|'ShameCycle'|'Composite')
//   version: Integer (1, 2, 3... incrementing)
//
//   // Orchid-specific (biological model)
//   neurotype_classification: String (e.g., 'analytical_empath', 'creative_sensitive')
//   sensory_processing_style: String ('high_sensitivity'|'moderate_sensitivity'|'standard')
//   biological_model: String ('orchid'|'dandelion'|'tulip')
//
//   // Boardroom-specific (parts model summary)
//   dominant_aspect: String (which aspect is currently leading)
//   balance_status: String ('integrated'|'fragmented'|'transitioning')
//
//   // Temporal validity (Graphiti manages these)
//   valid_from: DateTime (when this version became active)
//   valid_to: DateTime (null = current version; set when superseded)
//
//   created_at: DateTime

// Example SelfConcept creation (initial profile setup from Step 1):
/*
CREATE (sc:SelfConcept {
    id: $selfconcept_id,
    type: 'Orchid',
    version: 1,

    neurotype_classification: $neurotype_classification,
    sensory_processing_style: $sensory_processing_style,
    biological_model: $biological_model,

    valid_from: datetime(),
    valid_to: null,

    created_at: datetime()
})
WITH sc
MATCH (u:User {id: $user_id})
CREATE (u)-[:HAS_PROFILE_VERSION]->(sc)
RETURN sc
*/

// SelfConcept evolution (when user's understanding grows):
/*
// First, invalidate old version
MATCH (u:User {id: $user_id})-[:HAS_PROFILE_VERSION]->(old:SelfConcept)
WHERE old.valid_to IS NULL
SET old.valid_to = datetime()
WITH old, u

// Create new version
CREATE (new:SelfConcept {
    id: randomUUID(),
    type: old.type,
    version: old.version + 1,

    neurotype_classification: COALESCE($new_neurotype, old.neurotype_classification),
    sensory_processing_style: COALESCE($new_sensory_style, old.sensory_processing_style),
    biological_model: old.biological_model,

    valid_from: datetime(),
    valid_to: null,

    created_at: datetime()
})
CREATE (u)-[:HAS_PROFILE_VERSION]->(new)
CREATE (old)-[:EVOLVED_TO]->(new)
RETURN new
*/

// ============================================================================
// ASPECT NODE
// Boardroom model members - inner parts/voices
// Based on IFS (Internal Family Systems) and Boardroom metaphor
// ============================================================================
//
// Properties:
//   id: String (UUID)
//   name: String ('Protector'|'Inner CEO'|'Inner Child'|'Inner Critic'|'Visionary'|custom)
//   role: String (description of this aspect's function)
//   status: String ('Silenced'|'Active'|'In Control'|'Balanced'|'Emerging')
//
//   symbol: String (visual representation for UI)
//   seat_position: String (where they sit in the boardroom metaphor)
//   system_message: String (therapeutic message about this aspect)
//
//   // Evolution tracking
//   original_status: String (status at first detection)
//   target_status: String (therapeutic goal status)
//
//   created_at: DateTime
//   updated_at: DateTime

// Standard Boardroom Aspects:
// - Protector: Head of Security, threat detector, hypervigilance
// - Inner CEO: Executive function, decision-maker (often silenced by Protector)
// - Inner Child: Emotional needs, vulnerability, play (often silenced)
// - Inner Critic: Performance standards, harsh self-judgment
// - Visionary: Creative self, dreams, possibilities

// Example Aspect creation (from Step 1 boardroom exercise):
/*
MATCH (u:User {id: $user_id})
CREATE (a:Aspect {
    id: randomUUID(),
    name: $name,
    role: $role,
    status: $status,

    symbol: $symbol,
    seat_position: CASE $name
        WHEN 'Protector' THEN 'Head of Table'
        WHEN 'Inner CEO' THEN 'Executive Chair'
        WHEN 'Inner Child' THEN 'Corner Seat'
        WHEN 'Inner Critic' THEN 'Standing'
        WHEN 'Visionary' THEN 'Window Seat'
        ELSE 'Guest Chair'
    END,
    system_message: CASE $name
        WHEN 'Protector' THEN 'This aspect has kept you safe. We are not firing it; we are repositioning it.'
        WHEN 'Inner CEO' THEN 'Your executive self is ready to lead when given the chance.'
        WHEN 'Inner Child' THEN 'Your emotional core deserves a seat at the table.'
        WHEN 'Inner Critic' THEN 'High standards can be valuable when balanced with compassion.'
        WHEN 'Visionary' THEN 'Your dreams matter. They guide where you want to go.'
        ELSE 'Every voice has value in the boardroom.'
    END,

    original_status: $status,
    target_status: 'Balanced',

    created_at: datetime(),
    updated_at: datetime()
})
CREATE (u)-[:HAS_ASPECT]->(a)
RETURN a
*/

// Aspect status update (during therapy/growth):
/*
MATCH (a:Aspect {id: $aspect_id})
SET a.status = $new_status,
    a.updated_at = datetime()
RETURN a
*/

// ============================================================================
// THREATPREDICTION NODE
// Core threat predictions from Step 1 "If/Then" mapping
// Format: "If [condition], then [feared outcome]"
// ============================================================================
//
// Properties:
//   id: String (UUID)
//   prediction: String (the full If/Then statement)
//   condition: String (the "If" part - the trigger)
//   feared_outcome: String (the "Then" part - what user fears)
//
//   domain: String (self|relationships|work|world|health)
//   protector_directive: String (what Protector does to prevent this)
//   emotional_cost: String (what user sacrifices by following Protector)
//   silenced_aspect: String (which aspect gets suppressed)
//
//   // Validity tracking
//   active: Boolean (is this threat still believed?)
//   challenge_count: Integer (times this was challenged)
//   invalidation_evidence: String (evidence against this threat)
//
//   created_at: DateTime
//   updated_at: DateTime

// Example ThreatPrediction creation (from Step 1 threat mapping):
/*
MATCH (u:User {id: $user_id})
CREATE (tp:ThreatPrediction {
    id: randomUUID(),
    prediction: $prediction,
    condition: $condition,
    feared_outcome: $feared_outcome,

    domain: $domain,
    protector_directive: $protector_directive,
    emotional_cost: $emotional_cost,
    silenced_aspect: $silenced_aspect,

    active: true,
    challenge_count: 0,
    invalidation_evidence: null,

    created_at: datetime(),
    updated_at: datetime()
})
CREATE (u)-[:HAS_THREAT]->(tp)

// Link to silenced aspect
WITH tp, u
MATCH (u)-[:HAS_ASPECT]->(a:Aspect {name: $silenced_aspect})
CREATE (tp)-[:SILENCES]->(a)

RETURN tp
*/

// ThreatPrediction challenge (when capture contradicts prediction):
/*
MATCH (tp:ThreatPrediction {id: $threat_id})
SET tp.challenge_count = tp.challenge_count + 1,
    tp.invalidation_evidence = COALESCE(tp.invalidation_evidence + '; ', '') + $new_evidence,
    tp.updated_at = datetime(),
    tp.active = CASE WHEN tp.challenge_count >= 3 THEN false ELSE tp.active END
RETURN tp
*/

// ----------------------------------------------------------------------------
// RELATIONSHIP DEFINITIONS
// ----------------------------------------------------------------------------

// User has profile versions (temporal self-concept)
// (:User)-[:HAS_PROFILE_VERSION]->(:SelfConcept)

// SelfConcept evolves to newer version
// (:SelfConcept)-[:EVOLVED_TO]->(:SelfConcept)

// User has boardroom aspects
// (:User)-[:HAS_ASPECT]->(:Aspect)

// User has threat predictions
// (:User)-[:HAS_THREAT]->(:ThreatPrediction)

// ThreatPrediction silences an aspect
// (:ThreatPrediction)-[:SILENCES]->(:Aspect)

// Capture activates an aspect (during emotional event)
// (:Capture)-[:ACTIVATES]->(:Aspect)

// Capture triggers a threat prediction
// (:Capture)-[:TRIGGERS]->(:ThreatPrediction)

// ----------------------------------------------------------------------------
// CROSS-SCHEMA RELATIONSHIPS (linking narrative to MoSAEIC core)
// ----------------------------------------------------------------------------

// When a capture's cognitions match a ThreatPrediction:
/*
MATCH (c:Capture {id: $capture_id})
MATCH (tp:ThreatPrediction {id: $threat_id})
CREATE (c)-[:TRIGGERS]->(tp)

// Update threat occurrence count
SET tp.challenge_count = tp.challenge_count + 1,
    tp.updated_at = datetime()

RETURN c, tp
*/

// When a capture activates a specific aspect:
/*
MATCH (c:Capture {id: $capture_id})
MATCH (a:Aspect {id: $aspect_id})
CREATE (c)-[:ACTIVATES {
    activation_strength: $strength,
    timestamp: datetime()
}]->(a)
RETURN c, a
*/

// ----------------------------------------------------------------------------
// COMMON QUERIES
// ----------------------------------------------------------------------------

// Get user's current SelfConcept (valid_to is null)
/*
MATCH (u:User {id: $user_id})-[:HAS_PROFILE_VERSION]->(sc:SelfConcept)
WHERE sc.valid_to IS NULL
RETURN sc
*/

// Get user's SelfConcept evolution history
/*
MATCH (u:User {id: $user_id})-[:HAS_PROFILE_VERSION]->(sc:SelfConcept)
RETURN sc.version, sc.valid_from, sc.valid_to, sc.type, sc.neurotype_classification
ORDER BY sc.version
*/

// Get user's boardroom state
/*
MATCH (u:User {id: $user_id})-[:HAS_ASPECT]->(a:Aspect)
RETURN a.name, a.role, a.status, a.symbol
ORDER BY CASE a.status
    WHEN 'In Control' THEN 0
    WHEN 'Active' THEN 1
    WHEN 'Balanced' THEN 2
    WHEN 'Emerging' THEN 3
    WHEN 'Silenced' THEN 4
    ELSE 5
END
*/

// Get user's active threat predictions
/*
MATCH (u:User {id: $user_id})-[:HAS_THREAT]->(tp:ThreatPrediction)
WHERE tp.active = true
RETURN tp.prediction, tp.domain, tp.protector_directive, tp.silenced_aspect
ORDER BY tp.challenge_count ASC
*/

// Find which aspects are silenced by active threats
/*
MATCH (u:User {id: $user_id})-[:HAS_THREAT]->(tp:ThreatPrediction)-[:SILENCES]->(a:Aspect)
WHERE tp.active = true
RETURN tp.prediction, a.name AS silenced_aspect, a.status
*/

// Get captures that triggered a specific threat
/*
MATCH (c:Capture)-[:TRIGGERS]->(tp:ThreatPrediction {id: $threat_id})
RETURN c ORDER BY c.timestamp DESC
*/

// Show user's growth: threats challenged over time
/*
MATCH (u:User {id: $user_id})-[:HAS_THREAT]->(tp:ThreatPrediction)
RETURN tp.prediction,
       tp.challenge_count,
       tp.active,
       tp.invalidation_evidence
ORDER BY tp.challenge_count DESC
*/

// Full narrative profile snapshot
/*
MATCH (u:User {id: $user_id})
OPTIONAL MATCH (u)-[:HAS_PROFILE_VERSION]->(sc:SelfConcept) WHERE sc.valid_to IS NULL
OPTIONAL MATCH (u)-[:HAS_ASPECT]->(a:Aspect)
OPTIONAL MATCH (u)-[:HAS_THREAT]->(tp:ThreatPrediction) WHERE tp.active = true
RETURN {
    user_id: u.id,
    self_concept: sc,
    aspects: collect(DISTINCT a),
    active_threats: collect(DISTINCT tp)
} AS profile
*/
