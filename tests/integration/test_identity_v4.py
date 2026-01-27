import pytest
import asyncio
from api.services.session_manager import get_session_manager
from api.agents.consolidated_memory_stores import get_consolidated_memory_store
from dionysus_mcp.tools.recall import semantic_recall_tool


def test_identity_aware_recall_isolation():
    """
    TDD Test: Verifies that memories are isolated by device_id.
    """
    store = get_consolidated_memory_store()
    session_mgr = get_session_manager()
    
    device_a = "device_alpha"
    device_b = "device_beta"
    
    # 1. Create a journey for Device A
    journey_a = await session_mgr.get_or_create_journey(
        device_id=device_a,
        participant_id="user_alpha"
    )
    
    # 2. Add a memory (via Graphiti/MemEvolve would be better, but we'll mock or use the store directly if possible)
    # For simplicity in this test, we want to see if get_active_journey filters correctly
    
    # Device A's journey should be visible to Device A
    active_a = await store.get_active_journey(device_id=device_a)
    assert active_a is not None
    assert active_a.participant_id == "user_alpha"
    
    # Device A's journey should NOT be visible to Device B
    active_b = await store.get_active_journey(device_id=device_b)
    assert active_b is None or active_b.participant_id != "user_alpha"


def test_recall_tool_device_filtering():
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
