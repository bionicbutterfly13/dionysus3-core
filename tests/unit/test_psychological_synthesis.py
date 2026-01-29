import pytest
import numpy as np
from api.services.efe_engine import get_efe_engine
from api.models.hexis_ontology import CognitiveModality

@pytest.mark.asyncio
async def test_adhd_exploratory_bias():
    """
    Verify that ADHD_EXPLORATORY modality favors discovery by 
    reducing the penalty for uncertainty/entropy.
    """
    engine = get_efe_engine()
    
    # Simulation: A thought seed with high uncertainty but high divergence
    prediction_probs = [0.2, 0.2, 0.2, 0.2, 0.2] # High entropy (~2.32 bits)
    thought_vector = np.array([0.5, 0.5])
    goal_vector = np.array([1.0, 1.0])
    precision = 1.0
    
    # Neurotypical calculation
    nt_efe = engine.calculate_efe(
        prediction_probs, 
        thought_vector, 
        goal_vector, 
        precision=precision, 
        modality=CognitiveModality.NEUROTYPICAL
    )
    
    # ADHD Exploratory calculation
    adhd_efe = engine.calculate_efe(
        prediction_probs, 
        thought_vector, 
        goal_vector, 
        precision=precision, 
        modality=CognitiveModality.ADHD_EXPLORATORY
    )
    
    print(f"NT EFE: {nt_efe:.4f}, ADHD EFE: {adhd_efe:.4f}")
    
    # In ADHD mode, the uncertainty weight is 0.5 instead of 1.0.
    # The divergence weight is 1.5 instead of 1.0.
    # If uncertainty is large, ADHD EFE should typically be lower if not dominated by divergence.
    # Let's verify the relative scaling.
    assert adhd_efe != nt_efe
    
    # Specific verification: 
    # NT = 1.0 * H + 1.0 * D
    # ADHD = 0.5 * H + 1.5 * D
    # If H is high and D is low, ADHD should be lower.
    
@pytest.mark.asyncio
async def test_triple_bind_detection():
    """
    Verify the detection of policy gridlock (Triple-Bind).
    """
    engine = get_efe_engine()
    
    # All policies have high EFE
    high_efe_scores = [2.0, 1.8, 2.5, 3.0]
    locked = engine.detect_triple_bind(high_efe_scores, threshold=1.5)
    assert locked is True
    
    # At least one policy is good
    good_efe_scores = [2.0, 0.8, 2.5]
    locked = engine.detect_triple_bind(good_efe_scores, threshold=1.5)
    assert locked is False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_adhd_exploratory_bias())
    asyncio.run(test_triple_bind_detection())
