"""
Unit tests for Dynamic Precision Modulation (Feature 048).
"""
import pytest
from api.services.metaplasticity_service import MetaplasticityController

def test_precision_clamping():
    controller = MetaplasticityController()
    
    # Test high clamp
    controller.set_precision("test_agent", 10.0)
    assert controller.get_precision("test_agent") == 5.0
    
    # Test low clamp
    controller.set_precision("test_agent", 0.01)
    assert controller.get_precision("test_agent") == 0.1

def test_surprise_inverse_modulation():
    controller = MetaplasticityController()
    agent_id = "reasoning"
    
    # Initial precision is 1.0
    initial = controller.get_precision(agent_id)
    
    # 1. High Surprise (0.9) -> Should decrease precision (Zoom Out)
    new_prec = controller.update_precision_from_surprise(agent_id, 0.9)
    assert new_prec < initial
    
    # 2. Low Surprise (0.1) -> Should increase precision (Zoom In)
    current = controller.get_precision(agent_id)
    final_prec = controller.update_precision_from_surprise(agent_id, 0.1)
    assert final_prec > current

def test_set_mental_focus_tool():
    from api.agents.tools.cognitive_tools import set_mental_focus
    
    result = set_mental_focus.forward(
        agent_id="perception",
        precision_level=0.2,
        rationale="Need exploratory scan"
    )
    
    assert result["new_precision"] == 0.2
    assert "EPISTEMIC" in result["mode"]
