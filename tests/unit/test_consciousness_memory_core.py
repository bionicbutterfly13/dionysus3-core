import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from api.agents.consciousness_memory_core import ConsciousnessMemoryCore
from api.models.autobiographical import (
    DevelopmentEvent,
    DevelopmentEpisode,
    DevelopmentEventType,
)


@pytest.mark.asyncio
async def test_segment_episode_retains_symbolic_residue():
    mock_store = AsyncMock()
    mock_store.store_event = AsyncMock()
    mock_store.update_journey = AsyncMock()

    mock_river = AsyncMock()
    mock_river.check_boundary = AsyncMock(return_value=True)
    mock_river.construct_episode = AsyncMock(
        return_value=DevelopmentEpisode(
            episode_id="ep_1",
            journey_id="journey_1",
            title="Test Episode",
            summary="Test summary",
            narrative="Test narrative",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            events=["evt_1"],
        )
    )
    mock_river.predict_and_calibrate = AsyncMock(
        return_value=(["Fact A"], {"active_goals": ["Goal 1"]})
    )

    with patch(
        "api.agents.consciousness_memory_core.get_consolidated_memory_store",
        return_value=mock_store,
    ), patch(
        "api.agents.consciousness_memory_core.get_nemori_river_flow",
        return_value=mock_river,
    ):
        core = ConsciousnessMemoryCore(journey_id="test")
        event = DevelopmentEvent(
            event_id="evt_1",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.GENESIS,
            summary="Event 1",
            rationale="Testing",
            impact="None",
        )

        await core.record_interaction(event)

        assert core.last_symbolic_residue == {"active_goals": ["Goal 1"]}
