import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from api.services.context_packaging import BiographicalConstraintCell, CellPriority
from api.models.autobiographical import AutobiographicalJourney
from api.agents.consciousness_manager import ConsciousnessManager

@pytest.mark.asyncio
async def test_biographical_constraint_cell_formatting():
    """Test that the cell generates correct XML content."""
    cell = BiographicalConstraintCell(
        cell_id="test_cell",
        content="",
        priority=CellPriority.CRITICAL,
        token_count=100,
        journey_id="Journey to the West",
        unresolved_themes=["Enlightenment", "Discipline"],
        identity_markers=["Monkey King", "Pilgrim"]
    )
    
    assert 'journey="Journey to the West"' in cell.content
    assert "<theme>Enlightenment</theme>" in cell.content
    assert "<theme>Discipline</theme>" in cell.content
    assert "<marker>Monkey King</marker>" in cell.content
    assert "<biographical_constraints" in cell.content

@pytest.mark.asyncio
async def test_fetch_biographical_context():
    """Test that ConsciousnessManager fetches and packages the active journey."""
    
    # Mock the store
    mock_store = AsyncMock()
    mock_journey = AutobiographicalJourney(
        journey_id="j1",
        title="Test Journey",
        description="A test journey",
        themes={"Growth", "Integration"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_store.get_active_journey.return_value = mock_journey
    
    with patch("api.agents.consciousness_manager.get_consolidated_memory_store", return_value=mock_store):
        cm = ConsciousnessManager()
        
        # Test the method directly
        cell = await cm._fetch_biographical_context()
        
        assert cell is not None
        assert isinstance(cell, BiographicalConstraintCell)
        assert cell.journey_id == "Test Journey"
        assert "Growth" in cell.unresolved_themes or "Integration" in cell.unresolved_themes
        assert cell.priority == CellPriority.CRITICAL
        
        # Verify store call
        mock_store.get_active_journey.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_biographical_context_no_journey():
    """Test behavior when no active journey exists."""
    mock_store = AsyncMock()
    mock_store.get_active_journey.return_value = None
    
    with patch("api.agents.consciousness_manager.get_consolidated_memory_store", return_value=mock_store):
        cm = ConsciousnessManager()
        cell = await cm._fetch_biographical_context()
        assert cell is None
