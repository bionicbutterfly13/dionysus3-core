import pytest
import numpy as np
from api.services.efe_engine import EFEEngine

@pytest.fixture
def efe_engine():
    return EFEEngine()

def test_efe_calculation_logic(efe_engine):
    """Verify EFE ranking favors low uncertainty and low goal divergence."""
    goal_vector = [1.0, 0.0]
    
    thoughtseeds = [
        {
            "id": "pragmatic_perfect",
            "response_vector": [1.0, 0.0], # Matches goal
            "prediction_probabilities": [0.9, 0.1] # Low uncertainty
        },
        {
            "id": "uncertain_but_on_goal",
            "response_vector": [1.0, 0.0], # Matches goal
            "prediction_probabilities": [0.5, 0.5] # High uncertainty
        },
        {
            "id": "divergent",
            "response_vector": [0.0, 1.0], # Completely different direction
            "prediction_probabilities": [0.9, 0.1] # Low uncertainty
        }
    ]
    
    response = efe_engine.calculate_efe("test query", goal_vector, thoughtseeds)
    
    # Detailed checks
    scores = response.scores
    assert scores["pragmatic_perfect"].efe_score < scores["uncertain_but_on_goal"].efe_score
    assert scores["pragmatic_perfect"].efe_score < scores["divergent"].efe_score
    
    # Dominant should be the perfect one
    assert response.dominant_seed_id == "pragmatic_perfect"

def test_efe_null_vectors(efe_engine):
    """Verify EFE handles null vectors gracefully."""
    goal_vector = [0.0, 0.0]
    thoughtseeds = [{"id": "s1", "response_vector": [1.0, 0.0], "prediction_probabilities": [0.5, 0.5]}]
    
    response = efe_engine.calculate_efe("q", goal_vector, thoughtseeds)
    assert response.scores["s1"].goal_divergence == 1.0
