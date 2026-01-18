import pytest
import numpy as np
from pymdp import utils
from pymdp.agent import Agent

def test_pymdp_installation():
    """Verify pymdp is installed and importable."""
    assert utils is not None
    assert Agent is not None

def test_generative_model_basics():
    """Verify we can define a basic generative model using pymdp structures."""
    # Define a simple 2-state, 2-observation model
    # A matrix: Observation likelihood P(o|s)
    # 2 observations, 2 states
    A = utils.to_numpy([
        [0.9, 0.1],  # State 0 tends to produce Obs 0
        [0.1, 0.9]   # State 1 tends to produce Obs 1
    ])
    
    # B matrix: Transition dynamics P(s'|s,u)
    # 2 states, 2 states, 1 action (passive)
    B = np.eye(2).reshape(2, 2, 1)
    
    # C matrix: Preferences P(o)
    C = utils.to_numpy([1.0, 0.0]) # Prefer Obs 0
    
    # D matrix: Priors P(s)
    D = utils.to_numpy([0.5, 0.5])
    
    agent = Agent(A=A, B=B, C=C, D=D)
    
    assert agent.qs is not None
    assert agent.qs.shape == (2,)

def test_inference_step():
    """Verify a single step of active inference."""
    # Hidden State: 0 = Safe, 1 = Danger
    # Observation: 0 = Calm, 1 = Fear
    
    # A: Safe -> Calm (0.9), Danger -> Fear (0.9)
    A = np.zeros((2, 2))
    A[0, 0] = 0.9
    A[1, 0] = 0.1
    A[0, 1] = 0.1
    A[1, 1] = 0.9
    
    # Agent setup
    agent = Agent(A=A, D=np.array([0.5, 0.5]))
    
    # Test 1: Observation = Calm (0)
    # Should infer State = Safe (0)
    observation = [0] 
    qs = agent.infer_states(observation)
    
    # Expect high probability for state 0
    assert qs[0] > qs[1]
    assert qs[0] > 0.8  # Should be fairly confident
    
    # Test 2: Observation = Fear (1)
    # Should infer State = Danger (1)
    observation = [1]
    qs = agent.infer_states(observation)
    
    assert qs[1] > qs[0]
    assert qs[1] > 0.8
