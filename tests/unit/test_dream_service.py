"""
Unit Tests for DreamService
Feature: 069-hexis-subconscious-integration

Verifies:
- Drive initialization
- Drive decay logic
- Maintenance cycle execution
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from api.services.dream_service import DreamService, SubconsciousState, DriveType
from api.models.hexis_ontology import Neighborhood

@pytest.fixture
def mock_graphiti():
    return AsyncMock()

@pytest.fixture
def dream_service(mock_graphiti):
    service = DreamService(mock_graphiti)
    return service

@pytest.mark.asyncio
async def test_drive_initialization(dream_service):
    """Verify all drives are initialized to 0.5"""
    state = await dream_service.get_subconscious_state()
    assert len(state.drives) == len(DriveType)
    for drive in state.drives.values():
        assert drive.level == 0.5
        assert isinstance(drive.drive_type, DriveType)

@pytest.mark.asyncio
async def test_drive_decay(dream_service):
    """Verify drives decay over time"""
    # Manually set a drive to 1.0 updated 10 hours ago
    target_drive = DriveType.SURVIVAL
    state = await dream_service.get_subconscious_state()
    
    state.drives[target_drive].level = 1.0
    # Set update time to 10 hours ago
    state.drives[target_drive].last_updated = datetime.utcnow() - timedelta(hours=10)
    # Default decay is 0.01 per hour -> 0.1 total decay
    
    # Run maintenance
    await dream_service.run_maintenance_cycle()
    
    # Check new level
    # 1.0 - (0.01 * 10) = 0.9
    new_level = state.drives[target_drive].level
    assert new_level == pytest.approx(0.9, abs=0.01)
    
    # Check timestamp updated
    assert (datetime.utcnow() - state.drives[target_drive].last_updated).total_seconds() < 10

@pytest.mark.asyncio
async def test_maintenance_cycle_output(dream_service):
    """Verify maintenance cycle returns expected stats"""
    result = await dream_service.run_maintenance_cycle()
    
    assert "drives" in result
    assert "neighborhoods_updated" in result
    assert "nodes_pruned" in result
    
    assert result["neighborhoods_updated"] >= 0
    assert result["nodes_pruned"] >= 0

@pytest.mark.asyncio
async def test_guidance_generation(dream_service):
    """Verify guidance block is generated correctly"""
    # Force a low drive
    state = await dream_service.get_subconscious_state()
    state.drives[DriveType.REST].level = 0.1
    
    guidance = await dream_service.generate_guidance(context_summary="Testing context")
    
    assert "# Core Memory (Dionysus)" in guidance
    assert "REST: 0.10 [Need Action]" in guidance
    assert "Testing context" in guidance
    assert "Subconscious needs maintenance" in guidance # Since last_maintenance is None


