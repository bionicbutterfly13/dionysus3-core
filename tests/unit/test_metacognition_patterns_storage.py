"""
Unit tests for Metacognition Patterns Storage

Tests HOT-tier pattern storage and access patterns.
"""

import pytest
from datetime import datetime, timedelta

from api.services.metacognition_patterns_storage import (
    get_metacognition_patterns_storage,
    ProceduralMetacognitionPatternsStorage,
    MonitoringPattern,
    ControlPattern,
    ThoughtseedCompetitionPattern,
    LoopPreventionPattern,
    PatternType,
)


class TestMonitoringPattern:
    """Tests for MonitoringPattern."""

    def test_create_monitoring_pattern(self):
        """Test creating a monitoring pattern."""
        pattern = MonitoringPattern(
            check_interval=3,
            ttl_hours=1,
        )

        assert pattern.pattern_type == PatternType.MONITORING
        assert pattern.check_interval == 3
        assert pattern.ttl_hours == 1
        assert pattern.access_count == 0

    def test_monitoring_pattern_expiry(self):
        """Test monitoring pattern TTL expiry."""
        pattern = MonitoringPattern(ttl_hours=1)

        # Should not be expired immediately
        assert not pattern.is_expired()

        # Manually set created_at to past
        pattern.created_at = datetime.utcnow() - timedelta(hours=2)

        # Should be expired now
        assert pattern.is_expired()

    def test_monitoring_pattern_access_tracking(self):
        """Test access tracking for monitoring patterns."""
        pattern = MonitoringPattern()

        assert pattern.access_count == 0
        pattern.update_access()
        assert pattern.access_count == 1

        pattern.update_access()
        assert pattern.access_count == 2

    def test_monitoring_pattern_serialization(self):
        """Test serialization of monitoring pattern."""
        pattern = MonitoringPattern(check_interval=5)

        data = pattern.to_dict()

        assert data["pattern_type"] == "monitoring"
        assert data["check_interval"] == 5
        assert "pattern_id" in data
        assert "created_at" in data


class TestControlPattern:
    """Tests for ControlPattern."""

    def test_create_control_pattern(self):
        """Test creating a control pattern."""
        pattern = ControlPattern(
            surprise_threshold=0.7,
            confidence_threshold=0.3,
            free_energy_threshold=3.0,
        )

        assert pattern.pattern_type == PatternType.CONTROL
        assert pattern.surprise_threshold == 0.7
        assert pattern.confidence_threshold == 0.3

    def test_control_pattern_action_selection(self):
        """Test action selection based on thresholds."""
        pattern = ControlPattern(
            surprise_threshold=0.7,
            confidence_threshold=0.3,
            free_energy_threshold=3.0,
        )

        # High surprise
        action = pattern.get_action_for_state(
            surprise=0.8,
            confidence=0.5,
            free_energy=1.0
        )
        assert action == "generate_thoughtseeds"

        # Low confidence
        action = pattern.get_action_for_state(
            surprise=0.5,
            confidence=0.2,
            free_energy=1.0
        )
        assert action == "replan"

        # High free energy
        action = pattern.get_action_for_state(
            surprise=0.5,
            confidence=0.5,
            free_energy=4.0
        )
        assert action == "reduce_model_complexity"

        # All ok
        action = pattern.get_action_for_state(
            surprise=0.5,
            confidence=0.5,
            free_energy=1.0
        )
        assert action is None

    def test_control_pattern_bounds(self):
        """Test precision bounds."""
        pattern = ControlPattern()

        assert pattern.precision_bounds["min"] == 0.1
        assert pattern.precision_bounds["max"] == 0.9


class TestThoughtseedCompetitionPattern:
    """Tests for ThoughtseedCompetitionPattern."""

    def test_create_thoughtseed_pattern(self):
        """Test creating a thoughtseed pattern."""
        pattern = ThoughtseedCompetitionPattern(
            algorithm="meta_tot_mcts",
            max_iterations=100,
        )

        assert pattern.pattern_type == PatternType.THOUGHTSEED_COMPETITION
        assert pattern.algorithm == "meta_tot_mcts"
        assert pattern.max_iterations == 100

    def test_thoughtseed_pattern_access_tracking(self):
        """Test access tracking."""
        pattern = ThoughtseedCompetitionPattern()

        assert pattern.access_count == 0
        pattern.update_access()
        assert pattern.access_count == 1

    def test_thoughtseed_pattern_serialization(self):
        """Test serialization."""
        pattern = ThoughtseedCompetitionPattern()

        data = pattern.to_dict()

        assert data["pattern_type"] == "thoughtseed_competition"
        assert "algorithm" in data
        assert "max_iterations" in data


class TestLoopPreventionPattern:
    """Tests for LoopPreventionPattern."""

    def test_create_loop_prevention_pattern(self):
        """Test creating a loop prevention pattern."""
        pattern = LoopPreventionPattern(
            max_recursion_depth=3,
            diminishing_returns_threshold=0.05,
        )

        assert pattern.pattern_type == PatternType.LOOP_PREVENTION
        assert pattern.max_recursion_depth == 3

    def test_loop_prevention_depth_limit(self):
        """Test depth limit."""
        pattern = LoopPreventionPattern(max_recursion_depth=2)

        assert pattern.should_continue_recursion()
        pattern.recursion_depth = 1
        assert pattern.should_continue_recursion()
        pattern.recursion_depth = 2
        assert not pattern.should_continue_recursion()

    def test_loop_prevention_improvement_tracking(self):
        """Test improvement tracking and diminishing returns."""
        pattern = LoopPreventionPattern(
            max_recursion_depth=10,
            improvement_window=3,
            diminishing_returns_threshold=0.05,
        )

        # Record small improvements
        pattern.record_improvement(0.02)
        pattern.record_improvement(0.01)
        pattern.record_improvement(0.02)

        # Should detect diminishing returns
        assert not pattern.should_continue_recursion()

    def test_loop_prevention_force_execution(self):
        """Test force execution after N steps."""
        pattern = LoopPreventionPattern(
            max_recursion_depth=10,
            force_execution_after_steps=3,
        )

        pattern.step_counter = 2
        assert pattern.should_continue_recursion()

        pattern.step_counter = 3
        assert not pattern.should_continue_recursion()

    def test_loop_prevention_reset(self):
        """Test reset functionality."""
        pattern = LoopPreventionPattern()

        pattern.step_counter = 5
        pattern.recursion_depth = 2
        pattern.record_improvement(0.1)

        pattern.reset_for_new_context()

        assert pattern.step_counter == 0
        assert pattern.recursion_depth == 0
        assert len(pattern.last_improvements) == 0


class TestProceduralMetacognitionPatternsStorage:
    """Tests for the main storage service."""

    @pytest.fixture
    def storage(self):
        """Create a new storage instance for each test."""
        return ProceduralMetacognitionPatternsStorage()

    def test_initialization(self, storage):
        """Test storage initialization."""
        stats = storage.get_stats()

        # Should have 4 default patterns
        assert stats["monitoring_patterns_count"] == 1
        assert stats["control_patterns_count"] == 1
        assert stats["thoughtseed_patterns_count"] == 1
        assert stats["loop_prevention_patterns_count"] == 1
        assert stats["total_patterns"] == 4

    def test_store_and_retrieve_monitoring(self, storage):
        """Test storing and retrieving monitoring patterns."""
        pattern = MonitoringPattern(check_interval=5)
        pattern_id = storage.store_monitoring_pattern(pattern)

        retrieved = storage.get_monitoring_pattern(pattern_id)

        assert retrieved is not None
        assert retrieved.pattern_id == pattern_id
        assert retrieved.check_interval == 5
        assert retrieved.access_count == 1

    def test_store_and_retrieve_control(self, storage):
        """Test storing and retrieving control patterns."""
        pattern = ControlPattern(surprise_threshold=0.8)
        pattern_id = storage.store_control_pattern(pattern)

        retrieved = storage.get_control_pattern(pattern_id)

        assert retrieved is not None
        assert retrieved.surprise_threshold == 0.8

    def test_store_and_retrieve_thoughtseed(self, storage):
        """Test storing and retrieving thoughtseed patterns."""
        pattern = ThoughtseedCompetitionPattern(max_iterations=200)
        pattern_id = storage.store_thoughtseed_pattern(pattern)

        retrieved = storage.get_thoughtseed_pattern(pattern_id)

        assert retrieved is not None
        assert retrieved.max_iterations == 200

    def test_store_and_retrieve_loop_prevention(self, storage):
        """Test storing and retrieving loop prevention patterns."""
        pattern = LoopPreventionPattern(max_recursion_depth=5)
        pattern_id = storage.store_loop_prevention_pattern(pattern)

        retrieved = storage.get_loop_prevention_pattern(pattern_id)

        assert retrieved is not None
        assert retrieved.max_recursion_depth == 5

    def test_get_by_id(self, storage):
        """Test retrieving pattern by ID."""
        pattern = MonitoringPattern()
        pattern_id = storage.store_monitoring_pattern(pattern)

        retrieved = storage.get_pattern_by_id(pattern_id)

        assert retrieved is not None
        assert retrieved["pattern_type"] == "monitoring"

    def test_default_patterns(self, storage):
        """Test getting default patterns."""
        monitor = storage.get_default_monitoring_pattern()
        control = storage.get_default_control_pattern()
        thoughtseed = storage.get_default_thoughtseed_pattern()
        loop_prev = storage.get_default_loop_prevention_pattern()

        assert monitor is not None
        assert control is not None
        assert thoughtseed is not None
        assert loop_prev is not None

    def test_cleanup_expired_patterns(self, storage):
        """Test cleaning up expired patterns."""
        # Create expired pattern
        pattern = MonitoringPattern(ttl_hours=0)
        pattern.created_at = datetime.utcnow() - timedelta(hours=1)
        pattern_id = storage.store_monitoring_pattern(pattern)

        # Cleanup
        expired = storage.cleanup_expired_patterns()

        assert expired["monitoring"] == 1
        assert storage.get_monitoring_pattern(pattern_id) is None

    def test_list_all_patterns(self, storage):
        """Test listing all patterns."""
        all_patterns = storage.list_all_patterns()

        assert "monitoring" in all_patterns
        assert "control" in all_patterns
        assert "thoughtseed" in all_patterns
        assert "loop_prevention" in all_patterns

        assert len(all_patterns["monitoring"]) >= 1
        assert len(all_patterns["control"]) >= 1

    def test_clear_all_patterns(self, storage):
        """Test clearing all patterns."""
        storage.clear_all_patterns()

        stats = storage.get_stats()
        assert stats["total_patterns"] == 0

    def test_access_statistics(self, storage):
        """Test access statistics tracking."""
        pattern = MonitoringPattern()
        pattern_id = storage.store_monitoring_pattern(pattern)

        initial_stats = storage.get_stats()
        initial_accesses = initial_stats["patterns_accessed"]

        # Access the pattern
        storage.get_monitoring_pattern(pattern_id)
        storage.get_monitoring_pattern(pattern_id)

        updated_stats = storage.get_stats()
        assert updated_stats["patterns_accessed"] == initial_accesses + 2


class TestSingleton:
    """Tests for singleton instance."""

    def test_singleton_instance(self):
        """Test that singleton returns same instance."""
        storage1 = get_metacognition_patterns_storage()
        storage2 = get_metacognition_patterns_storage()

        assert storage1 is storage2

    def test_singleton_state_persistence(self):
        """Test that state persists across calls."""
        storage = get_metacognition_patterns_storage()

        # Store a pattern
        pattern = MonitoringPattern(check_interval=7)
        pattern_id = storage.store_monitoring_pattern(pattern)

        # Get new instance (should be same)
        storage2 = get_metacognition_patterns_storage()
        retrieved = storage2.get_monitoring_pattern(pattern_id)

        assert retrieved is not None
        assert retrieved.check_interval == 7
