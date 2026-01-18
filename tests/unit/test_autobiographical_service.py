import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
from api.services.autobiographical_service import AutobiographicalService


@pytest.mark.asyncio
async def test_record_event_merges_basin_for_resonance_link():
    mock_driver = AsyncMock()
    mock_driver.execute_query = AsyncMock(return_value=[])

    service = AutobiographicalService(driver=mock_driver)
    event = DevelopmentEvent(
        event_id="evt_1",
        timestamp=datetime.now(timezone.utc),
        event_type=DevelopmentEventType.GENESIS,
        summary="Event 1",
        rationale="Testing",
        impact="None",
        strange_attractor_id="conceptual-basin",
    )

    await service.record_event(event)

    assert mock_driver.execute_query.called
    cypher = mock_driver.execute_query.call_args[0][0]
    params = mock_driver.execute_query.call_args[0][1]

    assert "MERGE (b:AttractorBasin" in cypher
    assert "ON CREATE SET" in cypher
    assert params["basin_description"]
    assert isinstance(params["basin_concepts"], list)
    assert params["basin_strength"] > 0
