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


@pytest.mark.asyncio
async def test_to_prior_constraints():
    """Test that BiographicalConstraintCell converts to PriorConstraints correctly."""
    from api.models.priors import PriorLevel, ConstraintType

    cell = BiographicalConstraintCell(
        cell_id="test_cell",
        content="",
        priority=CellPriority.CRITICAL,
        token_count=100,
        journey_id="Hero_Journey",
        unresolved_themes=["Self-Discovery", "Integration"],
        identity_markers=["Narrative Coherence"]
    )

    constraints = cell.to_prior_constraints()

    # Should have 3 constraints: 2 themes + 1 identity marker
    assert len(constraints) == 3

    # Check theme constraints
    theme_constraints = [c for c in constraints if "theme" in c.name]
    assert len(theme_constraints) == 2
    for c in theme_constraints:
        assert c.level == PriorLevel.LEARNED
        assert c.constraint_type == ConstraintType.PREFER
        assert c.precision == 0.6  # Uses precision, not weight
        assert c.metadata.get("source") == "biographical"
        assert c.metadata.get("journey_id") == "Hero_Journey"

    # Check identity constraint
    id_constraints = [c for c in constraints if "identity" in c.name]
    assert len(id_constraints) == 1
    assert id_constraints[0].precision == 0.75  # Higher precision for identity


@pytest.mark.asyncio
async def test_prior_merge_on_fetch_biographical_context():
    """Test that fetching biographical context merges priors into hierarchy."""
    from api.models.priors import PriorHierarchy

    # Mock the store
    mock_store = AsyncMock()
    mock_journey = AutobiographicalJourney(
        journey_id="j1",
        title="Test Journey",
        description="A test journey",
        themes={"Growth"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_store.get_active_journey.return_value = mock_journey

    # Mock the prior persistence service
    mock_persistence = AsyncMock()
    mock_hierarchy = PriorHierarchy(
        agent_id="dionysus-1",
        basal_priors=[],
        dispositional_priors=[],
        learned_priors=[]
    )
    mock_persistence.hydrate_hierarchy.return_value = mock_hierarchy

    with patch("api.agents.consciousness_manager.get_consolidated_memory_store", return_value=mock_store):
        # Patch at the module where the import happens (inside the function)
        with patch("api.services.prior_persistence_service.get_prior_persistence_service", return_value=mock_persistence):
            cm = ConsciousnessManager()
            cell = await cm._fetch_biographical_context(agent_id="dionysus-1")

            assert cell is not None
            # The hierarchy should have merged priors
            # (Note: The hierarchy object is modified in place during the call)
            assert len(mock_hierarchy.learned_priors) > 0
            # Check that one of them is biographical
            bio_priors = [p for p in mock_hierarchy.learned_priors if p.metadata.get("source") == "biographical"]
            assert len(bio_priors) > 0
