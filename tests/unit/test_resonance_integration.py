import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from api.models.beautiful_loop import (
    UnifiedRealityModel,
    BoundInference,
    ResonanceMode,
    ResonanceSignal
)
from api.services.resonance_detector import ResonanceDetector
from api.agents.consciousness_manager import ConsciousnessManager

@pytest.fixture
def mock_urm():
    urm = UnifiedRealityModel(
        coherence_score=0.9,
        bound_inferences=[]
    )
    return urm

@pytest.fixture
def resonance_detector():
    return ResonanceDetector()

def test_resonance_detection_luminous(resonance_detector, mock_urm):
    # Setup luminous state: High coherence, low surprisal (high uncertainty reduction)
    mock_urm.bound_inferences = [
        BoundInference(
            inference_id="inf1",
            source_layer="reasoning",
            uncertainty_reduction=0.9,
            precision_score=0.9,
            coherence_score=0.9
        )
    ]
    mock_urm.coherence_score = 0.95
    
    signal = resonance_detector.detect(mock_urm)
    assert signal.mode == ResonanceMode.LUMINOUS
    assert signal.resonance_score > 0.8
    assert signal.surprisal < 0.2

def test_resonance_detection_dissonant(resonance_detector, mock_urm):
    # Setup dissonant state: High surprisal (low uncertainty reduction)
    mock_urm.bound_inferences = [
        BoundInference(
            inference_id="inf2",
            source_layer="reasoning",
            uncertainty_reduction=0.1, # Surprisal = 0.9
            precision_score=0.9,
            coherence_score=0.4
        )
    ]
    mock_urm.coherence_score = 0.5
    
    signal = resonance_detector.detect(mock_urm)
    assert signal.mode == ResonanceMode.DISSONANT
    assert signal.discovery_urgency >= 0.9

@pytest.mark.asyncio
async def test_consciousness_manager_emits_particle_on_dissonance():
    # Setup manager and mocks
    manager = ConsciousnessManager(model_id="test-model")
    
    # Mock services
    mock_urm_service = MagicMock()
    mock_urm = UnifiedRealityModel(coherence_score=0.5, bound_inferences=[])
    mock_urm_service.get_model.return_value = mock_urm
    
    # Mock ResonanceDetector to return DISSONANT
    mock_signal = ResonanceSignal(
        mode=ResonanceMode.DISSONANT,
        resonance_score=0.1,
        surprisal=0.9,
        discovery_urgency=0.95
    )
    
    initial_context = {"task": "test", "cycle_id": "test_cycle"}
    
    # Patch all the things
    with patch("api.agents.consciousness_manager.get_unified_reality_model", return_value=mock_urm_service), \
         patch("api.agents.consciousness_manager.get_resonance_detector") as mock_get_detector, \
         patch("api.agents.resource_gate.run_agent_with_timeout", AsyncMock(return_value=json.dumps({"reasoning": "test", "confidence": 0.5}))), \
         patch("api.agents.consciousness_manager.get_hyper_model_service", MagicMock()):
        
        mock_detector = MagicMock()
        mock_detector.detect.return_value = mock_signal
        mock_get_detector.return_value = mock_detector
        
        # Run OODA cycle (orchestrator is mocked)
        await manager.run_ooda_cycle(initial_context)
        
        # Verify resonance detector was called
        mock_detector.detect.assert_called_once()
        
        # Verify particle emission
        mock_urm_service.add_metacognitive_particle.assert_called_once()
        particle = mock_urm_service.add_metacognitive_particle.call_args[0][0]
        assert particle.urgency == 0.95
        assert "DISSONANT" in particle.content
