# Copyright 2025 Dionysus Project
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for Mental Model ↔ Identity/Worldview integration.
Feature: 005-mental-models (US6)
FRs: FR-014 through FR-020

TDD: These tests are written FIRST, before implementation.
"""

import pytest
from uuid import uuid4

# Skip DB-dependent tests until implementation exists
# Note: Service-level tests (FR-019) are unskipped for TDD validation


@pytest.mark.skip(reason="TDD: DB implementation pending")
class TestSelfModelIdentityLinking:
    """FR-014: Auto-link self-domain models to identity_aspects."""

    async def test_self_model_auto_links_to_identity_aspects(self, db_pool):
        """
        Given: A self-domain model with basins overlapping identity core_memory_clusters
        When: Model is created
        Then: model_identity_links are created with appropriate strength
        """
        # Arrange: Create identity aspect with known basins
        basin_id = uuid4()
        identity_id = await db_pool.fetchval("""
            INSERT INTO identity_aspects (aspect_type, content, core_memory_clusters)
            VALUES ('self_concept', 'I am helpful', ARRAY[$1]::uuid[])
            RETURNING id
        """, basin_id)

        # Act: Create self-domain model with overlapping basin
        model_id = await db_pool.fetchval("""
            INSERT INTO mental_models (name, domain, constituent_basins, status)
            VALUES ('Self Helper Model', 'self', ARRAY[$1]::uuid[], 'active')
            RETURNING id
        """, basin_id)

        # Trigger linking (should happen via trigger or explicit call)
        await db_pool.execute("SELECT link_self_model_to_identity($1)", model_id)

        # Assert: Link exists
        link = await db_pool.fetchrow("""
            SELECT * FROM model_identity_links
            WHERE model_id = $1 AND identity_aspect_id = $2
        """, model_id, identity_id)

        assert link is not None
        assert link["link_type"] == "informs"
        assert link["strength"] > 0

    async def test_self_model_no_link_when_no_overlap(self, db_pool):
        """
        Given: A self-domain model with basins NOT in any identity aspect
        When: Model is created
        Then: No model_identity_links are created
        """
        # Arrange: Identity with different basins
        await db_pool.execute("""
            INSERT INTO identity_aspects (aspect_type, content, core_memory_clusters)
            VALUES ('values', 'honesty', ARRAY[$1]::uuid[])
        """, uuid4())

        # Act: Create model with non-overlapping basin
        model_id = await db_pool.fetchval("""
            INSERT INTO mental_models (name, domain, constituent_basins, status)
            VALUES ('Isolated Model', 'self', ARRAY[$1]::uuid[], 'active')
            RETURNING id
        """, uuid4())

        await db_pool.execute("SELECT link_self_model_to_identity($1)", model_id)

        # Assert: No links
        count = await db_pool.fetchval("""
            SELECT COUNT(*) FROM model_identity_links WHERE model_id = $1
        """, model_id)

        assert count == 0


@pytest.mark.skip(reason="TDD: DB implementation pending")
class TestWorldModelWorldviewLinking:
    """FR-015: Auto-link world-domain models to worldview_primitives."""

    async def test_world_model_auto_links_to_worldview(self, db_pool):
        """
        Given: A world-domain model with explanatory_scope matching worldview category
        When: Model is created
        Then: model_worldview_links are created
        """
        # Arrange: Create worldview primitive
        worldview_id = await db_pool.fetchval("""
            INSERT INTO worldview_primitives (category, belief, confidence)
            VALUES ('technology', 'AI will transform work', 0.8)
            RETURNING id
        """)

        # Act: Create world model with matching scope
        model_id = await db_pool.fetchval("""
            INSERT INTO mental_models (name, domain, explanatory_scope, status)
            VALUES ('Tech Trends Model', 'world', ARRAY['technology'], 'active')
            RETURNING id
        """)

        await db_pool.execute("SELECT link_world_model_to_worldview($1)", model_id)

        # Assert: Link exists
        link = await db_pool.fetchrow("""
            SELECT * FROM model_worldview_links
            WHERE model_id = $1 AND worldview_id = $2
        """, model_id, worldview_id)

        assert link is not None
        assert link["link_type"] == "supports"


@pytest.mark.skip(reason="TDD: DB implementation pending")
class TestPredictionErrorAccumulation:
    """FR-016: Accumulate prediction errors per worldview primitive."""

    async def test_prediction_error_accumulates(self, db_pool):
        """
        Given: A world model linked to a worldview primitive
        When: Multiple predictions are resolved with errors
        Then: Errors are accumulated in worldview_prediction_errors
        """
        # Arrange
        worldview_id = await db_pool.fetchval("""
            INSERT INTO worldview_primitives (category, belief, confidence)
            VALUES ('economics', 'Markets are efficient', 0.7)
            RETURNING id
        """)

        model_id = await db_pool.fetchval("""
            INSERT INTO mental_models (name, domain, status)
            VALUES ('Market Model', 'world', 'active')
            RETURNING id
        """)

        # Link them
        await db_pool.execute("""
            INSERT INTO model_worldview_links (model_id, worldview_id)
            VALUES ($1, $2)
        """, model_id, worldview_id)

        # Act: Record multiple prediction errors
        for error in [0.3, 0.4, 0.35, 0.5, 0.45]:
            prediction_id = await db_pool.fetchval("""
                INSERT INTO model_predictions (model_id, prediction, confidence)
                VALUES ($1, '{"outcome": "up"}', 0.7)
                RETURNING id
            """, model_id)

            await db_pool.execute("""
                INSERT INTO worldview_prediction_errors
                (worldview_id, model_id, prediction_id, prediction_error)
                VALUES ($1, $2, $3, $4)
            """, worldview_id, model_id, prediction_id, error)

        # Assert: 5 errors accumulated
        count = await db_pool.fetchval("""
            SELECT COUNT(*) FROM worldview_prediction_errors
            WHERE worldview_id = $1
        """, worldview_id)

        assert count == 5


@pytest.mark.skip(reason="TDD: DB implementation pending")
class TestPrecisionWeightedUpdate:
    """FR-017: Precision-weighted error formula."""

    async def test_precision_weighted_update_calculation(self, db_pool):
        """
        Given: 5+ accumulated errors with known variance
        When: calculate_worldview_update() is called
        Then: precision_weighted_error = avg_error / (1 + variance)
        """
        # Arrange: Create worldview with errors
        worldview_id = await db_pool.fetchval("""
            INSERT INTO worldview_primitives (category, belief, confidence)
            VALUES ('test', 'test belief', 0.6)
            RETURNING id
        """)

        model_id = await db_pool.fetchval("""
            INSERT INTO mental_models (name, domain, status)
            VALUES ('Test Model', 'world', 'active')
            RETURNING id
        """)

        # Insert 5 errors with known values: [0.2, 0.3, 0.4, 0.3, 0.3]
        # avg = 0.3, variance = 0.005
        errors = [0.2, 0.3, 0.4, 0.3, 0.3]
        for error in errors:
            prediction_id = uuid4()
            await db_pool.execute("""
                INSERT INTO worldview_prediction_errors
                (worldview_id, model_id, prediction_id, prediction_error)
                VALUES ($1, $2, $3, $4)
            """, worldview_id, model_id, prediction_id, error)

        # Act: Calculate update
        result = await db_pool.fetchrow("""
            SELECT * FROM calculate_worldview_update($1)
        """, worldview_id)

        # Assert
        assert result["should_update"] is True
        assert result["evidence_count"] == 5
        # new_confidence should be less than 0.6 (errors reduce confidence)
        assert result["new_confidence"] < 0.6


@pytest.mark.skip(reason="TDD: DB implementation pending")
class TestLearningRateByStability:
    """FR-018: Learning rate based on belief stability."""

    async def test_high_confidence_low_learning_rate(self, db_pool):
        """
        Given: Worldview with confidence > 0.8
        When: Errors accumulate
        Then: Learning rate is 0.05 (slow update)
        """
        # Arrange: High confidence belief
        worldview_id = await db_pool.fetchval("""
            INSERT INTO worldview_primitives (category, belief, confidence)
            VALUES ('core', 'fundamental truth', 0.9)
            RETURNING id
        """)

        model_id = uuid4()

        # Add 5 high errors
        for _ in range(5):
            await db_pool.execute("""
                INSERT INTO worldview_prediction_errors
                (worldview_id, model_id, prediction_id, prediction_error)
                VALUES ($1, $2, $3, 0.8)
            """, worldview_id, model_id, uuid4())

        # Act
        result = await db_pool.fetchrow("""
            SELECT * FROM calculate_worldview_update($1)
        """, worldview_id)

        # Assert: With 0.05 learning rate, 0.9 confidence should drop only slightly
        # new = 0.9 * (1 - 0.05 * precision_weighted_error)
        assert result["new_confidence"] > 0.85  # Stable belief resists change

    async def test_low_confidence_high_learning_rate(self, db_pool):
        """
        Given: Worldview with confidence < 0.5
        When: Errors accumulate
        Then: Learning rate is 0.2 (fast update)
        """
        # Arrange: Low confidence belief
        worldview_id = await db_pool.fetchval("""
            INSERT INTO worldview_primitives (category, belief, confidence)
            VALUES ('uncertain', 'maybe true', 0.3)
            RETURNING id
        """)

        model_id = uuid4()

        # Add 5 moderate errors
        for _ in range(5):
            await db_pool.execute("""
                INSERT INTO worldview_prediction_errors
                (worldview_id, model_id, prediction_id, prediction_error)
                VALUES ($1, $2, $3, 0.5)
            """, worldview_id, model_id, uuid4())

        # Act
        result = await db_pool.fetchrow("""
            SELECT * FROM calculate_worldview_update($1)
        """, worldview_id)

        # Assert: With 0.2 learning rate, confidence drops more significantly
        assert result["new_confidence"] < 0.25  # Uncertain belief changes quickly


class TestWorldviewPredictionFiltering:
    """FR-019: Flag predictions contradicting worldview."""

    async def test_contradicting_prediction_flagged(self, worldview_integration_service):
        """
        Given: A prediction that contradicts linked worldview (alignment < 0.3)
        When: Prediction is generated
        Then: Prediction is flagged with suppression_factor = 0.5
        """
        # This tests the Python service, not just SQL
        result = await worldview_integration_service.filter_prediction_by_worldview(
            prediction={"outcome": "markets will crash"},
            worldview_belief="Markets are always efficient",
            base_confidence=0.8
        )

        assert result["flagged_for_review"] is True
        assert result["suppression_factor"] == 0.5
        assert result["final_confidence"] <= 0.8 * 0.5  # Suppressed (base * (1 - suppression))

    async def test_aligned_prediction_not_flagged(self, worldview_integration_service):
        """
        Given: A prediction that aligns with worldview (alignment > 0.3)
        When: Prediction is generated
        Then: Prediction passes without flagging
        """
        result = await worldview_integration_service.filter_prediction_by_worldview(
            prediction={"outcome": "technology will improve efficiency"},
            worldview_belief="Technology improves productivity",
            base_confidence=0.8
        )

        assert result["flagged_for_review"] is False
        assert result["suppression_factor"] == 0.0
        assert result["final_confidence"] >= 0.6  # Bayesian prior weighting only


@pytest.mark.skip(reason="TDD: DB and mock implementation pending")
class TestN8nWebhookSync:
    """FR-020: Sync to Neo4j via n8n webhooks."""

    async def test_prediction_resolved_triggers_webhook(
        self, model_service, mock_webhook_client
    ):
        """
        Given: A prediction is resolved with error
        When: resolve_prediction_with_propagation() is called
        Then: Webhook is sent to n8n with correct payload
        """
        # Arrange
        model_id = uuid4()
        prediction_id = uuid4()

        # Act
        await model_service.resolve_prediction_with_propagation(
            prediction_id=prediction_id,
            observation={"actual": "down"},
            prediction_error=0.4
        )

        # Assert: Webhook called
        mock_webhook_client.post.assert_called_once()
        call_args = mock_webhook_client.post.call_args

        assert "/webhook/model-prediction-resolved" in call_args[0][0]
        payload = call_args[1]["json"]
        assert payload["event"] == "prediction_resolved"
        assert payload["prediction_error"] == 0.4


# Fixtures

@pytest.fixture
async def worldview_integration_service():
    """Create WorldviewIntegrationService for testing (no db_pool needed for FR-019)."""
    from api.services.worldview_integration import WorldviewIntegrationService
    return WorldviewIntegrationService()


@pytest.fixture
def mock_webhook_client(mocker):
    """Mock httpx client for webhook testing."""
    return mocker.patch("api.services.remote_sync.httpx.AsyncClient")
