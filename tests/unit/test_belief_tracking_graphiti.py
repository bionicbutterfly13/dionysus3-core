"""
Unit Tests for BeliefTrackingService Graphiti Integration

Verifies that Graphiti ingestion methods are called correctly,
preventing silent failures from going undetected.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

pytestmark = pytest.mark.asyncio


class TestGraphitiIngestion:
    """Tests to ensure Graphiti ingestion is actually called."""

    @pytest.fixture
    def mock_graphiti(self):
        """Create a mock Graphiti service."""
        mock = AsyncMock()
        mock.ingest_message = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def belief_service(self):
        """Get fresh BeliefTrackingService instance."""
        from api.services.belief_tracking_service import BeliefTrackingService
        return BeliefTrackingService()

    async def test_journey_creation_calls_graphiti(self, belief_service, mock_graphiti):
        """Verify creating a journey triggers Graphiti ingestion."""
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=mock_graphiti
        ):
            journey = await belief_service.create_journey(participant_id="test_001")
            
            # Graphiti should be called for journey creation event
            assert mock_graphiti.ingest_message.called
            call_args = mock_graphiti.ingest_message.call_args
            assert "JOURNEY EVENT" in call_args.kwargs.get('content', '') or \
                   "JOURNEY EVENT" in str(call_args)

    async def test_belief_identification_calls_graphiti(self, belief_service, mock_graphiti):
        """Verify identifying a belief triggers Graphiti ingestion."""
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=mock_graphiti
        ):
            # Create journey first
            journey = await belief_service.create_journey(participant_id="test_002")
            mock_graphiti.ingest_message.reset_mock()
            
            # Identify belief
            belief = await belief_service.identify_limiting_belief(
                journey_id=journey.id,
                content="I am not good enough",
                pattern_name="unworthiness"
            )
            
            # Graphiti should be called for belief event
            assert mock_graphiti.ingest_message.called
            call_args = mock_graphiti.ingest_message.call_args
            content = call_args.kwargs.get('content', str(call_args))
            assert "BELIEF" in content or "limiting" in content.lower()

    async def test_replay_loop_resolution_calls_graphiti(self, belief_service, mock_graphiti):
        """Verify resolving a replay loop triggers Graphiti ingestion."""
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=mock_graphiti
        ):
            # Create journey and loop
            journey = await belief_service.create_journey(participant_id="test_003")
            loop = await belief_service.identify_replay_loop(
                journey_id=journey.id,
                trigger_situation="After a meeting",
                story_text="I said something wrong",
                emotion="anxiety",
                fear_underneath="Fear of rejection"
            )
            mock_graphiti.ingest_message.reset_mock()
            
            # Resolve loop
            resolved = await belief_service.resolve_replay_loop(
                journey_id=journey.id,
                loop_id=loop.id,
                lesson_found="My worth isn't defined by one interaction",
                comfort_offered="I am learning and growing"
            )
            
            # Graphiti should be called for replay event
            assert mock_graphiti.ingest_message.called

    async def test_graphiti_failure_logs_warning(self, belief_service, caplog):
        """Verify Graphiti failures are logged, not silently swallowed."""
        import logging
        
        failing_graphiti = AsyncMock()
        failing_graphiti.ingest_message = AsyncMock(
            side_effect=Exception("Neo4j connection failed")
        )
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=failing_graphiti
        ):
            with caplog.at_level(logging.WARNING):
                journey = await belief_service.create_journey(participant_id="test_004")
                
                # Should log warning about failure
                assert any(
                    "Failed to ingest" in record.message 
                    for record in caplog.records
                )

    async def test_graphiti_failure_does_not_break_operation(self, belief_service):
        """Verify operations succeed even when Graphiti fails (graceful degradation)."""
        failing_graphiti = AsyncMock()
        failing_graphiti.ingest_message = AsyncMock(
            side_effect=Exception("Neo4j unavailable")
        )
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=failing_graphiti
        ):
            # Operation should still succeed
            journey = await belief_service.create_journey(participant_id="test_005")
            assert journey is not None
            assert journey.id is not None
            
            # Can still identify beliefs
            belief = await belief_service.identify_limiting_belief(
                journey_id=journey.id,
                content="Test belief"
            )
            assert belief is not None


class TestGraphitiPayloads:
    """Tests to verify correct payload structure for Graphiti."""

    @pytest.fixture
    def belief_service(self):
        from api.services.belief_tracking_service import BeliefTrackingService
        return BeliefTrackingService()

    async def test_belief_payload_contains_required_fields(self, belief_service):
        """Verify belief ingestion payload has all required fields."""
        mock_graphiti = AsyncMock()
        mock_graphiti.ingest_message = AsyncMock(return_value=None)
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=mock_graphiti
        ):
            journey = await belief_service.create_journey(participant_id="test_payload")
            mock_graphiti.ingest_message.reset_mock()
            
            await belief_service.identify_limiting_belief(
                journey_id=journey.id,
                content="I must be perfect",
                pattern_name="perfectionism",
                protects_from="Fear of failure"
            )
            
            # Check the call was made with proper structure
            assert mock_graphiti.ingest_message.called
            call_kwargs = mock_graphiti.ingest_message.call_args.kwargs
            
            assert 'content' in call_kwargs
            assert 'source_description' in call_kwargs
            assert call_kwargs['source_description'] == 'ias_belief_tracking'

    async def test_group_id_uses_journey_graphiti_id(self, belief_service):
        """Verify events use journey's graphiti_group_id for grouping."""
        mock_graphiti = AsyncMock()
        mock_graphiti.ingest_message = AsyncMock(return_value=None)
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=mock_graphiti
        ):
            journey = await belief_service.create_journey(participant_id="test_group")
            
            # Check group_id is passed
            call_kwargs = mock_graphiti.ingest_message.call_args.kwargs
            assert 'group_id' in call_kwargs
            assert journey.graphiti_group_id in call_kwargs['group_id']


class TestIngestionTracking:
    """Tests for ingestion health tracking - ensures no silent failures."""

    @pytest.fixture
    def belief_service(self):
        from api.services.belief_tracking_service import BeliefTrackingService
        return BeliefTrackingService()

    async def test_initial_ingestion_health_is_clean(self, belief_service):
        """Verify new service has clean ingestion state."""
        health = belief_service.get_ingestion_health()
        
        assert health["total_attempts"] == 0
        assert health["successful"] == 0
        assert health["failed"] == 0
        assert health["success_rate"] == 1.0
        assert health["healthy"] is True
        assert health["recent_failures"] == []

    async def test_successful_ingestion_increments_counter(self, belief_service):
        """Verify successful ingestions are tracked."""
        mock_graphiti = AsyncMock()
        mock_graphiti.ingest_message = AsyncMock(return_value=None)
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=mock_graphiti
        ):
            await belief_service.create_journey(participant_id="test_track_001")
            
            health = belief_service.get_ingestion_health()
            assert health["total_attempts"] >= 1
            assert health["successful"] >= 1
            assert health["failed"] == 0
            assert health["healthy"] is True

    async def test_failed_ingestion_tracked_in_failures(self, belief_service):
        """Verify failed ingestions are tracked with details."""
        failing_graphiti = AsyncMock()
        failing_graphiti.ingest_message = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=failing_graphiti
        ):
            await belief_service.create_journey(participant_id="test_track_002")
            
            health = belief_service.get_ingestion_health()
            assert health["total_attempts"] >= 1
            assert health["failed"] >= 1
            assert health["healthy"] is False
            assert len(health["recent_failures"]) >= 1
            
            # Verify failure details
            failure = health["recent_failures"][0]
            assert "type" in failure
            assert "journey_id" in failure
            assert "error" in failure
            assert "Connection refused" in failure["error"]
            assert "timestamp" in failure

    async def test_success_rate_calculation(self, belief_service):
        """Verify success rate is calculated correctly."""
        mock_graphiti = AsyncMock()
        call_count = 0
        
        async def sometimes_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("Intermittent failure")
            return None
        
        mock_graphiti.ingest_message = AsyncMock(side_effect=sometimes_fail)
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=mock_graphiti
        ):
            # Create multiple journeys to trigger multiple ingestions
            for i in range(4):
                await belief_service.create_journey(participant_id=f"test_rate_{i}")
            
            health = belief_service.get_ingestion_health()
            # Should have some successes and some failures
            assert health["total_attempts"] >= 4
            assert 0 < health["success_rate"] < 1.0

    async def test_clear_failed_ingestions(self, belief_service):
        """Verify failed ingestions can be cleared."""
        failing_graphiti = AsyncMock()
        failing_graphiti.ingest_message = AsyncMock(
            side_effect=Exception("Test failure")
        )
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=failing_graphiti
        ):
            await belief_service.create_journey(participant_id="test_clear")
            
            # Verify failures exist
            health = belief_service.get_ingestion_health()
            assert health["failed"] >= 1
            
            # Clear failures
            cleared = belief_service.clear_failed_ingestions()
            assert cleared >= 1
            
            # Verify cleared
            health = belief_service.get_ingestion_health()
            assert health["failed"] == 0
            assert health["healthy"] is True

    async def test_recent_failures_limited_to_ten(self, belief_service):
        """Verify only last 10 failures are kept in recent_failures."""
        failing_graphiti = AsyncMock()
        failing_graphiti.ingest_message = AsyncMock(
            side_effect=Exception("Repeated failure")
        )
        
        with patch(
            'api.services.belief_tracking_service.get_graphiti_service',
            return_value=failing_graphiti
        ):
            # Create 15 journeys to trigger 15+ failures
            for i in range(15):
                await belief_service.create_journey(participant_id=f"test_limit_{i}")
            
            health = belief_service.get_ingestion_health()
            # recent_failures should be capped at 10
            assert len(health["recent_failures"]) <= 10
