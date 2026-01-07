"""
Unit tests for Multi-Tier Memory Migration (Feature 047).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from api.models.memory_tier import MemoryTier, TieredMemoryItem
from api.services.multi_tier_service import MultiTierMemoryService

@pytest.mark.asyncio
async def test_hot_storage_retrieval():
    service = MultiTierMemoryService()
    item_id = await service.store_memory("Active session data", importance=0.9)
    
    retrieved = await service.retrieve_memory(item_id)
    assert retrieved is not None
    assert retrieved.content == "Active session data"
    assert retrieved.tier == MemoryTier.HOT

@pytest.mark.asyncio
async def test_migration_hot_to_warm():
    mock_driver = AsyncMock()
    # Pass mock driver to constructor
    service = MultiTierMemoryService(driver=mock_driver)
    
    # Store an item
    item_id = await service.store_memory("Old data", importance=0.5)
    
    # Manually backdate it to simulate expiration (>24h)
    service.hot._store[item_id].created_at = datetime.utcnow() - timedelta(hours=25)
    
    with patch("api.services.multi_tier_service.chat_completion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Summary."
        
        # Run migration
        reports_dict = await service.run_lifecycle_management()
        
        assert reports_dict["status"] == "success"
        assert reports_dict["hot_to_warm"] == 1
        
        # Verify it's gone from Hot
        assert item_id not in service.hot._store
        
        # Verify driver was called (via Warm manager)
        mock_driver.execute_query.assert_called()

@pytest.mark.asyncio
async def test_hierarchical_retrieval_fallback():
    mock_driver = AsyncMock()
    service = MultiTierMemoryService(driver=mock_driver)
    
    # Mock Neo4j to return a "Warm" item
    node_data = {
        "id": "warm-123",
        "content": "I am warm",
        "memory_type": "semantic",
        "importance_score": 0.8,
        "project_id": "p1"
    }
    
    # execute_query returns a list of records (dicts)
    mock_driver.execute_query.return_value = [{"m": node_data}]
    
    # Retrieve something NOT in Hot
    retrieved = await service.retrieve_memory("warm-123")
    
    assert retrieved is not None
    assert retrieved.content == "I am warm"
    assert retrieved.tier == MemoryTier.WARM
    mock_driver.execute_query.assert_called_once()
