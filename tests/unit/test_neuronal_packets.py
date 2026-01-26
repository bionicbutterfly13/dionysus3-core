import pytest
from api.services.nemori_river_flow import NemoriRiverFlow
from api.models.autobiographical import DevelopmentEvent, PacketDynamics

@pytest.fixture
def river_flow():
    return NemoriRiverFlow()

@pytest.mark.asyncio
async def test_calculate_packet_dynamics(river_flow):
    """Verify packet dynamics are calculated correctly from text."""
    text = "This is a test of the neuronal packet dynamics calculation."
    dynamics = river_flow._calculate_packet_dynamics(text)
    
    assert isinstance(dynamics, PacketDynamics)
    # Check ranges (50-500ms)
    assert 50 <= dynamics.duration_ms <= 500
    assert dynamics.spike_density > 0
    assert 0 <= dynamics.phase_ratio <= 1.0

@pytest.mark.asyncio
async def test_create_packet_train(river_flow):
    """Verify that a large input is correctly quantized into packets."""
    # Create a long string (> 50 words to trigger multiple packets)
    long_text = "word " * 120
    packets = await river_flow.create_packet_train(long_text)
    
    assert len(packets) >= 3 # 120 / 50 = 2.4 -> 3 packets
    for i, pkt in enumerate(packets):
        assert isinstance(pkt, DevelopmentEvent)
        assert pkt.packet_dynamics is not None
        assert pkt.metadata["sequence_index"] == i
        if i > 0:
            assert pkt.metadata["parent_packet_id"] == packets[i-1].event_id

@pytest.mark.asyncio
async def test_packet_chaining(river_flow):
    """Verify packets are linked correctly."""
    text = "Short text for one packet."
    packets = await river_flow.create_packet_train(text)
    assert len(packets) == 1
    assert packets[0].metadata["parent_packet_id"] is None

@pytest.mark.asyncio
async def test_active_inference_metrics():
    """Verify entropy and surprisal calculations."""
    from api.services.active_inference_service import get_active_inference_service
    from api.models.belief_state import BeliefState
    import numpy as np
    
    svc = get_active_inference_service()
    
    # 1. Uncertainty (Entropy)
    # Uniform distribution over 2 states: H = ln(2) approx 0.693
    belief = BeliefState(mean=[0.5, 0.5], precision=[[1.0, 0.0], [0.0, 1.0]])
    uncertainty = svc.calculate_uncertainty(belief)
    assert 0.69 <= uncertainty <= 0.70
    
    # 2. Surprisal
    # Perfect prediction: obs matches state exactly, likelihood = 1.0 -> surprisal = 0
    # Create simple model
    model = svc.create_simple_model(num_states=2, num_observations=2, num_actions=1)
    model.A = [np.eye(2)] # Perfect mapping
    
    # Observation [1, 0] (State 0)
    obs = np.array([1, 0])
    # Belief strongly State 0
    belief_strong = BeliefState(mean=[0.99, 0.01], precision=[[1.0, 0.0], [0.0, 1.0]])
    surprisal_low = svc.calculate_surprisal(obs, belief_strong, model)
    assert surprisal_low < 0.5
    
    # Belief strongly State 1 (Surprise!)
    belief_wrong = BeliefState(mean=[0.01, 0.99], precision=[[1.0, 0.0], [0.0, 1.0]])
    surprisal_high = svc.calculate_surprisal(obs, belief_wrong, model)
    assert surprisal_high > 4.0
