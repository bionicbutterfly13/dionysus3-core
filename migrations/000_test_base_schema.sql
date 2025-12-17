-- Minimal base schema for mental model tests
-- Creates only tables needed for TDD tests (no AGE, no full schema.sql)

-- Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Stub tables referenced by mental model migrations
CREATE TABLE IF NOT EXISTS memory_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS active_inference_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Identity and Worldview tables (needed for US6 integration tests)
CREATE TABLE IF NOT EXISTS identity_aspects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aspect_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    core_memory_clusters UUID[] DEFAULT ARRAY[]::UUID[],
    stability FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS worldview_primitives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL,
    belief TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    emotional_valence FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_identity_aspects_type ON identity_aspects(aspect_type);
CREATE INDEX IF NOT EXISTS idx_worldview_category ON worldview_primitives(category);
CREATE INDEX IF NOT EXISTS idx_worldview_confidence ON worldview_primitives(confidence);
