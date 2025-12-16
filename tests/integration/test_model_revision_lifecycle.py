"""
Integration Tests for Model Revision Lifecycle
Feature: 005-mental-models
Task: T045 - Model revision lifecycle tests

Tests the complete revision workflow from flagging to application.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from api.models.mental_model import (
    CreateModelRequest,
    MentalModel,
    ModelDomain,
    ModelStatus,
    PredictionTemplate,
    ReviseModelRequest,
    RevisionTrigger,
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
    """Create a test model for revision testing."""
    request = CreateModelRequest(
        name=f"Revision Test Model {uuid4().hex[:8]}",
        domain=ModelDomain.USER,
        basin_ids=test_basins,
        description="Model for revision lifecycle testing",
    )
    model = await model_service.create_model(request)
    return model


# =============================================================================
# T045: Model Revision Lifecycle Tests
# =============================================================================


class TestModelRevisionLifecycle:
    """Integration tests for the complete model revision lifecycle."""

    @pytest.mark.asyncio
    async def test_apply_revision_adds_basin(self, model_service, test_model, test_basins):
        """Revision can add a new basin to a model."""
        new_basin = uuid4()  # Simulated new basin

        # Get initial basin count
        initial_basins = len(test_model.constituent_basins)

        # Apply revision to add basin
        revision_request = ReviseModelRequest(
            trigger_description="Adding new memory basin",
            add_basins=[new_basin],
        )

        revision = await model_service.apply_revision(test_model.id, revision_request)

        # Verify revision created
        assert revision is not None
        assert revision.model_id == test_model.id
        assert new_basin in revision.basins_added
        assert len(revision.basins_removed) == 0

        # Verify model updated
        updated_model = await model_service.get_model(test_model.id)
        assert len(updated_model.constituent_basins) == initial_basins + 1
        assert new_basin in updated_model.constituent_basins

    @pytest.mark.asyncio
    async def test_apply_revision_removes_basin(self, model_service, test_model):
        """Revision can remove a basin from a model (if not the last one)."""
        # Get a basin to remove (first one)
        basin_to_remove = test_model.constituent_basins[0]
        initial_count = len(test_model.constituent_basins)

        # Must have more than one basin
        assert initial_count > 1

        # Apply revision to remove basin
        revision_request = ReviseModelRequest(
            trigger_description="Removing outdated basin",
            remove_basins=[basin_to_remove],
        )

        revision = await model_service.apply_revision(test_model.id, revision_request)

        # Verify revision created
        assert revision is not None
        assert basin_to_remove in revision.basins_removed
        assert len(revision.basins_added) == 0

        # Verify model updated
        updated_model = await model_service.get_model(test_model.id)
        assert len(updated_model.constituent_basins) == initial_count - 1
        assert basin_to_remove not in updated_model.constituent_basins

    @pytest.mark.asyncio
    async def test_apply_revision_prevents_empty_model(self, model_service, test_basins):
        """Cannot apply revision that removes all basins."""
        # Create model with single basin
        single_basin = test_basins[:1]
        request = CreateModelRequest(
            name="Single Basin Model",
            domain=ModelDomain.USER,
            basin_ids=single_basin,
        )
        model = await model_service.create_model(request)

        # Try to remove the only basin
        revision_request = ReviseModelRequest(
            trigger_description="Remove all basins",
            remove_basins=single_basin,
        )

        with pytest.raises(ValueError, match="empty"):
            await model_service.apply_revision(model.id, revision_request)

    @pytest.mark.asyncio
    async def test_apply_revision_increments_count(self, model_service, test_model):
        """Applying revision increments model's revision_count."""
        initial_count = test_model.revision_count

        # Apply revision
        revision_request = ReviseModelRequest(
            trigger_description="Test revision",
            add_basins=[uuid4()],
        )

        await model_service.apply_revision(test_model.id, revision_request)

        # Verify count incremented
        updated = await model_service.get_model(test_model.id)
        assert updated.revision_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_apply_revision_records_accuracy(self, model_service, test_model):
        """Revision records accuracy before and after."""
        # Apply revision
        revision_request = ReviseModelRequest(
            trigger_description="Test revision with accuracy tracking",
            add_basins=[uuid4()],
        )

        revision = await model_service.apply_revision(test_model.id, revision_request)

        # Verify accuracy captured
        assert revision.accuracy_before is not None
        # accuracy_after is typically set after new predictions

    @pytest.mark.asyncio
    async def test_revision_history_maintained(self, model_service, test_model):
        """Multiple revisions maintain history."""
        # Apply multiple revisions
        for i in range(3):
            revision_request = ReviseModelRequest(
                trigger_description=f"Revision {i + 1}",
                add_basins=[uuid4()],
            )
            await model_service.apply_revision(test_model.id, revision_request)

        # Get revision history
        revisions = await model_service.get_revision_history(test_model.id)

        # Verify all revisions recorded
        assert len(revisions) >= 3

        # Verify revision numbers
        revision_numbers = [r.revision_number for r in revisions]
        assert 1 in revision_numbers
        assert 2 in revision_numbers
        assert 3 in revision_numbers

    @pytest.mark.asyncio
    async def test_revision_on_nonexistent_model(self, model_service):
        """Revision on nonexistent model raises error."""
        fake_id = uuid4()

        revision_request = ReviseModelRequest(
            trigger_description="Test",
            add_basins=[uuid4()],
        )

        with pytest.raises(ValueError, match="not found"):
            await model_service.apply_revision(fake_id, revision_request)


class TestRevisionTriggers:
    """Tests for different revision trigger types."""

    @pytest.mark.asyncio
    async def test_prediction_error_trigger(self, model_service, test_model):
        """Revision can be triggered by prediction error threshold."""
        revision_request = ReviseModelRequest(
            trigger_description="Accuracy dropped below 0.4",
            add_basins=[uuid4()],
        )

        revision = await model_service.apply_revision(test_model.id, revision_request)

        # Trigger is inferred as USER_REQUEST for manual revisions
        assert revision.trigger == RevisionTrigger.USER_REQUEST

    @pytest.mark.asyncio
    async def test_user_request_trigger(self, model_service, test_model):
        """User-initiated revision has correct trigger type."""
        revision_request = ReviseModelRequest(
            trigger_description="User requested model refinement",
            remove_basins=[test_model.constituent_basins[0]],
            add_basins=[uuid4()],
        )

        revision = await model_service.apply_revision(test_model.id, revision_request)

        assert revision.trigger == RevisionTrigger.USER_REQUEST


class TestRevisionRollback:
    """Tests for revision rollback functionality."""

    @pytest.mark.asyncio
    async def test_get_revision_history_ordered(self, model_service, test_model):
        """Revision history is returned in chronological order."""
        # Apply revisions
        for i in range(2):
            await model_service.apply_revision(
                test_model.id,
                ReviseModelRequest(
                    trigger_description=f"Revision {i}",
                    add_basins=[uuid4()],
                ),
            )

        revisions = await model_service.get_revision_history(test_model.id)

        # Should be ordered by revision_number
        numbers = [r.revision_number for r in revisions]
        assert numbers == sorted(numbers)

    @pytest.mark.asyncio
    async def test_revision_captures_state_snapshot(self, model_service, test_model):
        """Each revision captures the state at revision time."""
        initial_basins = set(test_model.constituent_basins)

        new_basin = uuid4()
        revision = await model_service.apply_revision(
            test_model.id,
            ReviseModelRequest(
                trigger_description="Add basin",
                add_basins=[new_basin],
            ),
        )

        # Basins_added should reflect the change
        assert new_basin in revision.basins_added
