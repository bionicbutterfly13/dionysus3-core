-- Migration: 011_worldview_prediction_errors
-- Feature: 005-mental-models (US6 - Identity/Worldview Integration)
-- FRs: FR-016, FR-017, FR-018
--
-- Implements precision-weighted belief update via error accumulation.
-- Based on Active Inference theory (Friston 2010, Parr et al. 2022).

-- ============================================================================
-- ACCUMULATOR TABLE
-- ============================================================================

-- Track prediction errors per worldview primitive for evidence accumulation
CREATE TABLE IF NOT EXISTS worldview_prediction_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worldview_id UUID NOT NULL REFERENCES worldview_primitives(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES mental_models(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES model_predictions(id) ON DELETE SET NULL,
    prediction_error FLOAT NOT NULL CHECK (prediction_error >= 0.0 AND prediction_error <= 1.0),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for aggregation queries (most recent errors per worldview)
CREATE INDEX IF NOT EXISTS idx_wpe_worldview_recent
ON worldview_prediction_errors(worldview_id, created_at DESC);

-- Index for model-based queries
CREATE INDEX IF NOT EXISTS idx_wpe_model
ON worldview_prediction_errors(model_id);

-- ============================================================================
-- PRECISION-WEIGHTED UPDATE FUNCTION (FR-017, FR-018)
-- ============================================================================

-- Calculate whether worldview should update and new confidence
-- Uses precision-weighted error: high variance = less update (uncertain evidence)
-- Uses adaptive learning rate: stable beliefs update slowly
CREATE OR REPLACE FUNCTION calculate_worldview_update(p_worldview_id UUID)
RETURNS TABLE(should_update BOOLEAN, new_confidence FLOAT, evidence_count INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_avg_error FLOAT;
    v_error_variance FLOAT;
    v_current_confidence FLOAT;
    v_count INT;
    v_threshold INT := 5;  -- Minimum errors before updating belief
    v_precision_weighted_error FLOAT;
    v_learning_rate FLOAT;
BEGIN
    -- Get current confidence
    SELECT confidence INTO v_current_confidence
    FROM worldview_primitives WHERE id = p_worldview_id;

    IF v_current_confidence IS NULL THEN
        RAISE EXCEPTION 'Worldview primitive not found: %', p_worldview_id;
    END IF;

    -- FR-018: Learning rate based on stability
    -- Stable beliefs (high confidence) update slowly
    -- Uncertain beliefs (low confidence) update faster
    v_learning_rate := CASE
        WHEN v_current_confidence > 0.8 THEN 0.05  -- Very stable
        WHEN v_current_confidence > 0.5 THEN 0.1   -- Moderate
        ELSE 0.2                                    -- Uncertain
    END;

    -- Calculate error statistics from recent predictions (30-day window)
    SELECT
        AVG(prediction_error),
        VARIANCE(prediction_error),
        COUNT(*)
    INTO v_avg_error, v_error_variance, v_count
    FROM worldview_prediction_errors
    WHERE worldview_id = p_worldview_id
    AND created_at > NOW() - INTERVAL '30 days';

    -- Check threshold: don't update on insufficient evidence
    IF v_count < v_threshold THEN
        RETURN QUERY SELECT FALSE, v_current_confidence, v_count;
        RETURN;
    END IF;

    -- FR-017: Precision-weighted error
    -- High variance = low precision = less update
    -- Formula: error / (1 + variance)
    v_precision_weighted_error := v_avg_error / (1 + COALESCE(v_error_variance, 0));

    -- Calculate new confidence using Bayesian-inspired update
    -- new = old * (1 - learning_rate * precision_weighted_error)
    RETURN QUERY SELECT
        TRUE,
        GREATEST(0.1, LEAST(0.99,
            v_current_confidence * (1 - v_learning_rate * v_precision_weighted_error)
        )),
        v_count;
END;
$$;

-- ============================================================================
-- APPLY WORLDVIEW UPDATE FUNCTION
-- ============================================================================

-- Actually apply the calculated update to the worldview primitive
CREATE OR REPLACE FUNCTION apply_worldview_update(p_worldview_id UUID)
RETURNS TABLE(updated BOOLEAN, old_confidence FLOAT, new_confidence FLOAT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_should_update BOOLEAN;
    v_new_confidence FLOAT;
    v_old_confidence FLOAT;
    v_evidence_count INT;
BEGIN
    -- Get current confidence
    SELECT confidence INTO v_old_confidence
    FROM worldview_primitives WHERE id = p_worldview_id;

    -- Calculate update
    SELECT cu.should_update, cu.new_confidence, cu.evidence_count
    INTO v_should_update, v_new_confidence, v_evidence_count
    FROM calculate_worldview_update(p_worldview_id) cu;

    IF NOT v_should_update THEN
        RETURN QUERY SELECT FALSE, v_old_confidence, v_old_confidence;
        RETURN;
    END IF;

    -- Apply update
    UPDATE worldview_primitives
    SET confidence = v_new_confidence,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_worldview_id;

    -- Clear old errors (optional: could keep for history)
    -- DELETE FROM worldview_prediction_errors
    -- WHERE worldview_id = p_worldview_id
    -- AND created_at < NOW() - INTERVAL '30 days';

    RETURN QUERY SELECT TRUE, v_old_confidence, v_new_confidence;
END;
$$;

-- ============================================================================
-- RECORD PREDICTION ERROR FOR WORLDVIEW
-- ============================================================================

-- Helper function to record a prediction error and check for worldview update
CREATE OR REPLACE FUNCTION record_worldview_prediction_error(
    p_model_id UUID,
    p_prediction_id UUID,
    p_prediction_error FLOAT,
    p_auto_update BOOLEAN DEFAULT FALSE
)
RETURNS TABLE(
    worldviews_affected INT,
    worldviews_updated INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_worldview_id UUID;
    v_affected INT := 0;
    v_updated INT := 0;
    v_was_updated BOOLEAN;
BEGIN
    -- Insert error for all linked worldviews
    FOR v_worldview_id IN
        SELECT worldview_id FROM model_worldview_links WHERE model_id = p_model_id
    LOOP
        INSERT INTO worldview_prediction_errors
            (worldview_id, model_id, prediction_id, prediction_error)
        VALUES
            (v_worldview_id, p_model_id, p_prediction_id, p_prediction_error);

        v_affected := v_affected + 1;

        -- Optionally auto-apply update
        IF p_auto_update THEN
            SELECT updated INTO v_was_updated
            FROM apply_worldview_update(v_worldview_id);

            IF v_was_updated THEN
                v_updated := v_updated + 1;
            END IF;
        END IF;
    END LOOP;

    RETURN QUERY SELECT v_affected, v_updated;
END;
$$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE worldview_prediction_errors IS
'Accumulates prediction errors per worldview primitive for precision-weighted belief updates (Active Inference)';

COMMENT ON FUNCTION calculate_worldview_update IS
'FR-017/FR-018: Calculates precision-weighted belief update with adaptive learning rate';

COMMENT ON FUNCTION apply_worldview_update IS
'Applies calculated update to worldview_primitives.confidence';

COMMENT ON FUNCTION record_worldview_prediction_error IS
'Records prediction error for all linked worldviews, optionally triggering updates';
