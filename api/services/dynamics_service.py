import numpy as np
from pydantic import BaseModel, Field
from typing import List, Optional

class DynamicsService:
    """
    Implements the mathematical primitives for Jan Treur's Self-Modeling Networks (SMN).
    Reference: Treur (2022) - Mental Models and Their Dynamics, Adaptation, and Control.
    """

    @staticmethod
    def alogistic(sigm: float, tau: float, input_values: List[float], weights: List[float]) -> float:
        """
        Alogistic combination function (Library #2).
        Calculates the aggregated impact using a logistic function with steepness 'sigm' and threshold 'tau'.
        """
        if not input_values:
            return 0.0
        
        # Calculate dot product
        impact = sum(v * w for v, w in zip(input_values, weights))
        
        # Logistic formula: [ (1/(1+exp(-sigm*(impact-tau)))) - (1/(1+exp(sigm*tau))) ] / [ (1/(1- (1/(1+exp(sigm*tau)))) ) ]
        # Simplified standard logistic used in SMN
        exp_term = np.exp(-sigm * (impact - tau))
        base_logistic = 1.0 / (1.0 + exp_term)
        
        # Shift and scale to ensure f(0) = 0 and max is 1 (Standard SMN scaling)
        shift = 1.0 / (1.0 + np.exp(sigm * tau))
        scale = 1.0 / (1.0 - shift)
        
        return (base_logistic - shift) * scale

    @staticmethod
    def hebbian(mu: float, x: float, y: float, w: float) -> float:
        """
        Hebbian learning combination function (Library #3).
        Calculates the new weight based on the persistence 'mu' and the co-occurrence of states X and Y.
        """
        # Formula: mu * x * y + (1 - mu * x) * w
        # Standard treur hebbian: w + mu * (x * y * (1 - w) - (1 - x) * y * w)
        # Let's use the one from the book excerpt (simplified)
        return mu * x * y + (1.0 - mu * x) * w

    @staticmethod
    def state_update(current_val: float, impact: float, speed_factor: float, delta_t: float = 1.0) -> float:
        """
        General state update equation: Y(t+dt) = Y(t) + eta * [impact - Y(t)] * dt
        """
        return current_val + speed_factor * (impact - current_val) * delta_t
