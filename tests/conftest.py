"""
Shared Pytest Configuration and Fixtures
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator

# =============================================================================
# Async Support
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create session-wide event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

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
def sample_journey(belief_tracking_service):
    """Create a sample journey for testing."""
    journey = belief_tracking_service.create_journey(participant_id="test_participant_001")
    return journey


@pytest.fixture
def sample_limiting_belief(belief_tracking_service, sample_journey):
    """Create a sample limiting belief for testing."""
    belief = belief_tracking_service.identify_limiting_belief(
        journey=sample_journey,
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
def sample_empowering_belief(belief_tracking_service, sample_journey):
    """Create a sample empowering belief for testing."""
    belief = belief_tracking_service.propose_empowering_belief(
        journey=sample_journey,
        content="My worth is inherent, not earned through perfection",
        bridge_version="I am learning to accept good enough as valuable",
        replaces_belief_id=None
    )
    return belief


@pytest.fixture
def sample_experiment(belief_tracking_service, sample_journey, sample_limiting_belief):
    """Create a sample experiment for testing."""
    experiment = belief_tracking_service.design_experiment(
        journey=sample_journey,
        limiting_belief_id=sample_limiting_belief.id,
        empowering_belief_id=None,
        hypothesis="Delegating this task will not result in failure",
        action_to_take="Delegate the quarterly report to my team lead",
        context="mid"
    )
    return experiment


@pytest.fixture
def sample_replay_loop(belief_tracking_service, sample_journey):
    """Create a sample replay loop for testing."""
    loop = belief_tracking_service.identify_replay_loop(
        journey=sample_journey,
        trigger_situation="After a meeting where I spoke assertively",
        story_text="I was too harsh. Everyone thinks I am difficult.",
        emotion="shame",
        fear_underneath="Fear of being rejected or disliked",
        pattern_name="assertiveness_shame",
        fed_by_belief_id=None
    )
    return loop