import os
import pytest
import asyncio
from uuid import uuid4

# MOCK ENVIRONMENT FOR INTEGRATION TESTS
os.environ["NEO4J_PASSWORD"] = "test_pass"
os.environ["OPENAI_API_KEY"] = "sk-test"
os.environ["GRAPHITI_GROUP_ID"] = "integration_test"

from unittest.mock import AsyncMock, patch
from api.services.session_manager import get_session_manager
from api.agents.consolidated_memory_stores import get_consolidated_memory_store, ConsolidatedMemoryStore
from dionysus_mcp.tools.recall import semantic_recall_tool

@pytest.mark.asyncio
async def test_identity_aware_recall_isolation(mock_neo4j_driver):
    """
    TDD Test: Verifies that memories are isolated by device_id.
    """
    device_a = str(uuid4())
    device_b = str(uuid4())
    journey_id_a = str(uuid4())
    
    # Robust mock behavior
    async def side_effect(query, params=None, **kwargs):
        params = params or {}
        # 1. MATCH in SessionManager or store.get_active_journey
        if params.get("device_id") == device_a:
            data_map = {
                "journey_id": journey_id_a,
                "title": "Test Journey",
                "id": journey_id_a,
                "device_id": device_a,
                "created_at": "2026-01-27T10:00:00Z",
                "updated_at": "2026-01-27T10:00:00Z",
                "metadata": "{}",
                "participant_id": "user_alpha",
                "themes": [],
                "description": "Test journey",
                "_is_new": True
            }
            return [{
                "labels": ["Journey", "AutobiographicalJourney"],
                "data": data_map,
                "journey_data": data_map,
                "session_count": 0
            }]
        return []

    mock_neo4j_driver.execute_query.side_effect = side_effect
    
    # Force the store to use our mocked driver and bypass GraphitiService singleton
    store = ConsolidatedMemoryStore(driver=mock_neo4j_driver)
    session_mgr = get_session_manager()
    session_mgr._driver = mock_neo4j_driver
    
    # 1. Create a journey for Device A
    journey_a = await session_mgr.get_or_create_journey(
        device_id=device_a,
        participant_id="user_alpha"
    )
    
    assert str(journey_a.id) == journey_id_a
    
    # 2. Device A's journey should be visible to Device A
    active_a = await store.get_active_journey(device_id=device_a)
    assert active_a is not None
    assert active_a.journey_id == journey_id_a
    
    # 3. Device A's journey should NOT be visible to Device B (mock returns empty)
    active_b = await store.get_active_journey(device_id=device_b)
    assert active_b is None

@pytest.mark.asyncio
async def test_recall_tool_device_filtering():
    """
    Verifies that semantic_recall_tool accepts and uses device_id.
    """
    # This might fail if the tool doesn't propagate device_id to the search service
    # or if we haven't seeded data. Since we're in TDD, let's just assert the signature
    # and basic propagation logic if we can mock the search service.
    
    from unittest.mock import AsyncMock, patch
    
    with patch("dionysus_mcp.tools.recall.get_vector_search_service") as mock_get_service:
        mock_search = AsyncMock()
        mock_get_service.return_value.semantic_search = mock_search
        
        await semantic_recall_tool(
            query="Who am I?",
            device_id="test_device"
        )
        
        # Verify device_id reached the service
        args, kwargs = mock_search.call_args
        filters = kwargs.get("filters")
        assert filters is not None
        assert filters.device_id == "test_device"
