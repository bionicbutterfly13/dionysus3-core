-- Migration: 009_mental_models_identity_worldview_integration
-- Feature: 005-mental-models (Extended Integration)
--
-- Connects Mental Models to existing Identity & Worldview infrastructure:
--   - domain='self' models → identity_aspects
--   - domain='world' models → worldview_primitives
--
-- Bidirectional flow:
--   - Model predictions update identity stability / worldview confidence
--   - Identity/worldview inform model relevance scoring

-- ============================================================================
-- BRIDGE TABLES
-- ============================================================================

-- Link Self Models to Identity Aspects
CREATE TABLE IF NOT EXISTS model_identity_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES mental_models(id) ON DELETE CASCADE,
    identity_aspect_id UUID NOT NULL REFERENCES identity_aspects(id) ON DELETE CASCADE,

    -- Relationship metadata
    link_type TEXT NOT NULL DEFAULT 'informs',  -- 'informs', 'challenges', 'extends'
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (model_id, identity_aspect_id)
);

-- Link World Models to Worldview Primitives
CREATE TABLE IF NOT EXISTS model_worldview_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES mental_models(id) ON DELETE CASCADE,
    worldview_id UUID NOT NULL REFERENCES worldview_primitives(id) ON DELETE CASCADE,

    -- Relationship metadata
    link_type TEXT NOT NULL DEFAULT 'supports',  -- 'supports', 'contradicts', 'extends'
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (model_id, worldview_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_model_identity_links_model ON model_identity_links(model_id);
CREATE INDEX IF NOT EXISTS idx_model_identity_links_aspect ON model_identity_links(identity_aspect_id);
CREATE INDEX IF NOT EXISTS idx_model_worldview_links_model ON model_worldview_links(model_id);
CREATE INDEX IF NOT EXISTS idx_model_worldview_links_worldview ON model_worldview_links(worldview_id);

-- ============================================================================
-- FUNCTIONS: Link Creation
-- ============================================================================

-- Auto-link Self Model to Identity Aspects based on shared basins
CREATE OR REPLACE FUNCTION link_self_model_to_identity(p_model_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_model_domain model_domain;
    v_model_basins UUID[];
    v_linked_count INTEGER := 0;
BEGIN
    -- Get model info
    SELECT domain, constituent_basins
    INTO v_model_domain, v_model_basins
    FROM mental_models WHERE id = p_model_id;

    IF v_model_domain IS NULL THEN
        RAISE EXCEPTION 'Model not found: %', p_model_id;
    END IF;

    -- Only process 'self' domain models
    IF v_model_domain != 'self' THEN
        RETURN 0;
    END IF;

    -- Link to identity aspects that share core_memory_clusters
    INSERT INTO model_identity_links (model_id, identity_aspect_id, link_type, strength)
    SELECT
        p_model_id,
        ia.id,
        'informs',
        -- Strength based on overlap ratio
        (SELECT COUNT(*) FROM UNNEST(v_model_basins) b
         WHERE b = ANY(ia.core_memory_clusters))::FLOAT /
        GREATEST(array_length(v_model_basins, 1), 1)
    FROM identity_aspects ia
    WHERE ia.core_memory_clusters && v_model_basins  -- Array overlap
    ON CONFLICT (model_id, identity_aspect_id) DO UPDATE
        SET strength = EXCLUDED.strength,
            updated_at = CURRENT_TIMESTAMP
    RETURNING 1 INTO v_linked_count;

    RETURN COALESCE(v_linked_count, 0);
END;
$$;

-- Auto-link World Model to Worldview Primitives based on semantic match
CREATE OR REPLACE FUNCTION link_world_model_to_worldview(p_model_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_model_domain model_domain;
    v_model_scope TEXT[];
    v_linked_count INTEGER := 0;
BEGIN
    -- Get model info
    SELECT domain, explanatory_scope
    INTO v_model_domain, v_model_scope
    FROM mental_models WHERE id = p_model_id;

    IF v_model_domain IS NULL THEN
        RAISE EXCEPTION 'Model not found: %', p_model_id;
    END IF;

    -- Only process 'world' domain models
    IF v_model_domain != 'world' THEN
        RETURN 0;
    END IF;

    -- Link to worldview primitives matching model's explanatory scope
    -- This uses text matching on category and belief content
    INSERT INTO model_worldview_links (model_id, worldview_id, link_type, strength)
    SELECT DISTINCT
        p_model_id,
        wp.id,
        'supports',
        0.5  -- Default strength, refined by prediction outcomes
    FROM worldview_primitives wp
    WHERE wp.category = ANY(v_model_scope)
       OR EXISTS (
           SELECT 1 FROM UNNEST(v_model_scope) scope
           WHERE wp.belief ILIKE '%' || scope || '%'
       )
    ON CONFLICT (model_id, worldview_id) DO NOTHING
    RETURNING 1 INTO v_linked_count;

    RETURN COALESCE(v_linked_count, 0);
END;
$$;

-- ============================================================================
-- FUNCTIONS: Propagate Prediction Outcomes
-- ============================================================================

-- Update identity stability based on Self Model prediction accuracy
CREATE OR REPLACE FUNCTION propagate_self_model_to_identity(
    p_model_id UUID,
    p_prediction_error FLOAT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_stability_delta FLOAT;
BEGIN
    -- Calculate stability adjustment
    -- Low error = increase stability, high error = decrease
    v_stability_delta := (0.5 - p_prediction_error) * 0.1;  -- Range: -0.05 to +0.05

    -- Update linked identity aspects
    UPDATE identity_aspects ia
    SET
        stability = GREATEST(0.0, LEAST(1.0, ia.stability + v_stability_delta)),
        updated_at = CURRENT_TIMESTAMP
    FROM model_identity_links mil
    WHERE mil.model_id = p_model_id
      AND mil.identity_aspect_id = ia.id;
END;
$$;

-- Update worldview confidence based on World Model prediction accuracy
CREATE OR REPLACE FUNCTION propagate_world_model_to_worldview(
    p_model_id UUID,
    p_prediction_error FLOAT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_confidence_delta FLOAT;
BEGIN
    -- Calculate confidence adjustment
    -- Low error = increase confidence, high error = decrease
    v_confidence_delta := (0.5 - p_prediction_error) * 0.1;  -- Range: -0.05 to +0.05

    -- Update linked worldview primitives
    UPDATE worldview_primitives wp
    SET
        confidence = GREATEST(0.0, LEAST(1.0, COALESCE(wp.confidence, 0.5) + v_confidence_delta)),
        updated_at = CURRENT_TIMESTAMP
    FROM model_worldview_links mwl
    WHERE mwl.model_id = p_model_id
      AND mwl.worldview_id = wp.id;
END;
$$;

-- ============================================================================
-- ENHANCED resolve_prediction() - Propagate to Identity/Worldview
-- ============================================================================

CREATE OR REPLACE FUNCTION resolve_prediction_with_propagation(
    p_prediction_id UUID,
    p_observation JSONB,
    p_prediction_error FLOAT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_model_id UUID;
    v_model_domain model_domain;
BEGIN
    -- Call original resolve_prediction
    PERFORM resolve_prediction(p_prediction_id, p_observation, p_prediction_error);

    -- Get model info
    SELECT mm.id, mm.domain INTO v_model_id, v_model_domain
    FROM model_predictions mp
    JOIN mental_models mm ON mp.model_id = mm.id
    WHERE mp.id = p_prediction_id;

    -- Propagate based on domain
    IF v_model_domain = 'self' THEN
        PERFORM propagate_self_model_to_identity(v_model_id, p_prediction_error);
    ELSIF v_model_domain = 'world' THEN
        PERFORM propagate_world_model_to_worldview(v_model_id, p_prediction_error);
    END IF;
END;
$$;

-- ============================================================================
-- VIEWS: Identity/Worldview Integration
-- ============================================================================

-- Self Models with their identity aspects
CREATE OR REPLACE VIEW self_models_with_identity AS
SELECT
    mm.id AS model_id,
    mm.name AS model_name,
    mm.prediction_accuracy,
    ia.id AS identity_aspect_id,
    ia.aspect_type,
    ia.stability AS identity_stability,
    mil.link_type,
    mil.strength AS link_strength
FROM mental_models mm
JOIN model_identity_links mil ON mm.id = mil.model_id
JOIN identity_aspects ia ON mil.identity_aspect_id = ia.id
WHERE mm.domain = 'self' AND mm.status = 'active';

-- World Models with their worldview primitives
CREATE OR REPLACE VIEW world_models_with_worldview AS
SELECT
    mm.id AS model_id,
    mm.name AS model_name,
    mm.prediction_accuracy,
    wp.id AS worldview_id,
    wp.category AS worldview_category,
    wp.belief,
    wp.confidence AS worldview_confidence,
    mwl.link_type,
    mwl.strength AS link_strength
FROM mental_models mm
JOIN model_worldview_links mwl ON mm.id = mwl.model_id
JOIN worldview_primitives wp ON mwl.worldview_id = wp.id
WHERE mm.domain = 'world' AND mm.status = 'active';

-- ============================================================================
-- TRIGGER: Auto-link on model creation
-- ============================================================================

CREATE OR REPLACE FUNCTION auto_link_model_on_create()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.domain = 'self' THEN
        PERFORM link_self_model_to_identity(NEW.id);
    ELSIF NEW.domain = 'world' THEN
        PERFORM link_world_model_to_worldview(NEW.id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS auto_link_model_trigger ON mental_models;
CREATE TRIGGER auto_link_model_trigger
    AFTER INSERT ON mental_models
    FOR EACH ROW
    EXECUTE FUNCTION auto_link_model_on_create();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE model_identity_links IS 'Links Self-domain Mental Models to Identity Aspects';
COMMENT ON TABLE model_worldview_links IS 'Links World-domain Mental Models to Worldview Primitives';
COMMENT ON FUNCTION propagate_self_model_to_identity IS 'Updates identity stability based on Self Model prediction accuracy';
COMMENT ON FUNCTION propagate_world_model_to_worldview IS 'Updates worldview confidence based on World Model prediction accuracy';
COMMENT ON VIEW self_models_with_identity IS 'Self Models with linked identity aspects for introspection';
COMMENT ON VIEW world_models_with_worldview IS 'World Models with linked worldview beliefs for reasoning';
