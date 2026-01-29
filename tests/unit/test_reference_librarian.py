import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from api.services.reconstruction_service import ReconstructionService, ReconstructionContext, Fragment, FragmentType
from api.models.hexis_ontology import CognitiveModality

@pytest.fixture
def reconstruction_service():
    service = ReconstructionService()
    # Mock the internal methods to avoid actual DB scans
    service._scan_fragments = AsyncMock()
    service._calculate_subconscious_bias = MagicMock(return_value=0.5)
    return service

@pytest.mark.asyncio
async def test_reference_librarian_siege_suppression(reconstruction_service):
    """
    Verify that Reference Librarian suppresses SESSION and EPISODIC fragments during SIEGE_LOCKED.
    """
    context = ReconstructionContext(project_path="/tmp", project_name="test")
    
    # Create test fragments
    f1 = Fragment(fragment_id="1", fragment_type=FragmentType.SESSION, content="Long meta history", activation=1.0)
    f2 = Fragment(fragment_id="2", fragment_type=FragmentType.TASK, content="Discrete next step", activation=0.5)
    
    reconstruction_service._fragments = [f1, f2]
    
    # Run reconstruction with siege_locked modality
    await reconstruction_service.reconstruct(context, modality="siege_locked")
    
    # Check activation levels
    # SESSION (f1) should be suppressed (0.4 * resonance_score)
    # TASK (f2) should be boosted (1.5 * resonance_score)
    
    assert f1.activation < 0.5  # Suppressed
    assert f2.activation > 0.7  # Boosted

@pytest.mark.asyncio
async def test_reference_librarian_adhd_suppression(reconstruction_service):
    """
    Verify softer suppression during ADHD_EXPLORATORY.
    """
    context = ReconstructionContext(project_path="/tmp", project_name="test")
    
    f1 = Fragment(fragment_id="1", fragment_type=FragmentType.SESSION, content="History", activation=1.0)
    reconstruction_service._fragments = [f1]
    
    await reconstruction_service.reconstruct(context, modality="adhd_exploratory")
    
    # resonance_score was ~0.43 in mock run.
    # 0.43 * 0.7 = 0.301
    assert abs(f1.activation - 0.301) < 0.01
