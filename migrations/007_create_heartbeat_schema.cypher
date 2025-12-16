// ============================================================================
// Migration 007: Create Heartbeat Schema
// Feature: 004-heartbeat-system
// Tasks: T002, T003
//
// Creates HeartbeatState singleton and HeartbeatLog nodes for cognitive loop.
// ============================================================================

// -----------------------------------------------------------------------------
// HeartbeatState Singleton
// -----------------------------------------------------------------------------

// Unique constraint ensures only one HeartbeatState node exists
CREATE CONSTRAINT heartbeat_state_singleton IF NOT EXISTS
FOR (s:HeartbeatState) REQUIRE s.singleton_id IS UNIQUE;

// Create the singleton HeartbeatState node with initial values
MERGE (s:HeartbeatState {singleton_id: "main"})
ON CREATE SET
    s.current_energy = 10.0,
    s.last_heartbeat_at = null,
    s.next_heartbeat_at = null,
    s.heartbeat_count = 0,
    s.paused = false,
    s.pause_reason = null,
    s.updated_at = datetime()
ON MATCH SET
    s.updated_at = datetime();

// -----------------------------------------------------------------------------
// HeartbeatLog Node
// -----------------------------------------------------------------------------

// Unique constraint on heartbeat log ID
CREATE CONSTRAINT heartbeat_log_id_unique IF NOT EXISTS
FOR (l:HeartbeatLog) REQUIRE l.id IS UNIQUE;

// Index for querying by heartbeat number (most recent first)
CREATE INDEX heartbeat_log_number_index IF NOT EXISTS
FOR (l:HeartbeatLog) ON (l.heartbeat_number);

// Index for querying by timestamp
CREATE INDEX heartbeat_log_started_index IF NOT EXISTS
FOR (l:HeartbeatLog) ON (l.started_at);

// -----------------------------------------------------------------------------
// HeartbeatConfig Node (for tunable parameters)
// -----------------------------------------------------------------------------

// Unique constraint on config key
CREATE CONSTRAINT heartbeat_config_key_unique IF NOT EXISTS
FOR (c:HeartbeatConfig) REQUIRE c.key IS UNIQUE;

// Create default configuration values
MERGE (c:HeartbeatConfig {key: "base_regeneration"}) SET c.value = 10.0;
MERGE (c:HeartbeatConfig {key: "max_energy"}) SET c.value = 20.0;
MERGE (c:HeartbeatConfig {key: "min_energy"}) SET c.value = 0.0;
MERGE (c:HeartbeatConfig {key: "heartbeat_interval_hours"}) SET c.value = 1.0;

// Action costs
MERGE (c:HeartbeatConfig {key: "cost_observe"}) SET c.value = 0.0;
MERGE (c:HeartbeatConfig {key: "cost_review_goals"}) SET c.value = 0.0;
MERGE (c:HeartbeatConfig {key: "cost_remember"}) SET c.value = 0.0;
MERGE (c:HeartbeatConfig {key: "cost_recall"}) SET c.value = 1.0;
MERGE (c:HeartbeatConfig {key: "cost_connect"}) SET c.value = 1.0;
MERGE (c:HeartbeatConfig {key: "cost_reprioritize"}) SET c.value = 1.0;
MERGE (c:HeartbeatConfig {key: "cost_reflect"}) SET c.value = 2.0;
MERGE (c:HeartbeatConfig {key: "cost_maintain"}) SET c.value = 2.0;
MERGE (c:HeartbeatConfig {key: "cost_brainstorm_goals"}) SET c.value = 3.0;
MERGE (c:HeartbeatConfig {key: "cost_inquire_shallow"}) SET c.value = 3.0;
MERGE (c:HeartbeatConfig {key: "cost_synthesize"}) SET c.value = 4.0;
MERGE (c:HeartbeatConfig {key: "cost_reach_out_user"}) SET c.value = 5.0;
MERGE (c:HeartbeatConfig {key: "cost_inquire_deep"}) SET c.value = 6.0;
MERGE (c:HeartbeatConfig {key: "cost_reach_out_public"}) SET c.value = 7.0;
MERGE (c:HeartbeatConfig {key: "cost_rest"}) SET c.value = 0.0;

// Safety thresholds
MERGE (c:HeartbeatConfig {key: "user_reach_out_cooldown_hours"}) SET c.value = 4.0;
MERGE (c:HeartbeatConfig {key: "goal_stale_threshold_days"}) SET c.value = 7.0;
MERGE (c:HeartbeatConfig {key: "max_active_goals"}) SET c.value = 3.0;

// -----------------------------------------------------------------------------
// Sample HeartbeatLog Node Structure (for documentation)
// -----------------------------------------------------------------------------
// CREATE (l:HeartbeatLog {
//     id: randomUUID(),
//     heartbeat_number: 47,
//     started_at: datetime(),
//     ended_at: datetime(),
//     energy_start: 12.0,
//     energy_end: 4.0,
//     environment_snapshot: {
//         timestamp: datetime(),
//         user_present: false,
//         time_since_user_hours: 3.0,
//         pending_events: []
//     },
//     goals_snapshot: {
//         active: ["goal-1"],
//         queued: ["goal-2", "goal-3"],
//         blocked: [],
//         stale: []
//     },
//     decision_reasoning: "I want to consolidate my understanding...",
//     actions_taken: [
//         {action: "recall", params: {query: "..."}, cost: 1, result: {...}},
//         {action: "reflect", params: {}, cost: 2, result: {...}}
//     ],
//     goals_modified: [
//         {goal_id: "...", change: "progress_added"}
//     ],
//     narrative: "This heartbeat I consolidated my understanding...",
//     emotional_valence: 0.3,
//     memory_id: "uuid-of-episodic-memory"
// });

// -----------------------------------------------------------------------------
// HeartbeatLog-Memory Link (each heartbeat creates an episodic memory)
// -----------------------------------------------------------------------------
// MATCH (l:HeartbeatLog {id: $log_id}), (m:Memory {id: $memory_id})
// CREATE (l)-[:CREATED_MEMORY]->(m);

// -----------------------------------------------------------------------------
// HeartbeatLog-Goal Link (goals touched during heartbeat)
// -----------------------------------------------------------------------------
// MATCH (l:HeartbeatLog {id: $log_id}), (g:Goal {id: $goal_id})
// CREATE (l)-[:TOUCHED_GOAL {
//     action: "progress_added"
// }]->(g);
