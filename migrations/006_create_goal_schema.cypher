// ============================================================================
// Migration 006: Create Goal Schema
// Feature: 004-heartbeat-system
// Task: T001
//
// Creates Goal nodes for AGI goal management system with priority-based backlog.
// ============================================================================

// -----------------------------------------------------------------------------
// Goal Node Constraints
// -----------------------------------------------------------------------------

// Unique constraint on goal ID
CREATE CONSTRAINT goal_id_unique IF NOT EXISTS
FOR (g:Goal) REQUIRE g.id IS UNIQUE;

// -----------------------------------------------------------------------------
// Goal Node Indexes
// -----------------------------------------------------------------------------

// Index for filtering by priority (active, queued, backburner)
CREATE INDEX goal_priority_index IF NOT EXISTS
FOR (g:Goal) ON (g.priority);

// Index for sorting by last_touched
CREATE INDEX goal_last_touched_index IF NOT EXISTS
FOR (g:Goal) ON (g.last_touched);

// Index for filtering by source
CREATE INDEX goal_source_index IF NOT EXISTS
FOR (g:Goal) ON (g.source);

// Composite index for active goals sorted by touch time
CREATE INDEX goal_active_recent_index IF NOT EXISTS
FOR (g:Goal) ON (g.priority, g.last_touched);

// -----------------------------------------------------------------------------
// Goal-Memory Relationship
// -----------------------------------------------------------------------------

// Index for goal-memory links by link_type
CREATE INDEX goal_memory_link_type_index IF NOT EXISTS
FOR ()-[r:GOAL_MEMORY_LINK]-() ON (r.link_type);

// -----------------------------------------------------------------------------
// Sample Goal Node Structure (for documentation)
// -----------------------------------------------------------------------------
// CREATE (g:Goal {
//     id: randomUUID(),
//     title: "Understand user's project architecture",
//     description: "Analyze codebase structure and document findings",
//     priority: "active",           // active | queued | backburner | completed | abandoned
//     source: "user_request",       // curiosity | user_request | identity | derived | external
//     parent_goal_id: null,         // UUID of parent goal (for hierarchical goals)
//     progress: [],                 // JSON array of progress notes
//     blocked_by: null,             // JSON describing blockers
//     emotional_valence: 0.3,       // -1.0 to 1.0
//     created_at: datetime(),
//     last_touched: datetime(),
//     completed_at: null,
//     abandoned_at: null,
//     abandonment_reason: null
// });

// -----------------------------------------------------------------------------
// Goal-Memory Link Structure
// -----------------------------------------------------------------------------
// MATCH (g:Goal {id: $goal_id}), (m:Memory {id: $memory_id})
// CREATE (g)-[:GOAL_MEMORY_LINK {
//     link_type: "progress",  // origin | progress | completion | blocker
//     created_at: datetime()
// }]->(m);

// -----------------------------------------------------------------------------
// Goal Hierarchy (parent-child)
// -----------------------------------------------------------------------------
// MATCH (parent:Goal {id: $parent_id}), (child:Goal {id: $child_id})
// CREATE (parent)-[:HAS_SUBGOAL]->(child);
