import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.context_packaging import TokenBudgetManager, ContextCell, CellPriority
from datetime import datetime

@pytest.mark.asyncio
async def test_critical_cell_persistence_trigger():
    """Verify that adding a CRITICAL cell triggers async persistence to Graphiti."""
    # 1. Setup mocks
    mock_graphiti = AsyncMock()
    mock_graphiti.execute_cypher = AsyncMock(return_value=[])
    
    with patch("api.services.graphiti_service.get_graphiti_service", return_value=mock_graphiti):
        manager = TokenBudgetManager(total_budget=1000)
        
        test_cell = ContextCell(
            cell_id="test-critical",
            content="Must remember this",
            priority=CellPriority.CRITICAL,
            token_count=10
        )
        
        # 2. Add cell
        manager.add_cell(test_cell)
        
        # 3. Wait for fire-and-forget task
        # We give it a small sleep since it's an asyncio.create_task
        await asyncio.sleep(0.5)
        
        # 4. Verify Graphiti was called
        mock_graphiti.execute_cypher.assert_called_once()
        args, kwargs = mock_graphiti.execute_cypher.call_args
        assert "MERGE (c:ContextCell {id: $id})" in args[0]
        assert args[1]["id"] == "test-critical"
        assert args[1]["priority"] == "critical"

@pytest.mark.asyncio
async def test_ephemeral_cell_no_persistence():
    """Verify that EPHEMERAL cells do NOT trigger persistence."""
    mock_graphiti = AsyncMock()
    
    with patch("api.services.graphiti_service.get_graphiti_service", return_value=mock_graphiti):
        manager = TokenBudgetManager(total_budget=1000)
        
        test_cell = ContextCell(
            cell_id="test-ephemeral",
            content="Safe to forget",
            priority=CellPriority.EPHEMERAL,
            token_count=5
        )
        
        manager.add_cell(test_cell)
        await asyncio.sleep(0.5)
        
        mock_graphiti.execute_cypher.assert_not_called()
