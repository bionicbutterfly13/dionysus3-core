import pytest
from api.services.metaplasticity_service import MetaplasticityController

@pytest.fixture
def controller():
    return MetaplasticityController(base_learning_rate=0.1, surprise_threshold=0.5)

def test_learning_rate_scaling(controller):
    """Verify learning rate increases with surprise."""
    low_surprise = 0.1
    high_surprise = 0.9
    
    lr_low = controller.calculate_learning_rate(low_surprise)
    lr_high = controller.calculate_learning_rate(high_surprise)
    
    assert lr_high > lr_low
    assert lr_low >= 0.1
    assert lr_high <= 0.2

def test_max_steps_adjustment(controller):
    """Verify max_steps increases when surprise is above threshold."""
    low_surprise = 0.1
    high_surprise = 0.9
    
    steps_low = controller.calculate_max_steps(low_surprise, base_steps=5)
    steps_high = controller.calculate_max_steps(high_surprise, base_steps=5)
    
    assert steps_high > steps_low
    assert steps_high == 7
    assert steps_low == 5
