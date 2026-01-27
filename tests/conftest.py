"""
Shared Pytest Configuration and Fixtures
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# Mock Neo4j Driver (prevents real webhook connections)
# =============================================================================

@pytest.fixture(autouse=True)
def mock_neo4j_driver():
    """
    Auto-applied fixture that mocks the Neo4j webhook driver.
    This prevents tests from trying to connect to real n8n webhooks.
    """
    mock_driver = AsyncMock()
    mock_driver.execute_query = AsyncMock(return_value=[])
    
    # Track 041 (T041-022): Unified mocking of Neo4j driver
    with patch('api.services.webhook_neo4j_driver.get_neo4j_driver', return_value=mock_driver):
        with patch('api.services.remote_sync.get_neo4j_driver', return_value=mock_driver):
            yield mock_driver


@pytest.fixture(autouse=True)
def mock_graphiti_service():
    """
    Auto-applied fixture that mocks Graphiti service.
    Prevents tests from trying to connect to real Neo4j.
    """
    mock_service = AsyncMock()
    mock_service.ingest_message = AsyncMock(return_value=None)
    mock_service.ingest_extracted_relationships = AsyncMock(return_value={"ingested": 0, "skipped": 0, "errors": []})
    mock_service.extract_with_context = AsyncMock(return_value={
        "entities": [],
        "relationships": [],
        "approved_count": 0,
        "pending_count": 0,
        "model_used": "test"
    })

    with patch('api.services.belief_tracking_service.get_graphiti_service', return_value=mock_service):
        yield mock_service


@pytest.fixture(autouse=True)
def reset_belief_tracking_singleton():
    """
    Reset the BeliefTrackingService singleton between tests.
    """
    import api.services.belief_tracking_service as bt_module
    bt_module._belief_tracking_service = None
    yield
    bt_module._belief_tracking_service = None


# =============================================================================
# API Fixtures
# =============================================================================

@pytest.fixture
async def client():
    """Async client for integration testing."""
    from httpx import AsyncClient, ASGITransport
    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Belief Tracking Fixtures (Feature 036)
# =============================================================================

@pytest.fixture
def belief_tracking_service():
    """Get fresh BeliefTrackingService instance for testing."""
    from api.services.belief_tracking_service import BeliefTrackingService
    # Create fresh service instance (not singleton) for test isolation
    service = BeliefTrackingService()
    yield service
    # Clear journeys after test
    service._journeys.clear()


@pytest.fixture
async def sample_journey(belief_tracking_service):
    """Create a sample journey for testing."""
    journey = await belief_tracking_service.create_journey(participant_id="test_participant_001")
    return journey


@pytest.fixture
async def sample_limiting_belief(belief_tracking_service, sample_journey):
    """Create a sample limiting belief for testing."""
    belief = await belief_tracking_service.identify_limiting_belief(
        journey_id=sample_journey.id,
        content="I must always be exceptional—good enough is never enough",
        pattern_name="perfectionism_trap",
        origin_memory="Early school achievement pressure",
        self_talk=["I should have done better", "This isn't good enough"],
        mental_blocks=["Fear of delegation", "Analysis paralysis"],
        self_sabotage_behaviors=["Overworking", "Procrastinating on imperfect work"],
        protects_from="Fear of being seen as mediocre"
    )
    return belief


@pytest.fixture
async def sample_empowering_belief(belief_tracking_service, sample_journey):
    """Create a sample empowering belief for testing."""
    belief = await belief_tracking_service.propose_empowering_belief(
        journey_id=sample_journey.id,
        content="My worth is inherent, not earned through perfection",
        bridge_version="I am learning to accept good enough as valuable",
        replaces_belief_id=None
    )
    return belief


@pytest.fixture
async def sample_experiment(belief_tracking_service, sample_journey, sample_limiting_belief):
    """Create a sample experiment for testing."""
    experiment = await belief_tracking_service.design_experiment(
        journey_id=sample_journey.id,
        limiting_belief_id=sample_limiting_belief.id,
        empowering_belief_id=None,
        hypothesis="Delegating this task will not result in failure",
        action_to_take="Delegate the quarterly report to my team lead",
        context="mid"
    )
    return experiment


@pytest.fixture
async def sample_replay_loop(belief_tracking_service, sample_journey):
    """Create a sample replay loop for testing."""
    loop = await belief_tracking_service.identify_replay_loop(
        journey_id=sample_journey.id,
        trigger_situation="After a meeting where I spoke assertively",
        story_text="I was too harsh. Everyone thinks I am difficult.",
        emotion="shame",
        fear_underneath="Fear of being rejected or disliked",
        pattern_name="assertiveness_shame",
        fed_by_belief_id=None
    )
    return loop
