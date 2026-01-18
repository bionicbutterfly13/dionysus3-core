import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.context_stream import ContextStreamService, ContextFlow
from api.models.cognitive import FlowState

@pytest.mark.asyncio
async def test_compression_calculation():
    """Verify compression ratio calculation (tokens_in / tokens_out)."""
    service = ContextStreamService()
    
    # 1000 tokens in, 100 tokens out -> Ratio 10.0 (High compression)
    ratio = service.calculate_compression(tokens_in=1000, tokens_out=100)
    assert ratio == 10.0
    
    # 100 tokens in, 500 tokens out -> Ratio 0.2 (Low compression / verbose)
    ratio = service.calculate_compression(tokens_in=100, tokens_out=500)
    assert ratio == 0.2

@pytest.mark.asyncio
async def test_resonance_calculation():
    """Verify resonance (semantic similarity) calculation using EmbeddingService."""
    service = ContextStreamService()
    
    # Mock EmbeddingService.calculate_similarity
    with patch("api.services.embedding.EmbeddingService.calculate_similarity", new_callable=AsyncMock) as mock_sim:
        mock_sim.return_value = 0.85
        
        resonance = await service.calculate_resonance("My Goal", "My Action Output")
        assert resonance == 0.85

@pytest.mark.asyncio
async def test_flow_state_mapping():
    """Verify that FlowState accurately reflects new metrics."""
    service = ContextStreamService()
    
    # High resonance, low turbulence, High density -> STABLE
    flow = service.map_to_flow_state(density=0.6, turbulence=0.1, compression=5.0, resonance=0.9)
    assert flow.state == FlowState.STABLE
    
    # Low resonance -> DRIFTING
    flow = service.map_to_flow_state(density=0.5, turbulence=0.1, compression=1.0, resonance=0.2)
    assert flow.state == FlowState.DRIFTING


@pytest.mark.asyncio
async def test_analyze_current_flow_uses_memories():
    """Verify flow analysis uses MemEvolve recall output."""
    service = ContextStreamService()
    adapter = AsyncMock()
    adapter.recall_memories.return_value = {
        "memories": [
            {"content": "error detected"},
            {"content": "mismatch observed"},
        ]
    }

    with patch("api.services.context_stream.get_memevolve_adapter", return_value=adapter):
        flow = await service.analyze_current_flow(project_id="proj-1")

    assert flow.density == 0.2
    assert flow.turbulence == 0.4
