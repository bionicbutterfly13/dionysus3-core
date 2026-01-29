import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from api.services.reconstruction_service import (
    ReconstructionService,
    ReconstructionContext,
    Fragment,
    FragmentType
)

@pytest.mark.asyncio
async def test_guidance_forced_retrieval():
    """
    Test that subconscious guidance can force the retrieval of a specific entity
    even if it's not in the main project scan.
    """
    # 1. Setup Mock Graphiti
    mock_graphiti = AsyncMock()
    # Mock search to return nothing significant
    mock_graphiti.search.return_value = {"edges": []}
    # Mock Cypher to return a specific "forgotten" node when biased
    mock_graphiti.execute_cypher.return_value = [
        {
            "id": "forgotten-123",
            "name": "Secret Project X",
            "summary": "This was a forgotten breakthrough.",
            "created_at": "2023-01-01T00:00:00Z"
        }
    ]

    # 2. Setup Context with Guidance
    context = ReconstructionContext(
        project_path="/tmp",
        project_name="CurrentProject",
        subconscious_guidance="Spontaneous Recall: 'Secret Project X' surfaced from the depths."
    )

    # 3. Initialize Service
    with patch("api.services.reconstruction_service.get_graphiti_service", return_value=mock_graphiti):
        service = ReconstructionService(graphiti_enabled=True)
        
        # 4. Run Scan
        await service._scan_fragments(context)
        
        # 5. Verify forced retrieval
        # Fragments should contain our forced node
        forced_fragments = [f for f in service._fragments if f.source == "subconscious_forced"]
        assert len(forced_fragments) == 1
        assert forced_fragments[0].content == "Secret Project X"
        assert forced_fragments[0].fragment_id == "forgotten-123"

@pytest.mark.asyncio
async def test_guidance_resonance_bias():
    """
    Test that subconscious guidance amplifies the resonance of matching fragments.
    """
    service = ReconstructionService()
    
    # 1. Create a fragment that matches guidance
    fragment = Fragment(
        fragment_id="f1",
        fragment_type=FragmentType.EPISODIC,
        content="We should focus on performance optimization.",
        summary="Performance focus",
        source="test"
    )
    
    # 2. Context with guidance bias towards 'performance'
    context = ReconstructionContext(
        project_path="/tmp",
        project_name="Test",
        subconscious_guidance="## Drive Alerts\n- **CURIOSITY** is low. Focus on performance bottlenecks."
    )
    
    # 3. Manually add fragment and activate resonance
    service._fragments = [fragment]
    
    # Mock other resonance factors to be 0 for isolation
    with patch.object(service, '_calculate_cue_resonance', return_value=0.0):
        with patch.object(service, '_calculate_context_resonance', return_value=0.0):
            with patch.object(service, '_calculate_network_resonance', return_value=0.0):
                service._activate_resonance(context)
                
    # 4. Verify bias
    # Bias weight is 0.2. Overlap with 'performance' should give bias > 0.5.
    # Base bias is 0.5. 'performance' should add 0.1 -> 0.6.
    # Resonance = 0.6 * 0.2 = 0.12 (if others are 0)
    assert fragment.resonance_score > 0
    
    # Compare with a non-matching fragment
    fragment2 = Fragment(
        fragment_id="f2",
        fragment_type=FragmentType.EPISODIC,
        content="Lunch was good.",
        source="test"
    )
    service._fragments = [fragment2]
    with patch.object(service, '_calculate_cue_resonance', return_value=0.0):
        with patch.object(service, '_calculate_context_resonance', return_value=0.0):
            with patch.object(service, '_calculate_network_resonance', return_value=0.0):
                service._activate_resonance(context)
                
    # Matching fragment should have higher resonance than non-matching
    # Assuming both have same baseline resonance (0.5 * 0.2 = 0.1)
    # The matching one should be 0.6 * 0.2 = 0.12
    assert fragment.resonance_score > 0.1

@pytest.mark.asyncio
async def test_automatic_guidance_hydration():
    """
    Test that ReconstructionService automatically fetches guidance from DreamService
    if it's not provided in the context.
    """
    mock_dream_svc = AsyncMock()
    mock_dream_svc.generate_guidance.return_value = "Subconscious guidance: 'Forgotten Node'"
    
    mock_graphiti = AsyncMock()
    mock_graphiti.search.return_value = {"edges": []}
    mock_graphiti.execute_cypher.return_value = []
    
    context = ReconstructionContext(project_name="TestProject", project_path="/tmp")
    
    # Patch get_dream_service and reconstruct dependencies
    with patch("api.services.dream_service.get_dream_service", return_value=mock_dream_svc):
        with patch("api.services.reconstruction_service.get_graphiti_service", return_value=mock_graphiti):
            service = ReconstructionService()
            # We mock _scan_fragments to avoid actual network/DB calls beyond what we control
            with patch.object(service, '_scan_fragments', new_callable=AsyncMock) as mock_scan:
                await service.reconstruct(context)
                
                # Verify hydration was called
                mock_dream_svc.generate_guidance.assert_called_once()
                assert "Forgotten Node" in context.subconscious_guidance
