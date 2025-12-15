-- Migration: 003_create_sync_queue_table
-- Feature: 002-remote-persistence-safety
-- Task: T013
-- Date: 2025-12-14
-- Description: Create sync_queue table for offline operation and retry handling

CREATE TABLE IF NOT EXISTS sync_queue (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to the memory being synced
    -- Note: ON DELETE CASCADE ensures queue items are removed if memory is deleted
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,

    -- Type of operation: create, update, delete
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('create', 'update', 'delete')),

    -- Full payload to be synced (includes all memory data)
    payload JSONB NOT NULL,

    -- When this queue item was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Number of retry attempts so far
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),

    -- When to attempt next retry (NULL = immediate)
    next_retry_at TIMESTAMP WITH TIME ZONE,

    -- Last error message from failed sync attempt
    last_error TEXT
);

-- Index for processing queue in order (earliest retry first)
CREATE INDEX IF NOT EXISTS idx_sync_queue_next_retry ON sync_queue(next_retry_at ASC NULLS FIRST);

-- Index for finding queue items by memory (for deduplication)
CREATE INDEX IF NOT EXISTS idx_sync_queue_memory ON sync_queue(memory_id);

-- Index for finding items ready to process
CREATE INDEX IF NOT EXISTS idx_sync_queue_ready ON sync_queue(next_retry_at)
    WHERE next_retry_at IS NULL OR next_retry_at <= NOW();

-- Add comment for documentation
COMMENT ON TABLE sync_queue IS 'Queue for pending sync operations when remote is unavailable (Feature: 002-remote-persistence-safety)';
COMMENT ON COLUMN sync_queue.next_retry_at IS 'NULL means ready for immediate processing, otherwise exponential backoff';
COMMENT ON COLUMN sync_queue.payload IS 'Complete memory data to sync, stored as JSONB for flexibility';
