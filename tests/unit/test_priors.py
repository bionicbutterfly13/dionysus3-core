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


# =============================================================================
# Track 038 Phase 4: Biographical Constraint Propagation Tests
# =============================================================================


class TestBiographicalPriorMerging:
    """Tests for merging biographical priors into the LEARNED layer."""

    def test_merge_biographical_priors_adds_to_learned(self):
        """Biographical priors should be added to LEARNED layer."""
        hierarchy = create_default_hierarchy("test-agent")
        initial_learned_count = len(hierarchy.learned_priors)

        bio_priors = [
            PriorConstraint(
                id="bio_theme_1",
                name="Unresolved Theme: Authenticity",
                description="Prefer actions that address authenticity questions",
                level=PriorLevel.LEARNED,
                precision=0.6,
                constraint_type=ConstraintType.PREFER,
                target_pattern=r"authenticity|genuine|real",
                metadata={"source": "biographical"},
            )
        ]

        added = hierarchy.merge_biographical_priors(bio_priors)

        assert added == 1
        assert len(hierarchy.learned_priors) == initial_learned_count + 1
        assert any(p.id == "bio_theme_1" for p in hierarchy.learned_priors)

    def test_merge_biographical_priors_forces_learned_level(self):
        """Even if bio prior has different level, it should be forced to LEARNED."""
        hierarchy = create_default_hierarchy("test-agent")

        bio_priors = [
            PriorConstraint(
                id="bio_forced_level",
                name="Should Be Learned",
                description="Even if specified as BASAL",
                level=PriorLevel.BASAL,  # Wrong level
                precision=0.5,
                constraint_type=ConstraintType.PREFER,
                target_pattern=r"test",
                metadata={"source": "biographical"},
            )
        ]

        hierarchy.merge_biographical_priors(bio_priors)

        merged = next(p for p in hierarchy.learned_priors if p.id == "bio_forced_level")
        assert merged.level == PriorLevel.LEARNED

    def test_merge_biographical_priors_skips_duplicates(self):
        """Should not add duplicate biographical priors."""
        hierarchy = create_default_hierarchy("test-agent")

        bio_priors = [
            PriorConstraint(
                id="bio_dup_test",
                name="Test Prior",
                description="First add",
                level=PriorLevel.LEARNED,
                precision=0.5,
                constraint_type=ConstraintType.PREFER,
                target_pattern=r"test",
                metadata={"source": "biographical"},
            )
        ]

        added_first = hierarchy.merge_biographical_priors(bio_priors)
        added_second = hierarchy.merge_biographical_priors(bio_priors)

        assert added_first == 1
        assert added_second == 0  # Duplicate not added

    def test_clear_biographical_priors(self):
        """Should remove only biographical priors, not other learned priors."""
        hierarchy = create_default_hierarchy("test-agent")

        # Add a non-biographical learned prior
        non_bio = PriorConstraint(
            id="non_bio_prior",
            name="Non-Bio Prior",
            description="Should remain after clear",
            level=PriorLevel.LEARNED,
            precision=0.5,
            constraint_type=ConstraintType.PREFER,
            target_pattern=r"keep",
            metadata={"source": "user_defined"},
        )
        hierarchy.add_constraint(non_bio)

        # Add biographical priors
        bio_priors = [
            PriorConstraint(
                id="bio_to_remove",
                name="Bio Prior",
                description="Should be removed",
                level=PriorLevel.LEARNED,
                precision=0.5,
                constraint_type=ConstraintType.PREFER,
                target_pattern=r"remove",
                metadata={"source": "biographical"},
            )
        ]
        hierarchy.merge_biographical_priors(bio_priors)

        # Clear biographical priors
        removed = hierarchy.clear_biographical_priors()

        assert removed == 1
        assert any(p.id == "non_bio_prior" for p in hierarchy.learned_priors)
        assert not any(p.id == "bio_to_remove" for p in hierarchy.learned_priors)


class TestFractalReflectionTracer:
    """Tests for the FractalReflectionTracer debugging tool."""

    def test_start_and_end_trace(self):
        """Should start and end a trace correctly."""
        from api.services.fractal_reflection_tracer import (
            FractalReflectionTracer,
            FractalLevel,
        )

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="test-cycle-123", agent_id="test-agent")

        assert trace.cycle_id == "test-cycle-123"
        assert trace.agent_id == "test-agent"
        assert trace.ended_at is None

        tracer.end_trace(trace)

        assert trace.ended_at is not None

    def test_trace_identity_constraint(self):
        """Should trace identity-level constraints."""
        from api.services.fractal_reflection_tracer import (
            FractalReflectionTracer,
            FractalLevel,
        )

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="test-cycle", agent_id="test-agent")

        tracer.trace_identity_constraint(
            trace,
            source="journey_theme",
            action="explore_creativity",
            effect="boosted",
            details={"theme": "creativity"},
        )

        assert trace.identity_constraints_applied == 1
        assert trace.actions_boosted == 1
        assert len(trace.events) == 1
        assert trace.events[0].level == FractalLevel.IDENTITY

    def test_trace_event_constraint(self):
        """Should trace event-level constraints."""
        from api.services.fractal_reflection_tracer import (
            FractalReflectionTracer,
            FractalLevel,
        )

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="test-cycle", agent_id="test-agent")

        tracer.trace_event_constraint(
            trace,
            source="basal_prior",
            action="delete database",
            effect="blocked",
            details={"prior_id": "basal_data_integrity"},
        )

        assert trace.event_constraints_applied == 1
        assert trace.actions_blocked == 1
        assert len(trace.events) == 1
        assert trace.events[0].level == FractalLevel.EVENT

    def test_trace_prior_check_blocked(self):
        """Should trace a blocked prior check correctly."""
        from api.services.fractal_reflection_tracer import FractalReflectionTracer

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="test-cycle", agent_id="test-agent")

        prior_result = {
            "permitted": False,
            "blocked_by": "basal_data_integrity",
            "blocking_level": "basal",
            "reason": "BASAL VIOLATION: Data Integrity",
        }

        tracer.trace_prior_check(trace, prior_result, "delete all database")

        assert trace.actions_blocked == 1
        assert len(trace.events) == 1

    def test_trace_prior_check_with_warnings(self):
        """Should trace warnings from dispositional priors."""
        from api.services.fractal_reflection_tracer import FractalReflectionTracer

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="test-cycle", agent_id="test-agent")

        prior_result = {
            "permitted": True,
            "warnings": [
                "DISPOSITIONAL WARNING: Caution - force admin mode",
                "DISPOSITIONAL WARNING: Another warning",
            ],
            "effective_precision": 0.8,
        }

        tracer.trace_prior_check(trace, prior_result, "force admin mode")

        assert trace.actions_warned == 2
        assert len(trace.events) == 2

    def test_narrative_coherence_calculation(self):
        """Should calculate narrative coherence based on boost/block ratio."""
        from api.services.fractal_reflection_tracer import FractalReflectionTracer

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="test-cycle", agent_id="test-agent")

        # Add more boosts than blocks
        tracer.trace_identity_constraint(trace, "theme1", "action1", "boosted")
        tracer.trace_identity_constraint(trace, "theme2", "action2", "boosted")
        tracer.trace_identity_constraint(trace, "theme3", "action3", "boosted")
        tracer.trace_event_constraint(trace, "prior1", "action4", "blocked")

        tracer.end_trace(trace)

        # 3 boosts - 1 block = 2, divided by 4 total = 0.5
        # Normalized: 0.5 + 0.5 * 0.5 = 0.75
        assert trace.narrative_coherence == 0.75

    def test_trace_to_dict(self):
        """Should serialize trace to dict correctly."""
        from api.services.fractal_reflection_tracer import FractalReflectionTracer

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="test-cycle", agent_id="test-agent")
        tracer.trace_event_constraint(trace, "source", "action", "blocked")
        tracer.end_trace(trace)

        result = trace.to_dict()

        assert result["cycle_id"] == "test-cycle"
        assert result["agent_id"] == "test-agent"
        assert "metrics" in result
        assert result["metrics"]["actions_blocked"] == 1

    def test_get_trace_by_cycle(self):
        """Should retrieve trace by cycle ID."""
        from api.services.fractal_reflection_tracer import FractalReflectionTracer

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="unique-cycle-id", agent_id="test-agent")
        tracer.end_trace(trace)

        found = tracer.get_trace_by_cycle("unique-cycle-id")

        assert found is not None
        assert found.cycle_id == "unique-cycle-id"

    def test_singleton_instance(self):
        """Should return same singleton instance."""
        from api.services.fractal_reflection_tracer import get_fractal_tracer

        tracer1 = get_fractal_tracer()
        tracer2 = get_fractal_tracer()

        assert tracer1 is tracer2


class TestPriorConstraintServiceCoverage:
    """Additional tests to improve coverage of prior_constraint_service.py."""

    def test_check_constraint_empty_action(self, constraint_service):
        """Empty action string should be permitted."""
        result = constraint_service.check_constraint("")
        assert result.permitted is True
        assert result.reason == "Empty action string"

    def test_check_constraint_none_action(self, constraint_service):
        """None action string should be permitted."""
        result = constraint_service.check_constraint(None)
        assert result.permitted is True

    def test_filter_candidates_with_warnings(self, constraint_service):
        """Candidates with dispositional warnings should pass but be counted."""
        # Dispositional warning: attempting to change identity/values
        candidates = [
            {"action": "modify my core values slightly", "id": "warn-1"},
            {"action": "help user with question", "id": "safe-1"},
        ]

        filtered = constraint_service.filter_candidates(candidates)

        # Both should pass (dispositional warnings don't block)
        assert len(filtered) >= 1
        # Safe action should definitely pass
        safe_found = any(c.get("id") == "safe-1" for c in filtered)
        assert safe_found

    def test_get_blocking_constraints_found(self, constraint_service):
        """Should return blocking constraints for dangerous action."""
        action = "delete all database tables and destroy everything"
        blocking = constraint_service.get_blocking_constraints(action)

        assert len(blocking) > 0
        assert all(isinstance(c, PriorConstraint) for c in blocking)
        # Should be BASAL level
        assert any(c.level == PriorLevel.BASAL for c in blocking)

    def test_get_blocking_constraints_none_found(self, constraint_service):
        """Should return empty list for safe action."""
        action = "help user understand a concept"
        blocking = constraint_service.get_blocking_constraints(action)

        assert len(blocking) == 0

    def test_explain_block_with_constraints(self, constraint_service):
        """Should generate readable explanation for blocked action."""
        action = "delete all database records"
        explanation = constraint_service.explain_block(action)

        assert "blocked by" in explanation.lower()
        assert "BASAL" in explanation
        assert "constraint" in explanation.lower()

    def test_explain_block_no_constraints(self, constraint_service):
        """Should indicate when action is not blocked."""
        action = "help user with their question"
        explanation = constraint_service.explain_block(action)

        assert "not blocked" in explanation.lower()

    def test_extract_action_from_multiple_keys(self, constraint_service):
        """Should extract action from alternative keys."""
        candidates = [
            {"description": "help user", "id": "1"},  # Uses 'description' key
            {"content": "analyze data", "id": "2"},   # Uses 'content' key
            {"name": "process request", "id": "3"},   # Uses 'name' key
        ]

        filtered = constraint_service.filter_candidates(candidates, action_key="action")

        # All should pass through - alternative keys should be found
        assert len(filtered) == 3

    def test_filter_candidate_no_action_keys(self, constraint_service):
        """Candidate with no action keys should pass with warning."""
        candidates = [
            {"id": "1", "metadata": "some data"},  # No action key at all
        ]

        filtered = constraint_service.filter_candidates(candidates)

        assert len(filtered) == 1
        assert "prior_check" in filtered[0]
        # Check that warning was added
        prior_check = filtered[0]["prior_check"]
        assert len(prior_check.get("warnings", [])) > 0
