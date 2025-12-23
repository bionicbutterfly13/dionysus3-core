-- Migration: 014_drop_mosaeic_tables.sql
-- Feature: 011 - PostgreSQL MoSAEIC Cleanup
-- Purpose: Remove deprecated Feature 008 PostgreSQL schema
--          MoSAEIC data now stored in Neo4j via n8n webhooks (Feature 009)
--
-- Drops:
--   Tables: five_window_captures, turning_points, belief_rewrites,
--           maladaptive_patterns, verification_encounters
--   Views:  beliefs_needing_revision, patterns_requiring_intervention, recent_turning_points
--   Functions: calculate_belief_accuracy, is_turning_point_candidate, get_decay_candidates,
--              get_archive_candidates, update_mosaeic_timestamp, auto_detect_turning_point
--   Types: turning_point_trigger, pattern_severity, basin_influence_type
--          (model_domain kept - used by mental_models from migration 008)
--
-- NOTE: This is a destructive migration. Only run after code cleanup complete.

-- Step 1: Drop views (depend on tables)
DROP VIEW IF EXISTS recent_turning_points;
DROP VIEW IF EXISTS patterns_requiring_intervention;
DROP VIEW IF EXISTS beliefs_needing_revision;

-- Step 2: Drop functions
DROP FUNCTION IF EXISTS auto_detect_turning_point();
DROP FUNCTION IF EXISTS update_mosaeic_timestamp();
DROP FUNCTION IF EXISTS get_archive_candidates(float, integer);
DROP FUNCTION IF EXISTS get_decay_candidates(integer);
DROP FUNCTION IF EXISTS is_turning_point_candidate(float);
DROP FUNCTION IF EXISTS calculate_belief_accuracy(uuid);

-- Step 3: Drop triggers (attached to tables)
DROP TRIGGER IF EXISTS auto_turning_point_trigger ON five_window_captures;
DROP TRIGGER IF EXISTS update_five_window_captures_timestamp ON five_window_captures;
DROP TRIGGER IF EXISTS update_turning_points_timestamp ON turning_points;
DROP TRIGGER IF EXISTS update_belief_rewrites_timestamp ON belief_rewrites;
DROP TRIGGER IF EXISTS update_maladaptive_patterns_timestamp ON maladaptive_patterns;
DROP TRIGGER IF EXISTS update_verification_encounters_timestamp ON verification_encounters;

-- Step 4: Drop tables (CASCADE handles FK constraints)
DROP TABLE IF EXISTS verification_encounters CASCADE;
DROP TABLE IF EXISTS maladaptive_patterns CASCADE;
DROP TABLE IF EXISTS belief_rewrites CASCADE;
DROP TABLE IF EXISTS turning_points CASCADE;
DROP TABLE IF EXISTS five_window_captures CASCADE;

-- Step 5: Drop types (must be after tables that use them)
DROP TYPE IF EXISTS basin_influence_type;
DROP TYPE IF EXISTS pattern_severity;
DROP TYPE IF EXISTS turning_point_trigger;
-- NOTE: model_domain is NOT dropped - used by mental_models table from migration 008

-- Step 6: Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 014: Dropped MoSAEIC PostgreSQL tables. Data now in Neo4j.';
END $$;
