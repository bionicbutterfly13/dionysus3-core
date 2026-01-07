"""
Metaplasticity Service - Second-order learning rate adaptation.

Part of 034-network-self-modeling feature.
Implements T068-T070: H-state tracking and stress-reduces-adaptation.
"""

import math
import logging
from typing import Dict, Optional

from api.models.network_state import (
    AdaptationMode,
    TimingState,
    get_network_state_config,
)
from api.services.dynamics_service import DynamicsService

logger = logging.getLogger("dionysus.metaplasticity")


class MetaplasticityController:
    """
    Level-3 controller for adjusting agent learning rates based on OODA surprise.

    Implements second-order learning where the learning rate itself adapts:
    - η = η_base * (1 + sigmoid(surprise_level - threshold))
    - Stress reduces adaptation speed (configurable)
    - H-states track per-node speed factors

    Feature: 034-network-self-modeling (T068-T070)
    """

    def __init__(
        self,
        base_learning_rate: float = 0.1,
        surprise_threshold: float = 0.5,
        stress_reduction_factor: float = 0.5,
        enable_h_state_tracking: bool = True,
    ):
        self.base_learning_rate = base_learning_rate
        self.surprise_threshold = surprise_threshold
        self.stress_reduction_factor = stress_reduction_factor
        self.enable_h_state_tracking = enable_h_state_tracking

        # T068: H-state tracking - speed factors per node
        self._h_states: Dict[str, float] = {}
        self._current_stress: float = 0.0
        self._adaptation_mode: AdaptationMode = AdaptationMode.STABLE
        self._last_prediction_errors: list[float] = []
        
        # FEATURE 048: Precision Registry (Inverse Variance)
        # Default precision is 1.0 (Focused). Range [0.1, 5.0]
        self._precision_registry: Dict[str, float] = {}

    # -------------------------------------------------------------------------
    # FEATURE 048: Precision Modulation
    # -------------------------------------------------------------------------

    def get_precision(self, agent_id: str) -> float:
        """Get current precision for an agent (T048)."""
        return self._precision_registry.get(agent_id, 1.0)

    def set_precision(self, agent_id: str, value: float) -> None:
        """Set precision for an agent. Clamped to [0.1, 5.0]."""
        self._precision_registry[agent_id] = max(0.1, min(5.0, value))
        logger.info(f"Precision for '{agent_id}' set to {self._precision_registry[agent_id]:.2f}")

    def update_precision_from_surprise(self, agent_id: str, surprise_score: float) -> float:
        """
        Dynamically tune precision based on Surprise (Prediction Error).
        High Surprise -> Decrease Precision (Zoom Out / Curiosity)
        Low Surprise -> Increase Precision (Zoom In / Focus)
        """
        current = self.get_precision(agent_id)
        
        # alpha is the modulation sensitivity
        alpha = 0.2
        
        # If surprise is high (>0.5), we decrease precision
        # If surprise is low (<0.5), we increase precision
        delta = (0.5 - surprise_score) * alpha
        new_value = current + delta
        
        self.set_precision(agent_id, new_value)
        return self.get_precision(agent_id)

    # -------------------------------------------------------------------------
    # T068: H-State Tracking
    # -------------------------------------------------------------------------

    def get_h_state(self, node_id: str) -> float:
        """Get speed factor for a specific node (T068)."""
        return self._h_states.get(node_id, self.base_learning_rate)

    def set_h_state(self, node_id: str, speed_factor: float) -> None:
        """Set speed factor for a specific node (T068)."""
        # Clamp to reasonable bounds
        self._h_states[node_id] = max(0.01, min(1.0, speed_factor))

    def get_all_h_states(self) -> Dict[str, float]:
        """Get all tracked H-states (T068)."""
        return self._h_states.copy()

    def create_timing_state(self, agent_id: str, self_model_state_id: str) -> TimingState:
        """Create TimingState snapshot from current H-states (T068)."""
        return TimingState(
            agent_id=agent_id,
            self_model_state_id=self_model_state_id,
            h_states=self._h_states.copy(),
            adaptation_mode=self._adaptation_mode,
            stress_level=self._current_stress,
        )

    # -------------------------------------------------------------------------
    # T069: Second-Order Speed Modulation
    # -------------------------------------------------------------------------

    def calculate_learning_rate(self, prediction_error: float, node_id: Optional[str] = None) -> float:
        """
        Calculate adjusted learning rate based on prediction error (T069).

        Second-order modulation: learning speed adapts based on how well
        the agent is predicting its own state changes.

        Args:
            prediction_error: Current prediction error (0-1 normalized)
            node_id: Optional node for per-node H-state lookup

        Returns:
            Adjusted learning rate
        """
        # Track prediction errors for mode detection
        self._last_prediction_errors.append(prediction_error)
        if len(self._last_prediction_errors) > 10:
            self._last_prediction_errors.pop(0)

        # Get base rate (per-node if tracking enabled)
        if self.enable_h_state_tracking and node_id:
            base_lr = self.get_h_state(node_id)
        else:
            base_lr = self.base_learning_rate

        # Sigmoid centering surprise around the threshold
        diff = prediction_error - self.surprise_threshold
        sigmoid = 1 / (1 + math.exp(-diff * 10))

        # Second-order modulation: scale by (1 + sigmoid)
        adjusted_lr = base_lr * (1 + sigmoid)

        # T070: Apply stress reduction if stressed
        if self._current_stress > 0:
            stress_multiplier = 1 - (self._current_stress * self.stress_reduction_factor)
            adjusted_lr *= max(0.1, stress_multiplier)

        # Update adaptation mode based on error trend
        self._update_adaptation_mode()

        logger.debug(
            f"Metaplasticity: error={prediction_error:.3f}, "
            f"base_lr={base_lr:.3f}, adjusted_lr={adjusted_lr:.3f}, "
            f"stress={self._current_stress:.2f}, mode={self._adaptation_mode.value}"
        )

        return adjusted_lr

    def modulate_speed_from_error(self, node_id: str, prediction_error: float) -> float:
        """
        Modulate a node's H-state based on prediction error (T069).

        High prediction error → increase speed (learn faster from novelty)
        Low prediction error → maintain or decrease speed (stable)

        Args:
            node_id: Node to modulate
            prediction_error: Recent prediction error

        Returns:
            New speed factor for the node
        """
        current_h = self.get_h_state(node_id)

        # High error: speed up learning (novelty detected)
        # Low error: slow down (predictions are accurate)
        if prediction_error > self.surprise_threshold:
            # Increase speed by up to 20%
            delta = 0.2 * (prediction_error - self.surprise_threshold)
            new_h = current_h * (1 + delta)
        else:
            # Decrease speed slightly (stable predictions)
            delta = 0.1 * (self.surprise_threshold - prediction_error)
            new_h = current_h * (1 - delta)

        self.set_h_state(node_id, new_h)
        return self.get_h_state(node_id)

    def run_exposure_update(self, node_id: str, exposure_signal: float, mu_h: float = 0.05):
        """
        Treur Phase 5.3: Adaptation Accelerates with Increased Exposure (Robinson et al. 2016).
        The H-state (speed factor) for a node/model increases as it is 'exposed' more.
        
        Args:
            node_id: Node or Model ID
            exposure_signal: High signal (1.0) means high activation/usage
            mu_h: Speed of adaptation for the speed factor itself (Third-order adaptation)
        """
        current_h = self.get_h_state(node_id)
        
        # SMN State update: H(t+dt) = H(t) + mu_h * [exposure_signal - H(t)] * dt
        new_h = DynamicsService.state_update(current_h, exposure_signal, mu_h)
        
        # Apply stress blocking (T070)
        # In Treur's model, stress (fsb) blocks the UNBLOCKING of learning.
        # Here we reduce the H-state if stress is high.
        if self._current_stress > 0.7:
             # Learning is blocked or frozen
             new_h = current_h * 0.9 # Decay speed factor under stress
             
        self.set_h_state(node_id, new_h)
        logger.debug(f"Exposure-based Timing Update ({node_id}): {current_h:.3f} -> {new_h:.3f}")

    # -------------------------------------------------------------------------
    # T070: Stress-Reduces-Adaptation Principle
    # -------------------------------------------------------------------------

    def set_stress_level(self, stress: float) -> None:
        """
        Set current stress level (T070).

        Stress reduces adaptation speed - a protective mechanism that
        prevents rapid learning during high-uncertainty states.

        Args:
            stress: Stress level from 0.0 (calm) to 1.0 (high stress)
        """
        self._current_stress = max(0.0, min(1.0, stress))

        if self._current_stress > 0.7:
            self._adaptation_mode = AdaptationMode.STRESSED
            logger.warning(f"High stress detected ({stress:.2f}) - reducing adaptation speed")

    def get_stress_level(self) -> float:
        """Get current stress level."""
        return self._current_stress

    def calculate_stress_adjusted_rate(self, base_rate: float) -> float:
        """
        Apply stress reduction to a learning rate (T070).

        Implements the principle: stress reduces adaptation.

        Args:
            base_rate: Base learning rate before stress adjustment

        Returns:
            Stress-adjusted learning rate
        """
        if self._current_stress <= 0:
            return base_rate

        # Reduce rate proportionally to stress
        reduction = self._current_stress * self.stress_reduction_factor
        return base_rate * (1 - reduction)

    # -------------------------------------------------------------------------
    # Adaptation Mode Management
    # -------------------------------------------------------------------------

    def _update_adaptation_mode(self) -> None:
        """Update adaptation mode based on recent prediction errors."""
        if len(self._last_prediction_errors) < 3:
            return

        recent = self._last_prediction_errors[-3:]
        avg_error = sum(recent) / len(recent)

        # Check trend
        if len(self._last_prediction_errors) >= 5:
            older = self._last_prediction_errors[-5:-3]
            old_avg = sum(older) / len(older)

            if avg_error > old_avg + 0.05:
                self._adaptation_mode = AdaptationMode.ACCELERATING
            elif avg_error < old_avg - 0.05:
                self._adaptation_mode = AdaptationMode.DECELERATING
            else:
                if self._current_stress < 0.7:
                    self._adaptation_mode = AdaptationMode.STABLE

    def get_adaptation_mode(self) -> AdaptationMode:
        """Get current adaptation mode."""
        return self._adaptation_mode

    def calculate_max_steps(self, prediction_error: float, base_steps: int = 5) -> int:
        """
        Adjust agent max_steps based on surprise.
        High surprise allows for more exploratory steps.
        """
        if prediction_error > self.surprise_threshold:
            return base_steps + 2
        return base_steps


_metaplasticity_controller: Optional[MetaplasticityController] = None


def get_metaplasticity_controller() -> MetaplasticityController:
    """Get or create the metaplasticity controller singleton."""
    global _metaplasticity_controller
    if _metaplasticity_controller is None:
        config = get_network_state_config()
        _metaplasticity_controller = MetaplasticityController(
            enable_h_state_tracking=config.network_state_enabled
        )
    return _metaplasticity_controller
