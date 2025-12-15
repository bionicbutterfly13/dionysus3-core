-- Migration: 002_create_sync_events_table
-- Feature: 002-remote-persistence-safety
-- Task: T013
-- Date: 2025-12-14
-- Description: Create sync_events audit table for tracking all sync operations

CREATE TABLE IF NOT EXISTS sync_events (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Timestamp of sync event
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Direction: local_to_remote or remote_to_local
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('local_to_remote', 'remote_to_local')),

    -- Result: success, failed, partial, queued
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'failed', 'partial', 'queued')),

    -- Number of records involved in this sync
    record_count INTEGER NOT NULL DEFAULT 0 CHECK (record_count >= 0),

    -- Array of memory IDs involved in this sync
    memory_ids UUID[] DEFAULT '{}',

    -- Error message if sync failed
    error_message TEXT,

    -- Duration of sync operation in milliseconds
    duration_ms INTEGER CHECK (duration_ms >= 0),

    -- Number of retry attempts
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0)
);

-- Index for querying recent events (most common access pattern)
CREATE INDEX IF NOT EXISTS idx_sync_events_timestamp ON sync_events(timestamp DESC);

-- Index for finding failed syncs that need attention
CREATE INDEX IF NOT EXISTS idx_sync_events_failed ON sync_events(result) WHERE result = 'failed';

-- Index for finding syncs by direction
CREATE INDEX IF NOT EXISTS idx_sync_events_direction ON sync_events(direction, timestamp DESC);

-- Add comment for documentation
COMMENT ON TABLE sync_events IS 'Audit log for all sync operations (Feature: 002-remote-persistence-safety)';
COMMENT ON COLUMN sync_events.direction IS 'local_to_remote = push to Neo4j, remote_to_local = recovery from Neo4j';
COMMENT ON COLUMN sync_events.memory_ids IS 'Array of memory UUIDs involved in this sync operation';
