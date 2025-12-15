-- Migration: 004_create_session_metadata_table
-- Feature: 002-remote-persistence-safety
-- Task: T031, T032 (Phase 4 - Cross-Session Context)
--
-- Creates table for tracking session boundaries and metadata.

-- Session metadata table for tracking session start/end times
CREATE TABLE IF NOT EXISTS session_metadata (
    session_id UUID PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    project_id TEXT,
    summary TEXT,
    memory_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by project
CREATE INDEX IF NOT EXISTS idx_session_metadata_project_id
ON session_metadata(project_id);

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_session_metadata_started_at
ON session_metadata(started_at);

-- Add session_id column to memories table if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memories' AND column_name = 'session_id'
    ) THEN
        ALTER TABLE memories ADD COLUMN session_id UUID;
        CREATE INDEX idx_memories_session_id ON memories(session_id);
    END IF;
END $$;

-- Comment
COMMENT ON TABLE session_metadata IS 'Tracks coding session boundaries for cross-session memory queries';
