-- Migration: 001_session_continuity
-- Feature: Session Continuity (Journey Tracking)
-- Date: 2025-12-15
-- Description: Create tables for journey tracking across sessions

-- Journeys table: Represents a device's complete interaction history
CREATE TABLE IF NOT EXISTS journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL UNIQUE,  -- One journey per device
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
    -- Deferred post-MVP:
    -- thoughtseed_trajectory JSONB - Array of thoughtseed states over time
    -- attractor_dynamics_history JSONB - Array of attractor basin activations
);

-- Sessions table: A single conversation within a journey
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    summary TEXT,  -- Auto-generated session summary for search
    messages JSONB DEFAULT '[]',  -- Array of {role, content, timestamp}
    diagnosis JSONB,  -- IAS diagnosis result if completed
    confidence_score INTEGER DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 100)
);

-- Journey documents table: Documents/artifacts linked to a journey
CREATE TABLE IF NOT EXISTS journey_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL CHECK (document_type IN ('woop_plan', 'file_upload', 'artifact', 'note')),
    title TEXT,
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for journey lookups
CREATE INDEX IF NOT EXISTS idx_journeys_device ON journeys(device_id);

-- Indexes for session lookups
CREATE INDEX IF NOT EXISTS idx_sessions_journey ON sessions(journey_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(journey_id, created_at DESC);

-- Full-text search on session summaries (requires pg_trgm extension)
CREATE INDEX IF NOT EXISTS idx_sessions_summary_gin ON sessions
    USING GIN (to_tsvector('english', COALESCE(summary, '')));

-- Indexes for document lookups
CREATE INDEX IF NOT EXISTS idx_journey_docs_journey ON journey_documents(journey_id);
CREATE INDEX IF NOT EXISTS idx_journey_docs_type ON journey_documents(document_type);

-- Trigger to update updated_at on journeys
CREATE OR REPLACE FUNCTION update_journey_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_journey_updated_at
    BEFORE UPDATE ON journeys
    FOR EACH ROW
    EXECUTE FUNCTION update_journey_timestamp();

-- Trigger to update updated_at on sessions
CREATE OR REPLACE FUNCTION update_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_session_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_session_timestamp();

-- Comment on tables for documentation
COMMENT ON TABLE journeys IS 'Represents a device complete interaction history across multiple sessions';
COMMENT ON TABLE sessions IS 'A single conversation within a journey, containing messages and optional diagnosis';
COMMENT ON TABLE journey_documents IS 'Documents and artifacts linked to a journey';
COMMENT ON COLUMN journeys.device_id IS 'Persistent device identifier from ~/.dionysus/device_id';
COMMENT ON COLUMN sessions.confidence_score IS 'Diagnosis confidence 0-100';
COMMENT ON COLUMN sessions.messages IS 'Array of {role: user|assistant, content: string, timestamp?: datetime}';
