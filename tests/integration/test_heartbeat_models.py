"""
Integration Tests for Mental Models in Heartbeat System
Feature: 005-mental-models
Tasks: T018 (stub), T021 (US1), T036 (US2), T057 (US4), T066 (US5)

Tests mental model integration with heartbeat OODA loop.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from api.models.mental_model import (
    CreateModelRequest,
    MentalModel,
    ModelDomain,
    ModelPrediction,
    ModelStatus,
    PredictionTemplate,
    ReviseModelRequest,
    UpdateModelRequest,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def db_pool():
    """Database connection pool fixture."""
    # TODO: Set up test database connection
    pytest.skip("Database fixture not yet configured")


@pytest.fixture
def model_service(db_pool):
    """ModelService instance with test database."""
    from api.services.model_service import ModelService

    return ModelService(db_pool=db_pool)


@pytest.fixture
async def test_basins(db_pool):
    """Create test memory_clusters (basins) for model testing."""
    # TODO: Create test basins in database
    pytest.skip("Basin fixtures not yet configured")


@pytest.fixture
async def test_model(model_service, test_basins):
    """Create a test model for integration testing."""
    request = CreateModelRequest(
        name=f"Test Model {uuid4().hex[:8]}",
        domain=ModelDomain.USER,
        basin_ids=test_basins,
        description="Integration test model",
    )
    model = await model_service.create_model(request)
    return model


# =============================================================================
# T018: Basic Integration Tests
# =============================================================================


class TestModelServiceIntegration:
    """Basic integration tests for ModelService."""

    @pytest.mark.skip(reason="T018: Implement after database setup")
    async def test_create_model_persists(self, model_service, test_basins):
        """Created model is persisted to database."""
        request = CreateModelRequest(
            name="Persistence Test Model",
            domain=ModelDomain.USER,
            basin_ids=test_basins,
        )

        model = await model_service.create_model(request)

        # Verify model can be retrieved
        retrieved = await model_service.get_model(model.id)
        assert retrieved is not None
        assert retrieved.name == "Persistence Test Model"

    @pytest.mark.skip(reason="T018: Implement after database setup")
    async def test_list_models_returns_all(self, model_service, test_basins):
        """list_models returns all models."""
        # Create multiple models
        for i in range(3):
            await model_service.create_model(
                CreateModelRequest(
                    name=f"List Test Model {i}",
                    domain=ModelDomain.USER,
                    basin_ids=test_basins,
                )
            )

        response = await model_service.list_models()
        assert response.total >= 3


# =============================================================================
# T021: [US1] Integration test for prediction generation
# =============================================================================


class TestPredictionGeneration:
    """Integration tests for prediction generation during heartbeat."""

    @pytest.mark.asyncio
    async def test_model_generates_prediction_from_context(
        self, model_service, test_model
    ):
        """Active model generates prediction when context matches."""
        # Activate model
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )

        # Refresh model to get updated status
        activated_model = await model_service.get_model(test_model.id)

        context = {"user_message": "I'm stressed about the deadline"}

        prediction = await model_service.generate_prediction(
            model=activated_model,
            context=context,
        )

        assert prediction is not None
        assert prediction.model_id == test_model.id
        assert prediction.context == context
        assert prediction.confidence > 0

    @pytest.mark.asyncio
    async def test_prediction_stored_in_database(self, model_service, test_model):
        """Generated prediction is stored in database."""
        # Activate model first
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)

        context = {"test_key": "test_value"}

        # Generate prediction
        prediction = await model_service.generate_prediction(
            model=activated_model,
            context=context,
        )

        # Verify prediction was stored (query unresolved predictions)
        unresolved = await model_service.get_unresolved_predictions(
            model_id=test_model.id, limit=10
        )

        # Should find our prediction in unresolved list
        prediction_ids = [p.id for p in unresolved]
        assert prediction.id in prediction_ids

    @pytest.mark.asyncio
    async def test_inactive_model_does_not_generate(self, model_service, test_model):
        """Draft/deprecated models don't generate predictions."""
        # Model is draft by default
        context = {"user_message": "Test"}

        with pytest.raises(ValueError, match="not active"):
            await model_service.generate_prediction(
                model=test_model,
                context=context,
            )

    @pytest.mark.asyncio
    async def test_prediction_includes_confidence_score(
        self, model_service, test_model
    ):
        """Generated predictions include meaningful confidence scores."""
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)

        prediction = await model_service.generate_prediction(
            model=activated_model,
            context={"trigger": "test"},
        )

        # Confidence should be between 0 and 1
        assert 0.0 <= prediction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_prediction_includes_created_timestamp(
        self, model_service, test_model
    ):
        """Generated predictions have created_at timestamp."""
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)

        before = datetime.utcnow()
        prediction = await model_service.generate_prediction(
            model=activated_model,
            context={"trigger": "test"},
        )
        after = datetime.utcnow()

        # created_at should be between before and after
        assert prediction.created_at is not None
        assert before <= prediction.created_at <= after


# =============================================================================
# T036: [US2] Integration test for prediction resolution
# =============================================================================


class TestPredictionResolution:
    """Integration tests for prediction error tracking."""

    @pytest.mark.asyncio
    async def test_resolve_prediction_calculates_error(self, model_service, test_model):
        """Resolving prediction calculates and stores error."""
        # Activate model first
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)

        # Generate prediction
        prediction = await model_service.generate_prediction(
            model=activated_model,
            context={"user_message": "I'm happy today"},
        )

        # Resolve with observation
        observation = {"actual_state": "happy", "was_accurate": True}
        resolved = await model_service.resolve_prediction(
            prediction_id=prediction.id,
            observation=observation,
            prediction_error=0.1,  # Low error - prediction was accurate
        )

        assert resolved.is_resolved
        assert resolved.prediction_error == 0.1
        assert resolved.observation == observation

    @pytest.mark.asyncio
    async def test_resolution_updates_model_accuracy(self, model_service, test_model):
        """Resolving predictions updates model's rolling accuracy."""
        # Activate model first
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)
        original_accuracy = activated_model.prediction_accuracy

        # Generate and resolve multiple predictions
        for error in [0.1, 0.2, 0.1]:
            prediction = await model_service.generate_prediction(
                model=activated_model,
                context={"test": True},
            )
            await model_service.resolve_prediction(
                prediction_id=prediction.id,
                observation={"result": "test"},
                prediction_error=error,
            )

        # Check accuracy was updated
        updated = await model_service.get_model(test_model.id)
        assert updated.prediction_accuracy != original_accuracy

    @pytest.mark.asyncio
    async def test_unresolved_predictions_queryable(self, model_service, test_model):
        """Unresolved predictions can be queried."""
        # Activate model first
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)

        # Generate prediction without resolving
        await model_service.generate_prediction(
            model=activated_model,
            context={"test": True},
        )

        unresolved = await model_service.get_unresolved_predictions(
            model_id=test_model.id
        )
        assert len(unresolved) >= 1

    @pytest.mark.asyncio
    async def test_resolve_prediction_sets_resolved_at(self, model_service, test_model):
        """Resolved prediction has resolved_at timestamp set."""
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)

        prediction = await model_service.generate_prediction(
            model=activated_model,
            context={"trigger": "test"},
        )

        before = datetime.utcnow()
        resolved = await model_service.resolve_prediction(
            prediction_id=prediction.id,
            observation={"result": "observed"},
            prediction_error=0.2,
        )
        after = datetime.utcnow()

        assert resolved.resolved_at is not None
        assert before <= resolved.resolved_at <= after

    @pytest.mark.asyncio
    async def test_resolved_prediction_not_in_unresolved_query(
        self, model_service, test_model
    ):
        """Resolved predictions are not returned by get_unresolved_predictions."""
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        activated_model = await model_service.get_model(test_model.id)

        prediction = await model_service.generate_prediction(
            model=activated_model,
            context={"trigger": "test"},
        )

        # Resolve the prediction
        await model_service.resolve_prediction(
            prediction_id=prediction.id,
            observation={"result": "observed"},
            prediction_error=0.15,
        )

        # Query unresolved - should not find this prediction
        unresolved = await model_service.get_unresolved_predictions(
            model_id=test_model.id
        )
        unresolved_ids = [p.id for p in unresolved]
        assert prediction.id not in unresolved_ids


# =============================================================================
# T057: [US4] Integration test for manual model creation workflow
# =============================================================================


class TestManualModelCreation:
    """Integration tests for manual model creation and management."""

    @pytest.mark.asyncio
    async def test_create_model_with_templates(self, model_service, test_basins):
        """Model can be created with prediction templates."""
        templates = [
            PredictionTemplate(
                trigger="user mentions deadline",
                predict="time pressure",
                suggest="help prioritize",
            ),
            PredictionTemplate(
                trigger="user mentions success",
                predict="celebration mode",
                suggest="celebrate together",
            ),
        ]

        request = CreateModelRequest(
            name="Template Test Model",
            domain=ModelDomain.USER,
            basin_ids=test_basins,
            prediction_templates=templates,
        )

        model = await model_service.create_model(request)
        assert len(model.prediction_templates) == 2
        assert model.prediction_templates[0].trigger == "user mentions deadline"
        assert model.prediction_templates[1].trigger == "user mentions success"

    @pytest.mark.asyncio
    async def test_model_lifecycle_transitions(self, model_service, test_model):
        """Model status transitions correctly."""
        # Verify starts as draft
        assert test_model.status == ModelStatus.DRAFT

        # draft -> active
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        model = await model_service.get_model(test_model.id)
        assert model.status == ModelStatus.ACTIVE

        # active -> deprecated
        await model_service.deprecate_model(test_model.id)
        model = await model_service.get_model(test_model.id)
        assert model.status == ModelStatus.DEPRECATED

    @pytest.mark.asyncio
    async def test_deprecate_is_soft_delete(self, model_service, test_model):
        """Deprecating model doesn't delete it."""
        # First activate, then deprecate
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        await model_service.deprecate_model(test_model.id)

        # Model still exists
        model = await model_service.get_model(test_model.id)
        assert model is not None
        assert model.status == ModelStatus.DEPRECATED

    @pytest.mark.asyncio
    async def test_update_model_name_and_description(self, model_service, test_model):
        """Model name and description can be updated."""
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(
                name="Updated Model Name",
                description="Updated description text",
            ),
        )

        updated = await model_service.get_model(test_model.id)
        assert updated.name == "Updated Model Name"
        assert updated.description == "Updated description text"

    @pytest.mark.asyncio
    async def test_update_prediction_templates(self, model_service, test_model):
        """Model prediction templates can be updated."""
        new_templates = [
            PredictionTemplate(
                trigger="new trigger",
                predict="new prediction",
                suggest="new suggestion",
            ),
        ]

        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(prediction_templates=new_templates),
        )

        updated = await model_service.get_model(test_model.id)
        assert len(updated.prediction_templates) == 1
        assert updated.prediction_templates[0].trigger == "new trigger"

    @pytest.mark.asyncio
    async def test_cannot_activate_deprecated_model(self, model_service, test_model):
        """Cannot transition from deprecated back to active."""
        # Activate then deprecate
        await model_service.update_model(
            test_model.id,
            UpdateModelRequest(status=ModelStatus.ACTIVE),
        )
        await model_service.deprecate_model(test_model.id)

        # Try to re-activate - should fail
        with pytest.raises(ValueError, match="Invalid status transition"):
            await model_service.update_model(
                test_model.id,
                UpdateModelRequest(status=ModelStatus.ACTIVE),
            )


# =============================================================================
# T066: [US5] Integration test for domain-based model selection
# =============================================================================


class TestDomainBasedSelection:
    """Integration tests for domain-based model selection."""

    @pytest.mark.asyncio
    async def test_get_relevant_models_filters_by_domain(
        self, model_service, test_basins
    ):
        """get_relevant_models returns models matching context domain."""
        # Create models with different domains
        user_model = await model_service.create_model(
            CreateModelRequest(
                name="User Domain Model",
                domain=ModelDomain.USER,
                basin_ids=test_basins,
            )
        )
        world_model = await model_service.create_model(
            CreateModelRequest(
                name="World Domain Model",
                domain=ModelDomain.WORLD,
                basin_ids=test_basins,
            )
        )

        # Activate both
        for m in [user_model, world_model]:
            await model_service.update_model(
                m.id, UpdateModelRequest(status=ModelStatus.ACTIVE)
            )

        # Query for user context
        context = {"domain_hint": "user", "user_message": "Hello"}
        relevant = await model_service.get_relevant_models(context)

        # Should prioritize user domain model
        assert any(m.domain == ModelDomain.USER for m in relevant)

    @pytest.mark.asyncio
    async def test_list_models_filters_by_domain(self, model_service, test_basins):
        """list_models with domain parameter filters correctly."""
        # Create models with different domains
        await model_service.create_model(
            CreateModelRequest(
                name="User Model for Filter",
                domain=ModelDomain.USER,
                basin_ids=test_basins,
            )
        )
        await model_service.create_model(
            CreateModelRequest(
                name="Self Model for Filter",
                domain=ModelDomain.SELF,
                basin_ids=test_basins,
            )
        )

        # Filter by domain
        user_only = await model_service.list_models(domain=ModelDomain.USER)
        assert all(m.domain == ModelDomain.USER for m in user_only.models)

    @pytest.mark.asyncio
    async def test_get_relevant_models_returns_only_active(
        self, model_service, test_basins
    ):
        """get_relevant_models only returns active models."""
        # Create a draft model
        draft_model = await model_service.create_model(
            CreateModelRequest(
                name="Draft Model",
                domain=ModelDomain.USER,
                basin_ids=test_basins,
            )
        )

        # Create and activate another model
        active_model = await model_service.create_model(
            CreateModelRequest(
                name="Active Model",
                domain=ModelDomain.USER,
                basin_ids=test_basins,
            )
        )
        await model_service.update_model(
            active_model.id, UpdateModelRequest(status=ModelStatus.ACTIVE)
        )

        context = {"domain_hint": "user"}
        relevant = await model_service.get_relevant_models(context)

        # Draft model should not be in results
        relevant_ids = [m.id for m in relevant]
        assert draft_model.id not in relevant_ids
        # Active model should be in results
        assert active_model.id in relevant_ids

    @pytest.mark.asyncio
    async def test_get_relevant_models_respects_max_models(
        self, model_service, test_basins
    ):
        """get_relevant_models respects max_models parameter."""
        # Create and activate 3 models
        for i in range(3):
            model = await model_service.create_model(
                CreateModelRequest(
                    name=f"Model {i}",
                    domain=ModelDomain.USER,
                    basin_ids=test_basins,
                )
            )
            await model_service.update_model(
                model.id, UpdateModelRequest(status=ModelStatus.ACTIVE)
            )

        context = {"domain_hint": "user"}
        relevant = await model_service.get_relevant_models(context, max_models=2)

        # Should return at most 2 models
        assert len(relevant) <= 2

    @pytest.mark.asyncio
    async def test_list_models_filters_by_status(self, model_service, test_basins):
        """list_models with status parameter filters correctly."""
        # Create draft model
        await model_service.create_model(
            CreateModelRequest(
                name="Draft Status Model",
                domain=ModelDomain.USER,
                basin_ids=test_basins,
            )
        )

        # Create and activate another model
        active = await model_service.create_model(
            CreateModelRequest(
                name="Active Status Model",
                domain=ModelDomain.USER,
                basin_ids=test_basins,
            )
        )
        await model_service.update_model(
            active.id, UpdateModelRequest(status=ModelStatus.ACTIVE)
        )

        # Filter by active status
        active_only = await model_service.list_models(status=ModelStatus.ACTIVE)
        assert all(m.status == ModelStatus.ACTIVE for m in active_only.models)


# =============================================================================
# Heartbeat Integration Tests
# =============================================================================


class TestHeartbeatIntegration:
    """Integration tests for mental models in heartbeat OODA loop."""

    @pytest.mark.skip(reason="Implement after heartbeat integration")
    async def test_observe_phase_generates_predictions(self):
        """OBSERVE phase generates predictions from active models."""
        # TODO: Test heartbeat OBSERVE integration (T033)
        pass

    @pytest.mark.skip(reason="Implement after heartbeat integration")
    async def test_orient_phase_resolves_predictions(self):
        """ORIENT phase resolves pending predictions."""
        # TODO: Test heartbeat ORIENT integration (T041)
        pass

    @pytest.mark.skip(reason="Implement after heartbeat integration")
    async def test_decide_phase_flags_revisions(self):
        """DECIDE phase flags models needing revision."""
        # TODO: Test heartbeat DECIDE integration (T052)
        pass
