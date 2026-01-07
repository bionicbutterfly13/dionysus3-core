import pytest
import asyncio
from uuid import uuid4
from api.services.dynamics_service import DynamicsService
from api.services.efe_engine import EFEEngine
from api.services.metaplasticity_service import get_metaplasticity_controller
from api.models.mental_model import BasinRelationship, RelationshipType

def test_dynamics_primitives():
    """Verify alogistic and hebbian math."""
    # Test Alogistic #2
    # sigm=5, tau=0.5, impact=0.8 -> should be high activation
    act = DynamicsService.alogistic(5.0, 0.5, [0.8], [1.0])
    assert act > 0.5
    
    # sigm=5, tau=0.5, impact=0.2 -> should be low activation
    act_low = DynamicsService.alogistic(5.0, 0.5, [0.2], [1.0])
    assert act_low < 0.5
    assert act_low < act

    # Test Hebbian #3
    # mu=0.1, x=1, y=1, w=0.5 -> new w should be > 0.5
    new_w = DynamicsService.hebbian(0.1, 1.0, 1.0, 0.5)
    assert new_w > 0.5
    
    # Test persistence (x=0) -> should stay same or decay slightly depending on formula
    new_w_low = DynamicsService.hebbian(0.1, 0.0, 1.0, 0.5)
    assert new_w_low == 0.5 # mu*0*1 + (1-0)*0.5 = 0.5

def test_efe_alogistic_selection():
    """Verify EFEEngine uses alogistic aggregation."""
    engine = EFEEngine()
    candidates = [
        {"id": "A", "efe_score": 0.1}, # Very good
        {"id": "B", "efe_score": 0.5}, # Medium
        {"id": "C", "efe_score": 0.9}, # Poor
    ]
    
    selected = engine.select_top_candidates_alogistic(candidates)
    assert len(selected) == 3
    assert selected[0]["id"] == "A"
    assert selected[0]["activation"] > 0.5
    assert selected[2]["activation"] < 0.5

def test_metaplasticity_exposure():
    """Verify H-state updates based on exposure."""
    ctrl = get_metaplasticity_controller()
    node_id = "test_node"
    ctrl.set_h_state(node_id, 0.1)
    
    # Run exposure update (high exposure)
    ctrl.run_exposure_update(node_id, 1.0, mu_h=0.1)
    new_h = ctrl.get_h_state(node_id)
    assert new_h > 0.1
    
    # Test stress blocking
    ctrl.set_stress_level(0.9)
    ctrl.run_exposure_update(node_id, 1.0, mu_h=0.1)
    h_stressed = ctrl.get_h_state(node_id)
    assert h_stressed < new_h # Decay due to stress blocking
