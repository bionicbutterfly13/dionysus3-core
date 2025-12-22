-- Migration: 012_mosaeic_memory
-- Feature: 008-mosaeic-memory
-- Task: T001 (Phase 1: Data Models)
--
-- Creates MOSAEIC dual memory architecture tables:
-- - five_window_captures: Episodic memory with 5 experiential dimensions
-- - turning_points: Flashbulb memory exemptions from decay
-- - belief_rewrites: Confidence-scored semantic beliefs
-- - maladaptive_patterns: Recurring negative pattern tracking
-- - verification_encounters: Belief testing logs
--
-- Implements opposing management protocols:
-- - Episodic: time-based decay (efficiency protocol)
-- - Semantic: confidence-based preservation (accuracy protocol)

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Turning point trigger types
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'turning_point_trigger') THEN
        CREATE TYPE turning_point_trigger AS ENUM (
            'high_emotion',
            'surprise',
            'consequence',
            'manual'
        );
    END IF;
END $$;

-- Pattern severity levels
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pattern_severity') THEN
        CREATE TYPE pattern_severity AS ENUM (
            'low',
            'moderate',
            'high',
            'critical'
        );
    END IF;
END $$;

-- Basin influence types (for belief evolution tracking)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'basin_influence_type') THEN
        CREATE TYPE basin_influence_type AS ENUM (
            'reinforcement',
            'competition',
            'synthesis',
            'emergence'
        );
    END IF;
END $$;

-- Model domain (from 008_create_mental_models.sql, created if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'model_domain') THEN
        CREATE TYPE model_domain AS ENUM ('user', 'self', 'world', 'task_specific');
    END IF;
END $$;

-- ============================================================================
-- T001: EPISODIC MEMORY TABLES
-- ============================================================================

-- Five-window episodic captures
-- Stores context-rich autobiographical snapshots across 5 experiential dimensions
-- Governed by time-based decay (efficiency protocol)
CREATE TABLE IF NOT EXISTS five_window_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    -- Five experiential windows
    mental TEXT,                    -- Thoughts, cognitions, inner dialogue
    observation TEXT,               -- Perceptions, what was noticed externally
    senses TEXT,                    -- Sensory details (visual, auditory, tactile)
    actions TEXT,                   -- Behavioral responses, what was done
    emotions TEXT,                  -- Affective states, feelings

    -- Intensity and preservation
    emotional_intensity FLOAT DEFAULT 5.0
        CHECK (emotional_intensity >= 0.0 AND emotional_intensity <= 10.0),
    preserve_indefinitely BOOLEAN DEFAULT FALSE,  -- Turning Point flag

    -- Context
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for decay queries: find old, non-preserved captures
CREATE INDEX IF NOT EXISTS idx_captures_decay
    ON five_window_captures (created_at, preserve_indefinitely)
    WHERE preserve_indefinitely = FALSE;

-- Index for session lookups
CREATE INDEX IF NOT EXISTS idx_captures_session
    ON five_window_captures (session_id);

-- Index for high-intensity captures (potential turning points)
CREATE INDEX IF NOT EXISTS idx_captures_intensity
    ON five_window_captures (emotional_intensity)
    WHERE emotional_intensity >= 8.0;


-- Turning points: Flashbulb memory markers exempt from decay
-- "Keep forever" memories based on emotional significance
CREATE TABLE IF NOT EXISTS turning_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    capture_id UUID NOT NULL REFERENCES five_window_captures(id) ON DELETE CASCADE,

    -- Trigger information
    trigger_type turning_point_trigger NOT NULL,
    trigger_description TEXT,

    -- Autobiographical linking (from 005-mental-models)
    narrative_thread_id UUID,       -- Link to autobiographical narrative thread
    life_chapter_id UUID,           -- Link to life chapter

    -- Metadata
    vividness_score FLOAT DEFAULT 0.8
        CHECK (vividness_score >= 0.0 AND vividness_score <= 1.0),

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- One turning point per capture
    CONSTRAINT turning_points_capture_unique UNIQUE (capture_id)
);

-- Index for narrative queries
CREATE INDEX IF NOT EXISTS idx_turning_points_narrative
    ON turning_points (narrative_thread_id)
    WHERE narrative_thread_id IS NOT NULL;


-- ============================================================================
-- T001: SEMANTIC MEMORY TABLES
-- ============================================================================

-- Belief rewrites: Confidence-scored semantic beliefs
-- Governed by confidence-based preservation (accuracy protocol)
-- High-confidence beliefs persist indefinitely; low-confidence may be archived
CREATE TABLE IF NOT EXISTS belief_rewrites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    old_belief_id UUID REFERENCES belief_rewrites(id) ON DELETE SET NULL,

    -- Belief content
    new_belief TEXT NOT NULL,
    domain model_domain NOT NULL,  -- Reuses enum from 008_create_mental_models.sql

    -- Confidence scoring
    adaptiveness_score FLOAT DEFAULT 0.5
        CHECK (adaptiveness_score >= 0.0 AND adaptiveness_score <= 1.0),
    evidence_count INTEGER DEFAULT 0 CHECK (evidence_count >= 0),
    last_verified TIMESTAMPTZ,

    -- Prediction tracking
    prediction_success_count INTEGER DEFAULT 0 CHECK (prediction_success_count >= 0),
    prediction_failure_count INTEGER DEFAULT 0 CHECK (prediction_failure_count >= 0),

    -- Evolution tracking
    evolution_trigger basin_influence_type,

    -- Lifecycle
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for archive queries: find low-confidence, stale beliefs
CREATE INDEX IF NOT EXISTS idx_beliefs_archive
    ON belief_rewrites (archived, adaptiveness_score, last_verified)
    WHERE archived = FALSE;

-- Index for domain queries
CREATE INDEX IF NOT EXISTS idx_beliefs_domain
    ON belief_rewrites (domain);

-- Index for belief chains (evolution history)
CREATE INDEX IF NOT EXISTS idx_beliefs_evolution
    ON belief_rewrites (old_belief_id)
    WHERE old_belief_id IS NOT NULL;


-- Maladaptive patterns: Recurring negative patterns for intervention
CREATE TABLE IF NOT EXISTS maladaptive_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern identification
    belief_content TEXT NOT NULL,
    domain model_domain NOT NULL,

    -- Severity metrics
    severity_score FLOAT DEFAULT 0.0
        CHECK (severity_score >= 0.0 AND severity_score <= 1.0),
    severity_level pattern_severity DEFAULT 'low',
    recurrence_count INTEGER DEFAULT 0 CHECK (recurrence_count >= 0),

    -- Intervention status
    intervention_triggered BOOLEAN DEFAULT FALSE,
    last_intervention TIMESTAMPTZ,

    -- Links to related entities
    linked_capture_ids UUID[] DEFAULT ARRAY[]::UUID[],
    linked_model_ids UUID[] DEFAULT ARRAY[]::UUID[],

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for intervention candidates
CREATE INDEX IF NOT EXISTS idx_patterns_intervention
    ON maladaptive_patterns (severity_score, recurrence_count)
    WHERE intervention_triggered = FALSE AND severity_score >= 0.7;

-- Index for domain queries
CREATE INDEX IF NOT EXISTS idx_patterns_domain
    ON maladaptive_patterns (domain);


-- Verification encounters: Logs when beliefs are tested against reality
CREATE TABLE IF NOT EXISTS verification_encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was tested
    belief_id UUID NOT NULL REFERENCES belief_rewrites(id) ON DELETE CASCADE,
    prediction_id UUID NOT NULL,  -- References model_predictions

    -- Outcome
    prediction_content JSONB NOT NULL,
    observation JSONB,
    belief_activated VARCHAR(10),  -- 'old' or 'new'
    prediction_error FLOAT
        CHECK (prediction_error IS NULL OR (prediction_error >= 0.0 AND prediction_error <= 1.0)),

    -- Context
    session_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for pending verifications
CREATE INDEX IF NOT EXISTS idx_verifications_pending
    ON verification_encounters (belief_id, timestamp)
    WHERE observation IS NULL;

-- Index for session queries
CREATE INDEX IF NOT EXISTS idx_verifications_session
    ON verification_encounters (session_id);


-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Calculate accuracy for a belief
CREATE OR REPLACE FUNCTION calculate_belief_accuracy(
    p_success_count INTEGER,
    p_failure_count INTEGER
) RETURNS FLOAT AS $$
DECLARE
    total INTEGER;
BEGIN
    total := p_success_count + p_failure_count;
    IF total = 0 THEN
        RETURN 0.5;  -- Prior assumption
    END IF;
    RETURN p_success_count::FLOAT / total::FLOAT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Check if a capture is a turning point candidate
CREATE OR REPLACE FUNCTION is_turning_point_candidate(
    p_capture_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_intensity FLOAT;
BEGIN
    SELECT emotional_intensity INTO v_intensity
    FROM five_window_captures
    WHERE id = p_capture_id;

    RETURN COALESCE(v_intensity >= 8.0, FALSE);
END;
$$ LANGUAGE plpgsql STABLE;

-- Get decay candidates older than threshold
CREATE OR REPLACE FUNCTION get_decay_candidates(
    p_threshold_days INTEGER DEFAULT 180
) RETURNS TABLE (
    id UUID,
    session_id UUID,
    age_days INTEGER,
    emotional_intensity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fwc.id,
        fwc.session_id,
        EXTRACT(DAY FROM (CURRENT_TIMESTAMP - fwc.created_at))::INTEGER AS age_days,
        fwc.emotional_intensity
    FROM five_window_captures fwc
    WHERE fwc.preserve_indefinitely = FALSE
    AND fwc.created_at < (CURRENT_TIMESTAMP - (p_threshold_days || ' days')::INTERVAL)
    ORDER BY fwc.created_at ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Get archive candidates for semantic beliefs
CREATE OR REPLACE FUNCTION get_archive_candidates(
    p_confidence_threshold FLOAT DEFAULT 0.3,
    p_stale_days INTEGER DEFAULT 365
) RETURNS TABLE (
    id UUID,
    new_belief TEXT,
    domain model_domain,
    adaptiveness_score FLOAT,
    days_since_verified INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        br.id,
        br.new_belief,
        br.domain,
        br.adaptiveness_score,
        EXTRACT(DAY FROM (CURRENT_TIMESTAMP - COALESCE(br.last_verified, br.created_at)))::INTEGER AS days_since_verified
    FROM belief_rewrites br
    WHERE br.archived = FALSE
    AND br.adaptiveness_score < p_confidence_threshold
    AND COALESCE(br.last_verified, br.created_at) < (CURRENT_TIMESTAMP - (p_stale_days || ' days')::INTERVAL)
    ORDER BY br.adaptiveness_score ASC;
END;
$$ LANGUAGE plpgsql STABLE;


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_mosaeic_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Belief rewrites timestamp trigger
DROP TRIGGER IF EXISTS trg_belief_rewrites_timestamp ON belief_rewrites;
CREATE TRIGGER trg_belief_rewrites_timestamp
    BEFORE UPDATE ON belief_rewrites
    FOR EACH ROW
    EXECUTE FUNCTION update_mosaeic_timestamp();

-- Maladaptive patterns timestamp trigger
DROP TRIGGER IF EXISTS trg_maladaptive_patterns_timestamp ON maladaptive_patterns;
CREATE TRIGGER trg_maladaptive_patterns_timestamp
    BEFORE UPDATE ON maladaptive_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_mosaeic_timestamp();

-- Auto-mark capture as turning point when emotional intensity is high
CREATE OR REPLACE FUNCTION auto_detect_turning_point()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.emotional_intensity >= 8.0 AND NEW.preserve_indefinitely = FALSE THEN
        NEW.preserve_indefinitely = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auto_turning_point ON five_window_captures;
CREATE TRIGGER trg_auto_turning_point
    BEFORE INSERT OR UPDATE ON five_window_captures
    FOR EACH ROW
    EXECUTE FUNCTION auto_detect_turning_point();


-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for beliefs needing revision (accuracy < 50% with sufficient data)
CREATE OR REPLACE VIEW beliefs_needing_revision AS
SELECT
    id,
    new_belief,
    domain,
    adaptiveness_score,
    prediction_success_count,
    prediction_failure_count,
    calculate_belief_accuracy(prediction_success_count, prediction_failure_count) AS accuracy,
    prediction_success_count + prediction_failure_count AS total_predictions,
    last_verified,
    updated_at
FROM belief_rewrites
WHERE archived = FALSE
AND prediction_success_count + prediction_failure_count >= 5
AND calculate_belief_accuracy(prediction_success_count, prediction_failure_count) < 0.5;

-- View for patterns requiring intervention
CREATE OR REPLACE VIEW patterns_requiring_intervention AS
SELECT
    id,
    belief_content,
    domain,
    severity_score,
    severity_level,
    recurrence_count,
    array_length(linked_capture_ids, 1) AS linked_captures,
    array_length(linked_model_ids, 1) AS linked_models,
    created_at,
    updated_at
FROM maladaptive_patterns
WHERE intervention_triggered = FALSE
AND severity_score >= 0.7
AND recurrence_count >= 3;

-- View for recent turning points
CREATE OR REPLACE VIEW recent_turning_points AS
SELECT
    tp.id,
    tp.capture_id,
    tp.trigger_type,
    tp.trigger_description,
    tp.vividness_score,
    tp.created_at,
    fwc.emotional_intensity,
    fwc.mental,
    fwc.emotions,
    fwc.session_id
FROM turning_points tp
JOIN five_window_captures fwc ON fwc.id = tp.capture_id
ORDER BY tp.created_at DESC;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE five_window_captures IS
    'Episodic memory: Context-rich autobiographical snapshots. Time-based decay, 6-month default threshold.';

COMMENT ON TABLE turning_points IS
    'Flashbulb memories exempt from decay. Triggered by high emotion, surprise, or consequence.';

COMMENT ON TABLE belief_rewrites IS
    'Semantic memory: Confidence-scored beliefs. Confidence-based preservation, archive at <30%.';

COMMENT ON TABLE maladaptive_patterns IS
    'Recurring negative patterns tracked for intervention. Severity escalates with recurrence.';

COMMENT ON TABLE verification_encounters IS
    'Logs when beliefs are tested against reality during MOSAEIC Phase 5 Verification.';

COMMENT ON TYPE turning_point_trigger IS
    'What triggered a memory to be marked as a Turning Point (exempt from decay).';

COMMENT ON TYPE pattern_severity IS
    'Severity levels for maladaptive patterns: low, moderate, high, critical.';

COMMENT ON TYPE basin_influence_type IS
    'Basin dynamics when new beliefs emerge: reinforcement, competition, synthesis, emergence.';
