-- Migration: 001_add_sync_tracking_to_memories
-- Feature: 002-remote-persistence-safety
-- Task: T012
-- Date: 2025-12-14
-- Description: Add sync tracking columns to memories table

-- Add sync_status column (pending, synced, failed, queued, conflict)
ALTER TABLE memories ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'pending';

-- Add synced_at timestamp for tracking when memory was last synced
ALTER TABLE memories ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP WITH TIME ZONE;

-- Add sync_version for conflict detection (monotonically increasing)
ALTER TABLE memories ADD COLUMN IF NOT EXISTS sync_version INTEGER DEFAULT 1;

-- Add remote_id to store Neo4j node ID if different from local UUID
ALTER TABLE memories ADD COLUMN IF NOT EXISTS remote_id VARCHAR(255);

-- Index for finding unsynced records (common query pattern)
CREATE INDEX IF NOT EXISTS idx_memories_sync_status ON memories(sync_status);

-- Index for conflict detection queries
CREATE INDEX IF NOT EXISTS idx_memories_sync_version ON memories(id, sync_version);

-- Index for finding recently synced memories
CREATE INDEX IF NOT EXISTS idx_memories_synced_at ON memories(synced_at DESC NULLS LAST);

-- Verify columns were added
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memories' AND column_name = 'sync_status'
    ) THEN
        RAISE EXCEPTION 'Migration failed: sync_status column not created';
    END IF;
END $$;
