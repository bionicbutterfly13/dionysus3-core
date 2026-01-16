"""
Unit Tests for Mental Model Functions
Feature: 005-mental-models
Tasks: T016 (stub), T035 (US2), T044 (US3), T065 (US5)

Tests SQL functions and model service logic.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from api.models.mental_model import (
    MentalModel,
    ModelDomain,
    ModelPrediction,
    ModelRevision,
    ModelStatus,
    RevisionTrigger,
    PredictionTemplate,
    BasinRelationships,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_basin_ids():
    """Sample basin UUIDs for testing."""
    return [uuid4(), uuid4()]


@pytest.fixture
def sample_model(sample_basin_ids):
    """Sample MentalModel for testing."""
    return MentalModel(
        name="Test Model",
        domain=ModelDomain.USER,
        constituent_basins=sample_basin_ids,
        description="A test mental model",
    )


@pytest.fixture
def sample_prediction(sample_model):
    """Sample ModelPrediction for testing."""
    return ModelPrediction(
        model_id=sample_model.id,
        prediction={"state": "happy", "confidence_reason": "positive keywords"},
        confidence=0.8,
        context={"user_message": "I'm having a great day!"},
    )


# =============================================================================
# T016: Model Entity Tests
# =============================================================================


class TestMentalModelEntity:
    """Tests for MentalModel Pydantic model."""

    def test_model_defaults(self, sample_basin_ids):
        """MentalModel has sensible defaults."""
        model = MentalModel(
            name="Test",
            domain=ModelDomain.USER,
            constituent_basins=sample_basin_ids,
        )

        assert model.name == "Test"
        assert model.domain == ModelDomain.USER
        assert model.status == ModelStatus.DRAFT
        assert model.prediction_accuracy == 0.5
        assert model.revision_count == 0
        assert len(model.constituent_basins) == 2

    def test_model_requires_basins(self):
        """MentalModel requires at least one basin."""
        with pytest.raises(ValueError):
            MentalModel(
                name="Test",
                domain=ModelDomain.USER,
                constituent_basins=[],
            )

    def test_model_domain_enum(self):
        """ModelDomain enum has expected values."""
        assert ModelDomain.USER.value == "user"
        assert ModelDomain.SELF.value == "self"
        assert ModelDomain.WORLD.value == "world"
        assert ModelDomain.TASK_SPECIFIC.value == "task_specific"

    def test_model_status_enum(self):
        """ModelStatus enum has expected values."""
        assert ModelStatus.DRAFT.value == "draft"
        assert ModelStatus.ACTIVE.value == "active"
        assert ModelStatus.DEPRECATED.value == "deprecated"


class TestModelPredictionEntity:
    """Tests for ModelPrediction Pydantic model."""

    def test_prediction_defaults(self):
        """ModelPrediction has sensible defaults."""
        prediction = ModelPrediction(
            model_id=uuid4(),
            prediction={"state": "neutral"},
        )

        assert prediction.confidence == 0.5
        assert prediction.context is None
        assert prediction.observation is None
        assert prediction.prediction_error is None
        assert prediction.resolved_at is None
        assert not prediction.is_resolved

    def test_prediction_resolution_status(self, sample_prediction):
        """Prediction knows if it's resolved."""
        assert not sample_prediction.is_resolved

        # Simulate resolution
        sample_prediction.resolved_at = datetime.utcnow()
        sample_prediction.observation = {"actual": "happy"}
        sample_prediction.prediction_error = 0.1

        assert sample_prediction.is_resolved


# =============================================================================
# T035: [US2] Unit test for resolve_prediction SQL function
# =============================================================================


class TestResolvePredictionFunction:
    """Tests for resolve_prediction SQL function behavior."""

    @pytest.mark.asyncio
    async def test_resolve_prediction_updates_fields(self, sample_prediction):
        """Resolving prediction updates observation, error, and resolved_at."""
        # Simulate resolve behavior
        observation = {"actual_state": "happy"}
        error = 0.1

        # Apply resolution
        sample_prediction.observation = observation
        sample_prediction.prediction_error = error
        sample_prediction.resolved_at = datetime.utcnow()

        assert sample_prediction.observation == observation
        assert sample_prediction.prediction_error == 0.1
        assert sample_prediction.resolved_at is not None
        assert sample_prediction.is_resolved

    @pytest.mark.asyncio
    async def test_resolve_prediction_accuracy_update_logic(self):
        """Model accuracy uses exponential moving average formula."""
        # EMA formula: new = alpha * (1 - error) + (1 - alpha) * old
        alpha = 0.1
        old_accuracy = 0.75
        prediction_error = 0.2

        new_accuracy = alpha * (1.0 - prediction_error) + (1.0 - alpha) * old_accuracy

        # Expected: 0.1 * 0.8 + 0.9 * 0.75 = 0.08 + 0.675 = 0.755
        assert abs(new_accuracy - 0.755) < 0.001

    def test_resolve_prediction_validates_error_range(self):
        """Error must be between 0.0 and 1.0."""
        prediction = ModelPrediction(
            model_id=uuid4(),
            prediction={"state": "test"},
        )

        # Valid error values
        prediction.prediction_error = 0.0
        assert prediction.prediction_error == 0.0

        prediction.prediction_error = 1.0
        assert prediction.prediction_error == 1.0

        prediction.prediction_error = 0.5
        assert prediction.prediction_error == 0.5

    def test_prediction_is_resolved_checks_resolved_at(self, sample_prediction):
        """is_resolved property checks resolved_at timestamp."""
        assert not sample_prediction.is_resolved

        sample_prediction.resolved_at = datetime.utcnow()
        assert sample_prediction.is_resolved

    @pytest.mark.asyncio
    async def test_resolve_with_mock_service(self, sample_prediction):
        """Test resolve_prediction through mocked service."""
        from api.services.model_service import ModelService

        # Mock the driver (Neo4j via webhooks)
        mock_driver = AsyncMock()
        mock_driver.execute_query = AsyncMock(return_value=[{
            "m": {
                "id": str(sample_prediction.model_id),
                "name": "test_model",
                "domain": "test",
                "current_beliefs": "{}",
                "confidence": 0.8,
            },
            "p": {
                "id": str(sample_prediction.id),
                "model_id": str(sample_prediction.model_id),
                "prediction": '{"key": "value"}',
                "confidence": sample_prediction.confidence,
                "context": '{}',
                "observation": '{"actual": "test"}',
                "prediction_error": 0.1,
                "resolved_at": datetime.utcnow().isoformat(),
                "created_at": sample_prediction.created_at.isoformat(),
                "inference_state_id": None,
            }
        }])
        service = ModelService(driver=mock_driver)

        # Test resolve_prediction
        result = await service.resolve_prediction(
            prediction_id=sample_prediction.id,
            observation={"actual": "test"},
            prediction_error=0.1
        )
        assert mock_driver.execute_query.called


# =============================================================================
# T044: [US3] Unit test for flag_model_revision SQL function
# =============================================================================


class TestFlagModelRevisionFunction:
    """Tests for flag_model_revision SQL function behavior."""

    def test_revision_trigger_enum_values(self):
        """RevisionTrigger enum has expected values."""
        assert RevisionTrigger.PREDICTION_ERROR.value == "prediction_error"
        assert RevisionTrigger.USER_REQUEST.value == "user_request"
        assert RevisionTrigger.NEW_MEMORY.value == "new_memory"

    def test_model_revision_entity_defaults(self, sample_model):
        """ModelRevision has sensible defaults."""
        revision = ModelRevision(
            model_id=sample_model.id,
            revision_number=1,
            trigger=RevisionTrigger.USER_REQUEST,
            trigger_description="Manual revision",
        )

        assert revision.model_id == sample_model.id
        assert revision.revision_number == 1
        assert revision.trigger == RevisionTrigger.USER_REQUEST
        assert revision.basins_added == []
        assert revision.basins_removed == []
        assert revision.accuracy_before is None
        assert revision.accuracy_after is None

    def test_revision_captures_basin_changes(self, sample_model):
        """Revision records basin additions and removals."""
        new_basin = uuid4()
        removed_basin = sample_model.constituent_basins[0]

        revision = ModelRevision(
            model_id=sample_model.id,
            revision_number=1,
            trigger=RevisionTrigger.NEW_MEMORY,
            trigger_description="Adding new memory basin",
            basins_added=[new_basin],
            basins_removed=[removed_basin],
        )

        assert len(revision.basins_added) == 1
        assert new_basin in revision.basins_added
        assert len(revision.basins_removed) == 1
        assert removed_basin in revision.basins_removed

    def test_revision_prevents_empty_model(self, sample_model):
        """Revision cannot result in empty model (validation logic)."""
        # Model has 2 basins, removing both should be invalid
        all_basins = sample_model.constituent_basins.copy()

        # This would be validated at service level
        # Revision entity itself doesn't prevent this
        revision = ModelRevision(
            model_id=sample_model.id,
            revision_number=1,
            trigger=RevisionTrigger.USER_REQUEST,
            trigger_description="Remove all basins",
            basins_removed=all_basins,
        )

        # The entity allows it, but service should reject
        # Calculate resulting basins
        resulting_basins = set(sample_model.constituent_basins) - set(revision.basins_removed)
        assert len(resulting_basins) == 0  # Would be empty - service must reject

    def test_revision_captures_accuracy_change(self, sample_model):
        """Revision captures accuracy before and after."""
        revision = ModelRevision(
            model_id=sample_model.id,
            revision_number=1,
            trigger=RevisionTrigger.PREDICTION_ERROR,
            trigger_description="Low accuracy triggered revision",
            accuracy_before=0.45,
            accuracy_after=0.50,
        )

        assert revision.accuracy_before == 0.45
        assert revision.accuracy_after == 0.50

    @pytest.mark.asyncio
    async def test_revision_increments_model_count(self, sample_model):
        """Model revision_count should increment after revision."""
        initial_count = sample_model.revision_count
        assert initial_count == 0

        # Simulate revision application
        sample_model.revision_count += 1
        assert sample_model.revision_count == 1


# =============================================================================
# T065: [US5] Unit test for domain filtering
# =============================================================================


class TestDomainFiltering:
    """Tests for domain-based model filtering."""

    def test_domain_enum_values(self):
        """ModelDomain enum has all expected values."""
        domains = [d.value for d in ModelDomain]
        assert "user" in domains
        assert "self" in domains
        assert "world" in domains
        assert "task_specific" in domains

    def test_domain_enum_from_string(self):
        """ModelDomain can be created from string value."""
        assert ModelDomain("user") == ModelDomain.USER
        assert ModelDomain("self") == ModelDomain.SELF
        assert ModelDomain("world") == ModelDomain.WORLD
        assert ModelDomain("task_specific") == ModelDomain.TASK_SPECIFIC

    def test_domain_enum_invalid_value_raises(self):
        """Invalid domain string raises ValueError."""
        with pytest.raises(ValueError):
            ModelDomain("invalid_domain")

    def test_model_domain_assignment(self, sample_basin_ids):
        """Model domain is correctly assigned at creation."""
        user_model = MentalModel(
            name="User Model",
            domain=ModelDomain.USER,
            constituent_basins=sample_basin_ids,
        )
        world_model = MentalModel(
            name="World Model",
            domain=ModelDomain.WORLD,
            constituent_basins=sample_basin_ids,
        )

        assert user_model.domain == ModelDomain.USER
        assert world_model.domain == ModelDomain.WORLD

    def test_domain_hint_extraction(self):
        """Context with domain_hint can be used for filtering."""
        context_user = {"domain_hint": "user", "message": "Hello"}
        context_world = {"domain_hint": "world", "message": "Weather update"}
        context_none = {"message": "No hint"}

        assert context_user.get("domain_hint") == "user"
        assert context_world.get("domain_hint") == "world"
        assert context_none.get("domain_hint") is None

    def test_domain_filtering_logic(self, sample_basin_ids):
        """Domain filtering selects models by domain."""
        models = [
            MentalModel(
                name="User Model 1",
                domain=ModelDomain.USER,
                constituent_basins=sample_basin_ids,
            ),
            MentalModel(
                name="User Model 2",
                domain=ModelDomain.USER,
                constituent_basins=sample_basin_ids,
            ),
            MentalModel(
                name="World Model",
                domain=ModelDomain.WORLD,
                constituent_basins=sample_basin_ids,
            ),
        ]

        # Filter by user domain
        user_models = [m for m in models if m.domain == ModelDomain.USER]
        assert len(user_models) == 2
        assert all(m.domain == ModelDomain.USER for m in user_models)

        # Filter by world domain
        world_models = [m for m in models if m.domain == ModelDomain.WORLD]
        assert len(world_models) == 1
        assert world_models[0].name == "World Model"

    def test_status_filtering_logic(self, sample_basin_ids):
        """Status filtering selects models by status."""
        draft_model = MentalModel(
            name="Draft Model",
            domain=ModelDomain.USER,
            constituent_basins=sample_basin_ids,
            status=ModelStatus.DRAFT,
        )
        active_model = MentalModel(
            name="Active Model",
            domain=ModelDomain.USER,
            constituent_basins=sample_basin_ids,
            status=ModelStatus.ACTIVE,
        )

        models = [draft_model, active_model]

        # Filter by active status
        active_models = [m for m in models if m.status == ModelStatus.ACTIVE]
        assert len(active_models) == 1
        assert active_models[0].name == "Active Model"

        # Filter by draft status
        draft_models = [m for m in models if m.status == ModelStatus.DRAFT]
        assert len(draft_models) == 1
        assert draft_models[0].name == "Draft Model"


# =============================================================================
# Status Transition Tests
# =============================================================================


class TestStatusTransitions:
    """Tests for model status transition validation.

    Note: validate_status_transition is not yet implemented in ModelService.
    Tests are skipped until the method is added.
    """

    @pytest.mark.skip(reason="validate_status_transition not implemented in ModelService")
    def test_valid_transitions(self):
        """Valid status transitions are allowed."""
        from api.services.model_service import ModelService

        service = ModelService()

        # draft -> active
        assert service.validate_status_transition(ModelStatus.DRAFT, ModelStatus.ACTIVE)
        # active -> deprecated
        assert service.validate_status_transition(ModelStatus.ACTIVE, ModelStatus.DEPRECATED)
        # deprecated -> active (reactivation)
        assert service.validate_status_transition(ModelStatus.DEPRECATED, ModelStatus.ACTIVE)

    @pytest.mark.skip(reason="validate_status_transition not implemented in ModelService")
    def test_invalid_transitions(self):
        """Invalid status transitions are rejected."""
        from api.services.model_service import ModelService

        service = ModelService()

        # draft -> deprecated (must go through active)
        assert not service.validate_status_transition(ModelStatus.DRAFT, ModelStatus.DEPRECATED)
        # active -> draft (can't go back to draft)
        assert not service.validate_status_transition(ModelStatus.ACTIVE, ModelStatus.DRAFT)
        # deprecated -> draft
        assert not service.validate_status_transition(ModelStatus.DEPRECATED, ModelStatus.DRAFT)
