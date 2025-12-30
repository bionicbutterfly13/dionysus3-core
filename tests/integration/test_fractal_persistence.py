import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from dionysus_mcp.server import create_thoughtseed

@pytest.mark.asyncio
async def test_fractal_thought_persistence():
    """Verify create_thoughtseed supports child_thought_ids and parent_thought_id."""
    
    parent_id = str(uuid4())
    child_id = str(uuid4())
    
    # Mock Neo4j driver and session
    mock_row = {
        "id": parent_id,
        "layer": "metacognitive",
        "activation_level": 0.5,
        "competition_status": "pending"
    }
    
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_row)
    
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    with patch("dionysus_mcp.server.get_neo4j_driver", return_value=mock_driver):
        result = await create_thoughtseed(
            layer="metacognitive",
            content="Top level reflection",
            child_thought_ids=[child_id],
            parent_thought_id=None
        )
        
        assert result["id"] == parent_id
        
        # Verify Cypher query included the new fields
        call_args = mock_session.run.call_args
        cypher = call_args[0][0]
        params = call_args[1]
        
        assert "child_thought_ids: $child_thought_ids" in cypher
        assert "parent_thought_id: $parent_thought_id" in cypher
        assert params["child_thought_ids"] == [child_id]
        assert params["parent_thought_id"] is None
