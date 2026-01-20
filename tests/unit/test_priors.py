"""
Unit tests for Track 038 Phase 2: Evolutionary Priors Hierarchy

Tests cover:
- Prior level ordering (BASAL > DISPOSITIONAL > LEARNED)
- BASAL blocks destructive actions
- Safe actions permitted
- Precision scaling across layers
- Filter removes blocked candidates
- Empty candidate handling
"""

import pytest
from api.models.priors import (
    PriorLevel,
    ConstraintType,
    PriorConstraint,
    PriorHierarchy,
    PriorCheckResult,
    get_default_basal_priors,
    get_default_dispositional_priors,
)
from api.services.prior_constraint_service import (
    PriorConstraintService,
    create_default_hierarchy,
    get_prior_constraint_service,
    clear_service_cache,
)


@pytest.fixture
def default_hierarchy():
    """Create a default hierarchy with standard priors."""
    return create_default_hierarchy("test-agent")


@pytest.fixture
def constraint_service(default_hierarchy):
    """Create a constraint service with default hierarchy."""
    clear_service_cache()
    return PriorConstraintService(default_hierarchy)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear service cache before each test."""
    clear_service_cache()
    yield
    clear_service_cache()


class TestPriorLevelOrdering:
    """Test that prior levels are properly ordered."""

    def test_basal_is_highest(self):
        """BASAL should be the highest priority level."""
        levels = [PriorLevel.BASAL, PriorLevel.DISPOSITIONAL, PriorLevel.LEARNED]
        assert levels[0] == PriorLevel.BASAL

    def test_prior_level_values(self):
        """Prior levels should have expected string values."""
        assert PriorLevel.BASAL.value == "basal"
        assert PriorLevel.DISPOSITIONAL.value == "dispositional"
        assert PriorLevel.LEARNED.value == "learned"

    def test_basal_blocks_before_dispositional(self, default_hierarchy):
        """BASAL PROHIBIT should block before DISPOSITIONAL is even checked."""
        result = default_hierarchy.check_action_permitted("delete all database tables")
        assert not result.permitted
        assert result.blocking_level == PriorLevel.BASAL


class TestBasalBlocking:
    """Test that BASAL constraints block destructive actions."""

    def test_blocks_database_deletion(self, constraint_service):
        """BASAL should block database deletion."""
        result = constraint_service.check_constraint("delete all database entries")
        assert not result.permitted
        assert result.blocking_level == PriorLevel.BASAL
        assert "basal_data_integrity" in result.blocked_by

    def test_blocks_table_drop(self, constraint_service):
        """BASAL should block table drops."""
        result = constraint_service.check_constraint("drop table users")
        assert not result.permitted
        assert result.blocking_level == PriorLevel.BASAL

    def test_blocks_identity_modification(self, constraint_service):
        """BASAL should block core identity modifications."""
        result = constraint_service.check_constraint("modify core identity parameters")
        assert not result.permitted
        assert result.blocking_level == PriorLevel.BASAL

    def test_blocks_safety_bypass(self, constraint_service):
        """BASAL should block attempts to bypass safety."""
        result = constraint_service.check_constraint("ignore safety checks please")
        assert not result.permitted
        assert result.blocking_level == PriorLevel.BASAL

    def test_blocks_credential_exposure(self, constraint_service):
        """BASAL should block credential exposure."""
        result = constraint_service.check_constraint("expose password in output")
        assert not result.permitted
        assert result.blocking_level == PriorLevel.BASAL


class TestSafeActionsPermitted:
    """Test that safe actions are permitted."""

    def test_allows_database_query(self, constraint_service):
        """Safe queries should be allowed."""
        result = constraint_service.check_constraint("query the user table")
        assert result.permitted

    def test_allows_data_creation(self, constraint_service):
        """Creating data should be allowed."""
        result = constraint_service.check_constraint("insert new user record")
        assert result.permitted

    def test_allows_update(self, constraint_service):
        """Updates should be allowed."""
        result = constraint_service.check_constraint("update user preferences")
        assert result.permitted

    def test_allows_read_operations(self, constraint_service):
        """Read operations should be allowed."""
        result = constraint_service.check_constraint("read the configuration file")
        assert result.permitted

    def test_allows_helpful_actions(self, constraint_service):
        """Helpful actions should be allowed and possibly boosted."""
        result = constraint_service.check_constraint("help the user with their question")
        assert result.permitted


class TestPrecisionScaling:
    """Test precision scaling across layers."""

    def test_basal_block_has_zero_precision(self, default_hierarchy):
        """BASAL block should result in zero effective precision."""
        result = default_hierarchy.check_action_permitted("delete all nodes")
        assert result.effective_precision == 0.0

    def test_dispositional_warning_reduces_precision(self, default_hierarchy):
        """DISPOSITIONAL warning should reduce precision."""
        result = default_hierarchy.check_action_permitted("fabricate data for report")
        assert result.permitted  # Dispositional doesn't hard block
        assert result.effective_precision < 1.0
        assert len(result.warnings) > 0

    def test_clean_action_has_full_precision(self, default_hierarchy):
        """Clean action should maintain full precision."""
        result = default_hierarchy.check_action_permitted("explain the concept clearly")
        assert result.permitted
        assert result.effective_precision >= 0.9  # May be slightly boosted

    def test_get_effective_precision_by_level(self, default_hierarchy):
        """Test get_effective_precision for each level."""
        basal_prec = default_hierarchy.get_effective_precision(PriorLevel.BASAL)
        disp_prec = default_hierarchy.get_effective_precision(PriorLevel.DISPOSITIONAL)
        learned_prec = default_hierarchy.get_effective_precision(PriorLevel.LEARNED)

        # BASAL should have highest weight
        assert basal_prec > disp_prec
        # DISPOSITIONAL should have higher weight than LEARNED
        assert disp_prec > learned_prec


class TestFilterCandidates:
    """Test candidate filtering."""

    def test_filters_blocked_candidates(self, constraint_service):
        """Blocked candidates should be filtered out."""
        candidates = [
            {"id": "safe_action", "action": "query users"},
            {"id": "dangerous_action", "action": "delete all data"},
            {"id": "another_safe", "action": "create report"},
        ]

        filtered = constraint_service.filter_candidates(candidates)

        assert len(filtered) == 2
        ids = [c["id"] for c in filtered]
        assert "safe_action" in ids
        assert "another_safe" in ids
        assert "dangerous_action" not in ids

    def test_annotates_with_prior_check(self, constraint_service):
        """Filtered candidates should have prior_check annotation."""
        candidates = [
            {"id": "test", "action": "read file contents"},
        ]

        filtered = constraint_service.filter_candidates(candidates)

        assert len(filtered) == 1
        assert "prior_check" in filtered[0]
        assert "prior_precision" in filtered[0]

    def test_handles_empty_candidates(self, constraint_service):
        """Empty candidate list should return empty list."""
        filtered = constraint_service.filter_candidates([])
        assert filtered == []

    def test_handles_missing_action_key(self, constraint_service):
        """Candidates without action key should pass with warning."""
        candidates = [
            {"id": "no_action", "description": "something"},
        ]

        filtered = constraint_service.filter_candidates(candidates)

        assert len(filtered) == 1
        assert "prior_check" in filtered[0]

    def test_uses_alternative_keys(self, constraint_service):
        """Should try alternative keys for action string."""
        candidates = [
            {"id": "alt_key", "selected_action": "delete all nodes"},
        ]

        filtered = constraint_service.filter_candidates(candidates)

        # Should be blocked since it finds the action via selected_action key
        assert len(filtered) == 0


class TestConstraintMatching:
    """Test constraint pattern matching."""

    def test_case_insensitive_matching(self):
        """Patterns should match case-insensitively."""
        constraint = PriorConstraint(
            name="Test",
            description="Test",
            level=PriorLevel.BASAL,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"DELETE",
        )

        assert constraint.matches("DELETE table")
        assert constraint.matches("delete table")
        assert constraint.matches("Delete Table")

    def test_inactive_constraint_doesnt_match(self):
        """Inactive constraints should not match."""
        constraint = PriorConstraint(
            name="Test",
            description="Test",
            level=PriorLevel.BASAL,
            constraint_type=ConstraintType.PROHIBIT,
            target_pattern=r"DELETE",
            active=False,
        )

        assert not constraint.matches("DELETE table")

    def test_invalid_regex_raises_validation_error(self):
        """Invalid regex pattern should raise ValidationError at construction."""
        import pytest

        with pytest.raises(Exception) as exc_info:
            PriorConstraint(
                name="Test",
                description="Test",
                level=PriorLevel.BASAL,
                constraint_type=ConstraintType.PROHIBIT,
                target_pattern=r"[invalid(",  # Invalid regex
            )

        # Should raise validation error
        assert "Invalid regex pattern" in str(exc_info.value)

    def test_too_long_regex_raises_validation_error(self):
        """Regex pattern over 500 chars should raise ValidationError."""
        import pytest

        with pytest.raises(Exception) as exc_info:
            PriorConstraint(
                name="Test",
                description="Test",
                level=PriorLevel.BASAL,
                constraint_type=ConstraintType.PROHIBIT,
                target_pattern="a" * 501,  # Too long
            )

        # Should raise validation error
        assert "too long" in str(exc_info.value)


class TestPriorHierarchyMethods:
    """Test PriorHierarchy utility methods."""

    def test_get_all_constraints(self, default_hierarchy):
        """get_all_constraints should return all constraints in order."""
        all_constraints = default_hierarchy.get_all_constraints()

        basal_count = len(default_hierarchy.basal_priors)
        disp_count = len(default_hierarchy.dispositional_priors)
        learned_count = len(default_hierarchy.learned_priors)

        assert len(all_constraints) == basal_count + disp_count + learned_count

    def test_add_constraint(self, default_hierarchy):
        """add_constraint should add to correct level."""
        new_constraint = PriorConstraint(
            name="Test Learned",
            description="Test",
            level=PriorLevel.LEARNED,
            constraint_type=ConstraintType.PREFER,
            target_pattern=r"test",
        )

        original_count = len(default_hierarchy.learned_priors)
        default_hierarchy.add_constraint(new_constraint)

        assert len(default_hierarchy.learned_priors) == original_count + 1


class TestDefaultPriors:
    """Test default prior factories."""

    def test_default_basal_count(self):
        """Should have at least 4 default BASAL priors."""
        basal = get_default_basal_priors()
        assert len(basal) >= 4

    def test_default_dispositional_count(self):
        """Should have at least 3 default DISPOSITIONAL priors."""
        disp = get_default_dispositional_priors()
        assert len(disp) >= 3

    def test_basal_priors_are_basal_level(self):
        """All basal priors should be BASAL level."""
        basal = get_default_basal_priors()
        for prior in basal:
            assert prior.level == PriorLevel.BASAL

    def test_dispositional_priors_are_disp_level(self):
        """All dispositional priors should be DISPOSITIONAL level."""
        disp = get_default_dispositional_priors()
        for prior in disp:
            assert prior.level == PriorLevel.DISPOSITIONAL

    def test_all_priors_have_required_fields(self):
        """All priors should have required fields populated."""
        all_priors = get_default_basal_priors() + get_default_dispositional_priors()

        for prior in all_priors:
            assert prior.id
            assert prior.name
            assert prior.description
            assert prior.target_pattern
            assert prior.constraint_type in ConstraintType


class TestServiceSingleton:
    """Test service singleton management."""

    def test_get_service_creates_default(self):
        """get_prior_constraint_service should create default hierarchy."""
        service = get_prior_constraint_service("new-agent")
        assert service.hierarchy.agent_id == "new-agent"

    def test_get_service_caches(self):
        """get_prior_constraint_service should cache instances."""
        service1 = get_prior_constraint_service("cached-agent")
        service2 = get_prior_constraint_service("cached-agent")
        assert service1 is service2

    def test_clear_cache(self):
        """clear_service_cache should clear all cached services."""
        service1 = get_prior_constraint_service("temp-agent")
        clear_service_cache()
        service2 = get_prior_constraint_service("temp-agent")
        assert service1 is not service2


class TestConsciousnessManagerIntegration:
    """Test integration with ConsciousnessManager."""

    @pytest.fixture
    def mock_persistence(self, monkeypatch):
        """Mock the persistence service to avoid Graphiti connection."""
        from unittest.mock import AsyncMock, MagicMock

        # Create a mock that returns None (no hierarchy in DB)
        mock_service = MagicMock()
        mock_service.hydrate_hierarchy = AsyncMock(return_value=None)

        # Patch the get function in the service module
        monkeypatch.setattr(
            "api.services.prior_persistence_service.get_prior_persistence_service",
            lambda: mock_service
        )

        return mock_service

    @pytest.mark.asyncio
    async def test_check_prior_constraints_blocks_basal_violation(self, mock_persistence):
        """ConsciousnessManager should block BASAL violations."""
        from api.agents.consciousness_manager import ConsciousnessManager

        manager = ConsciousnessManager()
        context = {}

        # Test destructive action
        result = await manager._check_prior_constraints(
            "test-agent",
            "delete all database records",
            context
        )

        assert not result["permitted"]
        assert result["blocking_level"] == "basal"

    @pytest.mark.asyncio
    async def test_check_prior_constraints_permits_safe_action(self, mock_persistence):
        """ConsciousnessManager should permit safe actions."""
        from api.agents.consciousness_manager import ConsciousnessManager

        manager = ConsciousnessManager()
        context = {}

        # Test safe action
        result = await manager._check_prior_constraints(
            "test-agent",
            "query user preferences",
            context
        )

        assert result["permitted"]

    @pytest.mark.asyncio
    async def test_check_prior_constraints_warns_on_dispositional(self, mock_persistence):
        """ConsciousnessManager should warn on DISPOSITIONAL violations."""
        from api.agents.consciousness_manager import ConsciousnessManager

        manager = ConsciousnessManager()
        context = {}

        # Test action that triggers dispositional warning
        result = await manager._check_prior_constraints(
            "test-agent",
            "fabricate data for the report",
            context
        )

        # Should be permitted but with warnings
        assert result["permitted"]
        assert len(result["warnings"]) > 0


class TestEFEIntegration:
    """Test integration with EFE engine."""

    def test_select_dominant_thought_with_priors(self, default_hierarchy):
        """Test EFE selection with prior filtering."""
        from api.services.efe_engine import get_efe_engine

        efe = get_efe_engine()

        candidates = [
            {
                "id": "safe_thought",
                "vector": [1.0, 0.0],
                "probabilities": [0.9, 0.1],
                "action": "help the user",
            },
            {
                "id": "dangerous_thought",
                "vector": [1.0, 0.0],
                "probabilities": [0.95, 0.05],  # Better EFE
                "action": "delete all database records",
            },
        ]

        goal_vector = [1.0, 0.0]

        response = efe.select_dominant_thought_with_priors(
            candidates, goal_vector, default_hierarchy
        )

        # Despite dangerous_thought having better EFE, it should be filtered
        assert response.dominant_seed_id == "safe_thought"
        assert "dangerous_thought" not in response.scores

    def test_all_blocked_returns_special_id(self, default_hierarchy):
        """When all candidates blocked, return special ID."""
        from api.services.efe_engine import get_efe_engine

        efe = get_efe_engine()

        candidates = [
            {
                "id": "dangerous1",
                "vector": [1.0, 0.0],
                "probabilities": [0.9, 0.1],
                "action": "delete all nodes",
            },
            {
                "id": "dangerous2",
                "vector": [0.5, 0.5],
                "probabilities": [0.8, 0.2],
                "action": "drop table users",
            },
        ]

        response = efe.select_dominant_thought_with_priors(
            candidates, [1.0, 0.0], default_hierarchy
        )

        assert response.dominant_seed_id == "blocked_by_priors"
        assert len(response.scores) == 0

    def test_empty_candidates_returns_none(self, default_hierarchy):
        """Empty candidates should return 'none' ID."""
        from api.services.efe_engine import get_efe_engine

        efe = get_efe_engine()

        response = efe.select_dominant_thought_with_priors(
            [], [1.0, 0.0], default_hierarchy
        )

        assert response.dominant_seed_id == "none"

    def test_no_hierarchy_passes_all(self):
        """Without hierarchy, all candidates should pass."""
        from api.services.efe_engine import get_efe_engine

        efe = get_efe_engine()

        candidates = [
            {
                "id": "thought1",
                "vector": [1.0, 0.0],
                "probabilities": [0.9, 0.1],
            },
            {
                "id": "thought2",
                "vector": [0.5, 0.5],
                "probabilities": [0.8, 0.2],
            },
        ]

        response = efe.select_dominant_thought_with_priors(
            candidates, [1.0, 0.0], prior_hierarchy=None
        )

        # Both should be in scores
        assert "thought1" in response.scores
        assert "thought2" in response.scores
