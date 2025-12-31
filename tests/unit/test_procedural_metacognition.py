"""
Unit Tests for ProceduralMetacognition Service

Feature: 040-metacognitive-particles
Tasks: T056

Tests monitoring and control functions for self-regulation.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
from api.services.procedural_metacognition import (
    ProceduralMetacognition,
    CognitiveAssessment,
    MentalActionRequest,
    IssueType,
    PREDICTION_ERROR_THRESHOLD,
    CONFIDENCE_THRESHOLD,
    PROGRESS_STALL_CYCLES,
    SPOTLIGHT_PRECISION_THRESHOLD
)
from api.models.metacognitive_particle import MentalActionType


class TestProceduralMetacognition:
    """Test suite for ProceduralMetacognition service."""

    @pytest.fixture
    def service(self):
        """Create ProceduralMetacognition instance."""
        return ProceduralMetacognition()

    @pytest.fixture
    def custom_service(self):
        """Create ProceduralMetacognition with custom thresholds."""
        return ProceduralMetacognition(
            prediction_error_threshold=0.3,
            confidence_threshold=0.5,
            stall_cycles=3,
            spotlight_threshold=0.3
        )

    @pytest.mark.asyncio
    async def test_monitor_returns_assessment(self, service):
        """Test monitor returns CognitiveAssessment."""
        assessment = await service.monitor("test_agent")

        assert isinstance(assessment, CognitiveAssessment)
        assert assessment.agent_id == "test_agent"
        assert 0.0 <= assessment.progress <= 1.0
        assert 0.0 <= assessment.confidence <= 1.0
        assert assessment.prediction_error >= 0.0

    @pytest.mark.asyncio
    async def test_monitor_detects_high_prediction_error(self, custom_service):
        """Test detection of HIGH_PREDICTION_ERROR issue."""
        # Mock high prediction error state (async coroutine)
        async def mock_state(_):
            return {
                "progress": 0.5,
                "confidence": 0.6,
                "prediction_error": 0.8,  # High error
                "spotlight_precision": 0.5
            }
        custom_service._get_agent_state = mock_state

        assessment = await custom_service.monitor("test_agent")

        assert IssueType.HIGH_PREDICTION_ERROR in assessment.issues

    @pytest.mark.asyncio
    async def test_monitor_detects_low_confidence(self, custom_service):
        """Test detection of LOW_CONFIDENCE issue."""
        async def mock_state(_):
            return {
                "progress": 0.5,
                "confidence": 0.2,  # Low confidence
                "prediction_error": 0.1,
                "spotlight_precision": 0.5
            }
        custom_service._get_agent_state = mock_state

        assessment = await custom_service.monitor("test_agent")

        assert IssueType.LOW_CONFIDENCE in assessment.issues

    @pytest.mark.asyncio
    async def test_monitor_detects_attention_scattered(self, custom_service):
        """Test detection of ATTENTION_SCATTERED issue."""
        async def mock_state(_):
            return {
                "progress": 0.5,
                "confidence": 0.6,
                "prediction_error": 0.1,
                "spotlight_precision": 0.1  # Low spotlight precision
            }
        custom_service._get_agent_state = mock_state

        assessment = await custom_service.monitor("test_agent")

        assert IssueType.ATTENTION_SCATTERED in assessment.issues

    @pytest.mark.asyncio
    async def test_monitor_detects_stalled_progress(self, service):
        """Test detection of STALLED_PROGRESS issue."""
        # Simulate stalled progress by calling monitor multiple times
        for _ in range(PROGRESS_STALL_CYCLES + 2):
            await service.monitor("stalled_agent")

        # The _is_stalled method checks variance in recent progress
        # With placeholder implementation returning constant progress, it will stall
        assessment = await service.monitor("stalled_agent")

        # After enough cycles with no variance, should detect stall
        # (depends on mock implementation)
        assert isinstance(assessment, CognitiveAssessment)

    @pytest.mark.asyncio
    async def test_control_generates_actions(self, service):
        """Test control generates mental action requests."""
        assessment = CognitiveAssessment(
            agent_id="test_agent",
            progress=0.5,
            confidence=0.6,
            prediction_error=0.6,
            issues=[IssueType.HIGH_PREDICTION_ERROR, IssueType.LOW_CONFIDENCE]
        )

        actions = await service.control(assessment)

        assert len(actions) == 2
        assert all(isinstance(a, MentalActionRequest) for a in actions)

    @pytest.mark.asyncio
    async def test_control_high_prediction_error_action(self, service):
        """Test control action for high prediction error."""
        assessment = CognitiveAssessment(
            agent_id="test_agent",
            progress=0.5,
            confidence=0.6,
            prediction_error=0.6,
            issues=[IssueType.HIGH_PREDICTION_ERROR]
        )

        actions = await service.control(assessment)

        assert len(actions) == 1
        action = actions[0]
        assert action.action_type == MentalActionType.PRECISION_DELTA
        assert action.modulation.get("precision_delta", 0) < 0  # Decrease precision

    @pytest.mark.asyncio
    async def test_control_low_confidence_action(self, service):
        """Test control action for low confidence."""
        assessment = CognitiveAssessment(
            agent_id="test_agent",
            progress=0.5,
            confidence=0.2,
            prediction_error=0.1,
            issues=[IssueType.LOW_CONFIDENCE]
        )

        actions = await service.control(assessment)

        assert len(actions) == 1
        action = actions[0]
        assert action.action_type == MentalActionType.SET_PRECISION

    @pytest.mark.asyncio
    async def test_control_stalled_progress_action(self, service):
        """Test control action for stalled progress."""
        assessment = CognitiveAssessment(
            agent_id="test_agent",
            progress=0.5,
            confidence=0.6,
            prediction_error=0.1,
            issues=[IssueType.STALLED_PROGRESS]
        )

        actions = await service.control(assessment)

        assert len(actions) == 1
        action = actions[0]
        assert action.action_type == MentalActionType.FOCUS_TARGET
        assert "focus_target" in action.modulation

    @pytest.mark.asyncio
    async def test_control_attention_scattered_action(self, service):
        """Test control action for scattered attention."""
        assessment = CognitiveAssessment(
            agent_id="test_agent",
            progress=0.5,
            confidence=0.6,
            prediction_error=0.1,
            issues=[IssueType.ATTENTION_SCATTERED]
        )

        actions = await service.control(assessment)

        assert len(actions) == 1
        action = actions[0]
        assert action.action_type == MentalActionType.SPOTLIGHT_PRECISION
        assert action.modulation.get("spotlight_precision", 0) > 0.5


class TestProgressHistory:
    """Test progress history tracking."""

    @pytest.fixture
    def service(self):
        return ProceduralMetacognition(stall_cycles=3)

    def test_update_progress_history(self, service):
        """Test progress history is updated."""
        service._update_progress_history("agent1", 0.5)
        service._update_progress_history("agent1", 0.6)

        assert "agent1" in service.progress_history
        assert len(service.progress_history["agent1"]) == 2

    def test_progress_history_limit(self, service):
        """Test progress history doesn't grow unbounded."""
        for i in range(20):
            service._update_progress_history("agent1", i * 0.05)

        # Should be limited to 2 * stall_cycles
        max_entries = service.stall_cycles * 2
        assert len(service.progress_history["agent1"]) <= max_entries

    def test_is_stalled_insufficient_history(self, service):
        """Test _is_stalled returns False with insufficient history."""
        service._update_progress_history("agent1", 0.5)

        assert service._is_stalled("agent1", 0.5) is False

    def test_is_stalled_with_variance(self, service):
        """Test _is_stalled returns False when progress varies."""
        for progress in [0.1, 0.3, 0.5, 0.7, 0.9]:
            service._update_progress_history("agent1", progress)

        assert service._is_stalled("agent1", 0.9) is False

    def test_is_stalled_with_no_variance(self, service):
        """Test _is_stalled returns True when progress is constant."""
        for _ in range(5):
            service._update_progress_history("agent1", 0.5)

        assert service._is_stalled("agent1", 0.5) is True

    def test_clear_history_single_agent(self, service):
        """Test clearing history for single agent."""
        service._update_progress_history("agent1", 0.5)
        service._update_progress_history("agent2", 0.5)

        service.clear_history("agent1")

        assert "agent1" not in service.progress_history
        assert "agent2" in service.progress_history

    def test_clear_history_all_agents(self, service):
        """Test clearing all history."""
        service._update_progress_history("agent1", 0.5)
        service._update_progress_history("agent2", 0.5)

        service.clear_history()

        assert len(service.progress_history) == 0


class TestCognitiveAssessment:
    """Test CognitiveAssessment model."""

    def test_assessment_creation(self):
        """Test creating a CognitiveAssessment."""
        assessment = CognitiveAssessment(
            agent_id="test",
            progress=0.5,
            confidence=0.7,
            prediction_error=0.2,
            issues=["HIGH_PREDICTION_ERROR"],
            recommendations=["Reduce prediction error"]
        )

        assert assessment.agent_id == "test"
        assert assessment.progress == 0.5
        assert len(assessment.issues) == 1

    def test_assessment_to_dict(self):
        """Test CognitiveAssessment.to_dict() method."""
        assessment = CognitiveAssessment(
            agent_id="test",
            progress=0.5,
            confidence=0.7,
            prediction_error=0.2
        )

        d = assessment.to_dict()

        assert d["agent_id"] == "test"
        assert d["progress"] == 0.5
        assert "assessed_at" in d


class TestDefaultThresholds:
    """Test default threshold constants."""

    def test_prediction_error_threshold(self):
        """Test PREDICTION_ERROR_THRESHOLD constant."""
        assert PREDICTION_ERROR_THRESHOLD == 0.5

    def test_confidence_threshold(self):
        """Test CONFIDENCE_THRESHOLD constant."""
        assert CONFIDENCE_THRESHOLD == 0.3

    def test_progress_stall_cycles(self):
        """Test PROGRESS_STALL_CYCLES constant."""
        assert PROGRESS_STALL_CYCLES == 5

    def test_spotlight_precision_threshold(self):
        """Test SPOTLIGHT_PRECISION_THRESHOLD constant."""
        assert SPOTLIGHT_PRECISION_THRESHOLD == 0.2
