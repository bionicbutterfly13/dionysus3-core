"""
Contract Tests for Mental Model MCP Tools
Feature: 005-mental-models
Tasks: T017 (stub), T019-T020 (US1), T056 (US4)

Tests MCP tool contracts match specifications in contracts/mcp-tools.md.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from api.models.mental_model import (
    CreateModelRequest,
    CreateModelToolResponse,
    GetModelToolResponse,
    ListModelsToolResponse,
    ModelDomain,
    ModelResponse,
    ModelStatus,
    PredictionTemplate,
    ReviseModelRequest,
    ReviseModelToolResponse,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_basin_ids():
    """Sample basin UUIDs for testing."""
    return [
        UUID("550e8400-e29b-41d4-a716-446655440001"),
        UUID("550e8400-e29b-41d4-a716-446655440002"),
    ]


@pytest.fixture
def valid_create_request(sample_basin_ids):
    """Valid CreateModelRequest matching contract."""
    return CreateModelRequest(
        name="User Emotional Patterns",
        domain=ModelDomain.USER,
        basin_ids=sample_basin_ids,
        description="Predicts user emotional states based on conversation patterns",
        prediction_templates=[
            PredictionTemplate(
                trigger="user mentions work stress",
                predict="likely experiencing anxiety about performance",
                suggest="acknowledge feelings before problem-solving",
            )
        ],
    )


# =============================================================================
# T017: Schema Validation Tests
# =============================================================================


class TestCreateModelRequestSchema:
    """Tests for CreateModelRequest schema compliance."""

    def test_valid_request(self, valid_create_request):
        """Valid request passes validation."""
        assert valid_create_request.name == "User Emotional Patterns"
        assert valid_create_request.domain == ModelDomain.USER
        assert len(valid_create_request.basin_ids) == 2

    def test_requires_name(self, sample_basin_ids):
        """Name is required."""
        with pytest.raises(ValueError):
            CreateModelRequest(
                domain=ModelDomain.USER,
                basin_ids=sample_basin_ids,
            )

    def test_requires_domain(self, sample_basin_ids):
        """Domain is required."""
        with pytest.raises(ValueError):
            CreateModelRequest(
                name="Test",
                basin_ids=sample_basin_ids,
            )

    def test_requires_basin_ids(self):
        """At least one basin_id is required."""
        with pytest.raises(ValueError):
            CreateModelRequest(
                name="Test",
                domain=ModelDomain.USER,
                basin_ids=[],
            )

    def test_domain_enum_validation(self, sample_basin_ids):
        """Domain must be valid enum value."""
        with pytest.raises(ValueError):
            CreateModelRequest(
                name="Test",
                domain="invalid_domain",  # type: ignore
                basin_ids=sample_basin_ids,
            )


class TestCreateModelToolResponseSchema:
    """Tests for CreateModelToolResponse schema compliance."""

    def test_success_response(self):
        """Success response has model_id and message."""
        response = CreateModelToolResponse(
            success=True,
            model_id=uuid4(),
            message="Model 'Test' created with 2 basins",
        )
        assert response.success is True
        assert response.model_id is not None
        assert "created" in response.message

    def test_failure_response(self):
        """Failure response has error message."""
        response = CreateModelToolResponse(
            success=False,
            message="One or more basin IDs do not exist",
        )
        assert response.success is False
        assert response.model_id is None


class TestListModelsToolResponseSchema:
    """Tests for ListModelsToolResponse schema compliance."""

    def test_empty_list(self):
        """Empty list response is valid."""
        response = ListModelsToolResponse(models=[], total=0)
        assert response.models == []
        assert response.total == 0

    def test_list_with_models(self):
        """List with models includes all required fields."""
        model_response = ModelResponse(
            id=uuid4(),
            name="Test Model",
            domain=ModelDomain.USER,
            status=ModelStatus.ACTIVE,
            prediction_accuracy=0.72,
            basin_count=2,
            revision_count=3,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        response = ListModelsToolResponse(models=[model_response], total=1)
        assert len(response.models) == 1
        assert response.total == 1


# =============================================================================
# T019: [US1] Contract test for create_model MCP tool
# =============================================================================


class TestCreateModelMCPTool:
    """Contract tests for create_model MCP tool."""

    def test_create_model_success_response_schema(self):
        """Success response has success=True, model_id, and message."""
        # Contract: {"success": true, "model_id": "uuid", "message": "..."}
        response = CreateModelToolResponse(
            success=True,
            model_id=uuid4(),
            message="Model 'Test' created with 2 basins",
        )
        assert response.success is True
        assert response.model_id is not None
        assert response.message is not None
        assert "created" in response.message.lower()

    def test_create_model_failure_response_schema(self):
        """Failure response has success=False and error message."""
        # Contract: {"success": false, "message": "error description"}
        response = CreateModelToolResponse(
            success=False,
            model_id=None,
            message="One or more basin IDs do not exist",
        )
        assert response.success is False
        assert response.model_id is None
        assert response.message is not None

    def test_create_model_tool_signature(self):
        """create_model MCP tool has correct parameter signature."""
        from dionysus_mcp.tools.models import create_mental_model_tool
        import inspect
        sig = inspect.signature(create_mental_model_tool)
        params = list(sig.parameters.keys())
        # Required: name, domain, basin_ids
        assert "name" in params
        assert "domain" in params
        assert "basin_ids" in params
        # Optional: description, prediction_templates
        assert "description" in params
        assert "prediction_templates" in params
        # Check defaults
        assert sig.parameters["description"].default is None
        assert sig.parameters["prediction_templates"].default is None

    def test_create_model_domain_enum_values(self):
        """Domain parameter accepts valid enum string values."""
        # Contract: domain must be one of user, self, world, task_specific
        valid_domains = ["user", "self", "world", "task_specific"]
        for domain in valid_domains:
            model_domain = ModelDomain(domain)
            assert model_domain.value == domain


# =============================================================================
# T020: [US1] Contract test for list_models MCP tool
# =============================================================================


class TestListModelsMCPTool:
    """Contract tests for list_models MCP tool."""

    def test_list_models_response_schema_has_models_key(self):
        """list_models response must have 'models' key."""
        # Contract: Response must have {"models": [...], "total": n}
        response = ListModelsToolResponse(models=[], total=0)
        assert hasattr(response, "models")
        assert isinstance(response.models, list)

    def test_list_models_response_schema_has_total_key(self):
        """list_models response must have 'total' key."""
        response = ListModelsToolResponse(models=[], total=5)
        assert hasattr(response, "total")
        assert isinstance(response.total, int)

    def test_list_models_model_response_has_required_fields(self):
        """Each model in response must have required fields per contract."""
        # Contract: id, name, domain, status, prediction_accuracy, basin_count, revision_count
        model = ModelResponse(
            id=uuid4(),
            name="Test",
            domain=ModelDomain.USER,
            status=ModelStatus.ACTIVE,
            prediction_accuracy=0.75,
            basin_count=2,
            revision_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert model.id is not None
        assert model.name == "Test"
        assert model.domain == ModelDomain.USER
        assert model.status == ModelStatus.ACTIVE
        assert model.prediction_accuracy == 0.75
        assert model.basin_count == 2
        assert model.revision_count == 0

    def test_list_models_domain_filter_valid_values(self):
        """Domain filter accepts valid enum values."""
        for domain in ["user", "self", "world", "task_specific"]:
            assert ModelDomain(domain) is not None

    def test_list_models_domain_filter_invalid_raises(self):
        """Domain filter rejects invalid values."""
        with pytest.raises(ValueError):
            ModelDomain("invalid_domain")

    def test_list_models_status_filter_valid_values(self):
        """Status filter accepts valid enum values."""
        for status in ["draft", "active", "deprecated"]:
            assert ModelStatus(status) is not None

    def test_list_models_status_filter_invalid_raises(self):
        """Status filter rejects invalid values."""
        with pytest.raises(ValueError):
            ModelStatus("invalid_status")

    def test_list_models_limit_default(self):
        """Default limit per contract is 20."""
        # This tests the contract expectation, not implementation
        from dionysus_mcp.tools.models import list_mental_models_tool
        import inspect
        sig = inspect.signature(list_mental_models_tool)
        assert sig.parameters["limit"].default == 20

    def test_list_models_offset_default(self):
        """Default offset per contract is 0."""
        from dionysus_mcp.tools.models import list_mental_models_tool
        import inspect
        sig = inspect.signature(list_mental_models_tool)
        assert sig.parameters["offset"].default == 0


# =============================================================================
# T056: [US4] Contract test for model creation validation (invalid basins)
# =============================================================================


class TestModelCreationValidation:
    """Contract tests for model creation validation."""

    def test_create_model_request_requires_valid_uuids(self, sample_basin_ids):
        """CreateModelRequest requires valid UUIDs for basin_ids."""
        # Valid UUIDs should work
        request = CreateModelRequest(
            name="Test",
            domain=ModelDomain.USER,
            basin_ids=sample_basin_ids,
        )
        assert len(request.basin_ids) == 2
        for bid in request.basin_ids:
            assert isinstance(bid, UUID)

    def test_create_model_request_requires_at_least_one_basin(self):
        """CreateModelRequest requires at least one basin_id."""
        with pytest.raises(ValueError):
            CreateModelRequest(
                name="Test",
                domain=ModelDomain.USER,
                basin_ids=[],  # Empty list should fail
            )

    def test_prediction_template_has_required_fields(self):
        """PredictionTemplate requires trigger, predict; suggest optional."""
        template = PredictionTemplate(
            trigger="user mentions stress",
            predict="likely anxious",
            suggest="acknowledge feelings",
        )
        assert template.trigger == "user mentions stress"
        assert template.predict == "likely anxious"
        assert template.suggest == "acknowledge feelings"

    def test_prediction_template_missing_trigger_fails(self):
        """PredictionTemplate without trigger should fail."""
        with pytest.raises(ValueError):
            PredictionTemplate(
                predict="likely anxious",
                suggest="acknowledge feelings",
            )

    def test_prediction_template_missing_predict_fails(self):
        """PredictionTemplate without predict should fail."""
        with pytest.raises(ValueError):
            PredictionTemplate(
                trigger="user mentions stress",
                suggest="acknowledge feelings",
            )

    def test_prediction_template_suggest_optional(self):
        """PredictionTemplate allows omit suggest (optional)."""
        template = PredictionTemplate(
            trigger="user mentions stress",
            predict="likely anxious",
        )
        assert template.trigger == "user mentions stress"
        assert template.predict == "likely anxious"
        assert template.suggest is None

    def test_create_model_error_message_format(self):
        """Error responses should contain descriptive messages."""
        # Contract: error message should describe what went wrong
        error_response = CreateModelToolResponse(
            success=False,
            model_id=None,
            message="Invalid basin IDs: [550e8400-e29b-41d4-a716-446655440001]",
        )
        assert "Invalid basin IDs" in error_response.message
        assert error_response.success is False


# =============================================================================
# ReviseModel Tool Tests
# =============================================================================


class TestReviseModelMCPTool:
    """Contract tests for revise_model MCP tool."""

    @pytest.mark.skip(reason="Implement after MCP tool is created")
    async def test_revise_model_returns_revision_id(self):
        """revise_model returns revision_id on success."""
        # Expected: {"success": true, "revision_id": "uuid", "message": "...", "new_accuracy": 0.72}
        pass

    @pytest.mark.skip(reason="Implement after MCP tool is created")
    async def test_revise_model_not_found_error(self):
        """revise_model returns NOT_FOUND error for invalid model_id."""
        pass

    @pytest.mark.skip(reason="Implement after MCP tool is created")
    async def test_revise_model_would_empty_error(self):
        """revise_model returns WOULD_EMPTY error when removing all basins."""
        pass
