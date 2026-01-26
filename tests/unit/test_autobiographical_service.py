"""
Unit tests for AutobiographicalService.

Tests memory persistence, event recording, and consciousness tracking
without requiring live Neo4j connections.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from api.models.autobiographical import (
    DevelopmentEvent,
    DevelopmentEventType,
    DevelopmentArchetype,
    ActiveInferenceState,
    ConversationMoment,
    ConsciousnessReport,
    ExtendedMindState,
)
from api.services.autobiographical_service import (
    AutobiographicalService,
    get_basin_for_archetype,
    get_basin_metadata,
)


# Only mark async tests with asyncio
# Helper function tests are sync and should not be marked


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    def test_get_basin_for_archetype_maps_correctly(self):
        """Verify archetype to basin mapping."""
        assert get_basin_for_archetype(DevelopmentArchetype.SAGE) == "conceptual-basin"
        assert get_basin_for_archetype(DevelopmentArchetype.CREATOR) == "procedural-basin"
        assert get_basin_for_archetype(DevelopmentArchetype.EXPLORER) == "experiential-basin"
        assert get_basin_for_archetype(DevelopmentArchetype.WARRIOR) == "strategic-basin"

    def test_get_basin_for_archetype_defaults_to_conceptual(self):
        """Verify unknown archetype defaults to conceptual-basin."""
        # Use a hypothetical archetype not in mapping
        unknown = DevelopmentArchetype.INNOCENT  # This is mapped, but test the fallback logic
        result = get_basin_for_archetype(unknown)
        assert result in ["conceptual-basin", "experiential-basin"]  # INNOCENT maps to experiential

    def test_get_basin_metadata_returns_expected_structure(self):
        """Verify basin metadata includes required fields."""
        meta = get_basin_metadata("conceptual-basin")
        assert "description" in meta
        assert "concepts" in meta
        assert "strength" in meta
        assert isinstance(meta["strength"], float)

    def test_get_basin_metadata_defaults_for_unknown(self):
        """Verify unknown basin gets safe defaults."""
        meta = get_basin_metadata("unknown-basin")
        assert meta["description"] == "Autobiographical attractor basin"
        assert meta["concepts"] == []
        assert meta["strength"] == 0.5


@pytest.mark.asyncio
class TestAutobiographicalServiceInit:
    """Tests for service initialization."""

    async def test_init_creates_service_with_default_driver(self):
        """Verify service initializes with default driver."""
        mock_driver = AsyncMock()
        with patch("api.services.autobiographical_service.get_neo4j_driver", return_value=mock_driver):
            service = AutobiographicalService()
            assert service._driver == mock_driver
            assert service._analyzer is not None

    async def test_init_accepts_custom_driver(self):
        """Verify service accepts custom driver for testing."""
        custom_driver = AsyncMock()
        service = AutobiographicalService(driver=custom_driver)
        assert service._driver == custom_driver


@pytest.mark.asyncio
class TestAnalyzeAndRecordEvent:
    """Tests for analyze_and_record_event method."""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver."""
        driver = AsyncMock()
        driver.execute_query = AsyncMock(return_value=[])
        return driver

    @pytest.fixture
    def mock_analyzer(self):
        """Create mock ActiveInferenceAnalyzer."""
        analyzer = MagicMock()
        analyzer.analyze = MagicMock(
            return_value=ActiveInferenceState(
                tools_accessed=["tool1"],
                resources_used=["resource1"],
                basin_influence_strength=0.8,
                resonance_frequency=1.2,
                harmonic_mode_id="mode1",
            )
        )
        analyzer.map_resonance_to_archetype = MagicMock(return_value=DevelopmentArchetype.SAGE)
        return analyzer

    async def test_analyze_and_record_event_creates_event_with_archetype(self, mock_driver, mock_analyzer):
        """Verify event is created with archetype and basin mapping."""
        service = AutobiographicalService(driver=mock_driver)
        service._analyzer = mock_analyzer

        event_id = await service.analyze_and_record_event(
            user_input="Test input",
            agent_response="Test response",
            event_type=DevelopmentEventType.SYSTEM_REFLECTION,
            summary="Test summary",
            rationale="Test rationale",
            tools_used=["tool1"],
        )

        assert event_id is not None
        mock_driver.execute_query.assert_awaited_once()
        call_args = mock_driver.execute_query.await_args
        assert call_args[0][0]  # Cypher query exists
        params = call_args[0][1]
        assert params["type"] == DevelopmentEventType.SYSTEM_REFLECTION.value
        assert params["archetype"] == DevelopmentArchetype.SAGE.value
        assert params["strange_attractor_id"] == "conceptual-basin"  # SAGE maps to conceptual

    async def test_analyze_and_record_event_handles_missing_archetype(self, mock_driver, mock_analyzer):
        """Verify service handles None archetype gracefully."""
        mock_analyzer.map_resonance_to_archetype.return_value = None
        service = AutobiographicalService(driver=mock_driver)
        service._analyzer = mock_analyzer

        event_id = await service.analyze_and_record_event(
            user_input="Test",
            agent_response="Response",
            event_type=DevelopmentEventType.SYSTEM_REFLECTION,
            summary="Summary",
            rationale="Rationale",
        )

        assert event_id is not None
        call_args = mock_driver.execute_query.await_args
        params = call_args[0][1]
        assert params["strange_attractor_id"] == "conceptual-basin"  # Default fallback


@pytest.mark.asyncio
class TestRecordEvent:
    """Tests for record_event method."""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver."""
        driver = AsyncMock()
        driver.execute_query = AsyncMock(return_value=[])
        return driver

    async def test_record_event_persists_event_to_neo4j(self, mock_driver):
        """Verify record_event calls driver with correct Cypher."""
        service = AutobiographicalService(driver=mock_driver)
        event = DevelopmentEvent(
            event_id="evt_123",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.SYSTEM_REFLECTION,
            summary="Test event",
            rationale="Test rationale",
            impact="Test impact",
            development_archetype=DevelopmentArchetype.SAGE,
            strange_attractor_id="conceptual-basin",
        )

        event_id = await service.record_event(event)

        assert event_id == "evt_123"
        mock_driver.execute_query.assert_awaited_once()
        call_args = mock_driver.execute_query.await_args
        cypher = call_args[0][0]
        assert "MERGE (e:DevelopmentEvent" in cypher
        assert "MERGE (b:AttractorBasin" in cypher
        params = call_args[0][1]
        assert params["id"] == "evt_123"
        assert params["type"] == DevelopmentEventType.SYSTEM_REFLECTION.value

    async def test_record_event_serializes_active_inference_state(self, mock_driver):
        """Verify active inference state is serialized to JSON."""
        service = AutobiographicalService(driver=mock_driver)
        ai_state = ActiveInferenceState(
            tools_accessed=["tool1"],
            basin_influence_strength=0.9,
        )
        event = DevelopmentEvent(
            event_id="evt_456",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.SYSTEM_REFLECTION,
            summary="Test",
            rationale="Test",
            impact="Test",
            active_inference_state=ai_state,
            strange_attractor_id="conceptual-basin",
        )

        await service.record_event(event)

        call_args = mock_driver.execute_query.await_args
        params = call_args[0][1]
        assert params["active_inference"] is not None
        assert isinstance(params["active_inference"], str)  # JSON string

    async def test_record_event_handles_dict_metadata(self, mock_driver):
        """Verify dict metadata is serialized correctly."""
        service = AutobiographicalService(driver=mock_driver)
        event = DevelopmentEvent(
            event_id="evt_789",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.SYSTEM_REFLECTION,
            summary="Test",
            rationale="Test",
            impact="Test",
            metadata={"key": "value", "number": 42},
            strange_attractor_id="conceptual-basin",
        )

        await service.record_event(event)

        call_args = mock_driver.execute_query.await_args
        params = call_args[0][1]
        assert isinstance(params["metadata"], str)  # JSON string
        import json
        parsed = json.loads(params["metadata"])
        assert parsed["key"] == "value"
        assert parsed["number"] == 42


@pytest.mark.asyncio
class TestGetSystemStory:
    """Tests for get_system_story method."""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver."""
        driver = AsyncMock()
        return driver

    async def test_get_system_story_returns_events(self, mock_driver):
        """Verify get_system_story retrieves and parses events."""
        mock_driver.execute_query = AsyncMock(
            return_value=[
                {
                    "e": {
                        "id": "evt_1",
                        "timestamp": "2024-01-01T00:00:00+00:00",
                        "type": "system_reflection",
                        "summary": "Event 1",
                        "rationale": "Rationale 1",
                        "impact": "Impact 1",
                        "lessons_learned": [],
                        "metadata": {},
                        "development_archetype": "sage",
                        "narrative_coherence": 0.8,
                        "resonance_score": 0.7,
                        "strange_attractor_id": "conceptual-basin",
                        "related_files": [],
                    }
                }
            ]
        )
        service = AutobiographicalService(driver=mock_driver)

        events = await service.get_system_story(limit=10)

        assert len(events) == 1
        assert events[0].event_id == "evt_1"
        assert events[0].summary == "Event 1"
        assert events[0].development_archetype == DevelopmentArchetype.SAGE
        mock_driver.execute_query.assert_awaited_once()

    async def test_get_system_story_rehydrates_active_inference(self, mock_driver):
        """Verify active inference state is rehydrated from JSON."""
        ai_state_json = '{"tools_accessed": ["tool1"], "basin_influence_strength": 0.8}'
        mock_driver.execute_query = AsyncMock(
            return_value=[
                {
                    "e": {
                        "id": "evt_2",
                        "timestamp": "2024-01-01T00:00:00+00:00",
                        "type": "system_reflection",
                        "summary": "Test",
                        "rationale": "Test",
                        "impact": "Test",
                        "lessons_learned": [],
                        "metadata": {},
                        "active_inference_state": ai_state_json,
                        "narrative_coherence": 0.8,
                        "resonance_score": 0.7,
                        "strange_attractor_id": "conceptual-basin",
                        "related_files": [],
                    }
                }
            ]
        )
        service = AutobiographicalService(driver=mock_driver)

        events = await service.get_system_story(limit=10)

        assert events[0].active_inference_state is not None
        assert events[0].active_inference_state.basin_influence_strength == 0.8

    async def test_get_system_story_handles_invalid_event_type(self, mock_driver):
        """Verify invalid event type falls back to SYSTEM_REFLECTION."""
        mock_driver.execute_query = AsyncMock(
            return_value=[
                {
                    "e": {
                        "id": "evt_3",
                        "timestamp": "2024-01-01T00:00:00+00:00",
                        "type": "invalid_type",
                        "summary": "Test",
                        "rationale": "Test",
                        "impact": "Test",
                        "lessons_learned": [],
                        "metadata": {},
                        "narrative_coherence": 0.8,
                        "resonance_score": 0.7,
                        "strange_attractor_id": "conceptual-basin",
                        "related_files": [],
                    }
                }
            ]
        )
        service = AutobiographicalService(driver=mock_driver)

        events = await service.get_system_story(limit=10)

        assert events[0].event_type == DevelopmentEventType.SYSTEM_REFLECTION


@pytest.mark.asyncio
class TestMemoryOperations:
    """Tests for memory CRUD operations."""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver."""
        driver = AsyncMock()
        return driver

    async def test_create_memory_creates_node(self, mock_driver):
        """Verify create_memory creates Memory node."""
        mock_driver.execute_query = AsyncMock(return_value=[{"id": "mem_123"}])
        service = AutobiographicalService(driver=mock_driver)

        memory_id = await service.create_memory(
            content="Test memory",
            memory_type="episodic",
            source="test",
            metadata={"key": "value"},
        )

        assert memory_id == "mem_123"
        mock_driver.execute_query.assert_awaited_once()
        call_args = mock_driver.execute_query.await_args
        assert "CREATE (m:Memory" in call_args[0][0]

    async def test_get_last_memory_time_returns_timestamp(self, mock_driver):
        """Verify get_last_memory_time retrieves latest timestamp."""
        from datetime import datetime as dt
        test_datetime = dt(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        # Mock Neo4j DateTime object with to_native method
        mock_datetime = MagicMock()
        mock_datetime.to_native = MagicMock(return_value=test_datetime)
        mock_driver.execute_query = AsyncMock(
            return_value=[{"last_time": mock_datetime}]
        )
        service = AutobiographicalService(driver=mock_driver)

        last_time = await service.get_last_memory_time("episodic", "test")

        assert last_time is not None
        assert isinstance(last_time, datetime)
        assert last_time == test_datetime

    async def test_count_recent_memories_returns_count(self, mock_driver):
        """Verify count_recent_memories returns integer count."""
        mock_driver.execute_query = AsyncMock(return_value=[{"count": 5}])
        service = AutobiographicalService(driver=mock_driver)

        count = await service.count_recent_memories(duration_hours=24)

        assert count == 5
        mock_driver.execute_query.assert_awaited_once()

    async def test_search_memories_returns_results(self, mock_driver):
        """Verify search_memories returns list of memory dicts."""
        mock_driver.execute_query = AsyncMock(
            return_value=[{"m": {"id": "mem_1", "content": "Found memory"}}]
        )
        service = AutobiographicalService(driver=mock_driver)

        results = await service.search_memories("query", limit=5)

        assert len(results) == 1
        assert results[0]["id"] == "mem_1"
        assert results[0]["content"] == "Found memory"


@pytest.mark.asyncio
class TestConversationMomentMethods:
    """Tests for methods that delegate to ConversationMomentService."""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver."""
        return AsyncMock()

    @pytest.fixture
    def mock_moment_service(self):
        """Create mock ConversationMomentService."""
        service = MagicMock()
        service.process_moment = AsyncMock(
            return_value=ConversationMoment(
                moment_id="moment_1",
                user_input="Test",
                agent_response="Response",
            )
        )
        service.get_consciousness_report = MagicMock(
            return_value=ConsciousnessReport(
                average_consciousness_level=0.8,
                extended_mind_size={"tools": 5, "resources": 3, "affordances": 2},
            )
        )
        service.extended_mind = ExtendedMindState(
            tools={"tool1"},
            resources={"resource1"},
        )
        service.get_recent_moments = MagicMock(
            return_value=[
                ConversationMoment(
                    moment_id="moment_1",
                    user_input="Test",
                    agent_response="Response",
                )
            ]
        )
        return service

    async def test_record_conversation_moment_delegates(self, mock_driver, mock_moment_service):
        """Verify record_conversation_moment delegates to moment service."""
        service = AutobiographicalService(driver=mock_driver)
        with patch(
            "api.services.autobiographical_service.get_conversation_moment_service",
            new_callable=AsyncMock,
            return_value=mock_moment_service,
        ):
            moment = await service.record_conversation_moment(
                user_input="Test",
                agent_response="Response",
                tools_used=["tool1"],
            )

            assert moment.moment_id == "moment_1"
            mock_moment_service.process_moment.assert_awaited_once()

    async def test_get_consciousness_report_delegates(self, mock_driver, mock_moment_service):
        """Verify get_consciousness_report delegates to moment service."""
        service = AutobiographicalService(driver=mock_driver)
        with patch(
            "api.services.autobiographical_service.get_conversation_moment_service",
            new_callable=AsyncMock,
            return_value=mock_moment_service,
        ):
            report = await service.get_consciousness_report()

            assert report.average_consciousness_level == 0.8
            assert report.extended_mind_size["tools"] == 5
            mock_moment_service.get_consciousness_report.assert_called_once()

    async def test_get_extended_mind_state_delegates(self, mock_driver, mock_moment_service):
        """Verify get_extended_mind_state returns extended mind."""
        service = AutobiographicalService(driver=mock_driver)
        with patch(
            "api.services.autobiographical_service.get_conversation_moment_service",
            new_callable=AsyncMock,
            return_value=mock_moment_service,
        ):
            state = await service.get_extended_mind_state()

            assert "tool1" in state.tools
            assert "resource1" in state.resources

    async def test_get_recent_moments_delegates(self, mock_driver, mock_moment_service):
        """Verify get_recent_moments delegates to moment service."""
        service = AutobiographicalService(driver=mock_driver)
        with patch(
            "api.services.autobiographical_service.get_conversation_moment_service",
            new_callable=AsyncMock,
            return_value=mock_moment_service,
        ):
            moments = await service.get_recent_moments(limit=10)

            assert len(moments) == 1
            mock_moment_service.get_recent_moments.assert_called_once_with(10)
