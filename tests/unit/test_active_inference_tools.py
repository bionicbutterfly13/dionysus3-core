import pytest
import numpy as np
from api.agents.tools.active_inference_tools import compute_policy_efe, update_belief_precision

def test_compute_policy_efe_tool():
    # Test valid computation
    result = compute_policy_efe.forward(
        policy_id="test_plan_001",
        action_indices=[0, 1],
        num_states=2
    )
    
    assert result["status"] == "computed"
    assert "efe" in result
    assert isinstance(result["efe"], float)
    assert result["policy_id"] == "test_plan_001"
    assert result["recommendation"] in ["LOW_G", "HIGH_G"]

def test_update_belief_precision_tool():
    # Test precision modulation
    # Note: This might require mocks if the service state is truly isolated/shared
    result = update_belief_precision.forward(
        agent_name="reasoning",
        precision_delta=0.1
    )
    
    assert result["status"] == "modulated"
    assert result["agent_name"] == "reasoning"
    assert "old_precision" in result
    assert "new_precision" in result
    assert result["new_precision"] != result["old_precision"]
