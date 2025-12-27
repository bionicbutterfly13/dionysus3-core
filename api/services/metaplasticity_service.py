import math
import logging
from typing import Dict, Any

logger = logging.getLogger("dionysus.metaplasticity")

class MetaplasticityController:
    """
    Level-3 controller for adjusting agent learning rates based on OODA surprise.
    η = η_base * (1 + sigmoid(surprise_level - threshold))
    """

    def __init__(self, base_learning_rate: float = 0.1, surprise_threshold: float = 0.5):
        self.base_learning_rate = base_learning_rate
        self.surprise_threshold = surprise_threshold

    def calculate_learning_rate(self, prediction_error: float) -> float:
        """
        Calculate adjusted learning rate based on current surprise (prediction error).
        """
        # Sigmoid centering surprise around the threshold
        # Scaling factor: range [1.0, 2.0]
        # η = η_base * (1 + 1 / (1 + exp(-(surprise - threshold) * 10)))
        
        diff = prediction_error - self.surprise_threshold
        sigmoid = 1 / (1 + math.exp(-diff * 10))
        
        adjusted_lr = self.base_learning_rate * (1 + sigmoid)
        
        logger.info(f"metaplasticity_adjustment", extra={
            "prediction_error": prediction_error,
            "surprise_threshold": self.surprise_threshold,
            "base_lr": self.base_learning_rate,
            "adjusted_lr": adjusted_lr
        })
        
        return adjusted_lr

    def calculate_max_steps(self, prediction_error: float, base_steps: int = 5) -> int:
        """
        Adjust agent max_steps based on surprise.
        High surprise allows for more exploratory steps.
        """
        if prediction_error > self.surprise_threshold:
            return base_steps + 2
        return base_steps

_metaplasticity_controller: Any = None

def get_metaplasticity_controller() -> MetaplasticityController:
    global _metaplasticity_controller
    if _metaplasticity_controller is None:
        _metaplasticity_controller = MetaplasticityController()
    return _metaplasticity_controller
