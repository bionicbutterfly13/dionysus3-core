import pytest
import asyncio
from api.services.unified_reality_model import UnifiedRealityModelService
from api.utils.event_bus import get_event_bus
from api.models.meta_tot import ActiveInferenceState

@pytest.mark.asyncio
async def test_urm_event_bus_integration():
    """Verify that URM auto-updates when cognitive events are emitted."""
    # 1. Setup service
    service = UnifiedRealityModelService()
    bus = get_event_bus()
    
    # 2. Emit event
    test_state = ActiveInferenceState(
        surprise=0.42,
        prediction_error=0.1,
        precision=0.8
    )
    
    await bus.emit_cognitive_event(
        source="test_unit",
        problem="Verifying EventBus integration",
        reasoning="Simple emission test",
        state=test_state
    )
    
    # 3. Verify URM updated
    model = service.get_model()
    assert len(model.active_inference_states) > 0
    
    # The state should match what we emitted
    # Note: Depending on how update_active_inference_states works (it replaces or appends)
    # The current implementation replaces: self._model.active_inference_states = states
    last_state = model.active_inference_states[-1]
    assert last_state.surprise == 0.42
    assert last_state.precision == 0.8
