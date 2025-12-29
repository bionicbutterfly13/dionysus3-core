"""
Self-Modeling Callback for smolagents integration.

Part of 034-network-self-modeling feature.
Implements T033-T034: Prediction/resolution cycle during agent execution.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from smolagents.agents import AgentStep
from smolagents.monitoring import AgentLogger

from api.models.network_state import get_network_state_config
from api.services.self_modeling_service import get_self_modeling_service
from api.services.network_state_service import get_network_state_service

logger = logging.getLogger("dionysus.self_modeling_callback")


class SelfModelingCallback(AgentLogger):
    """
    Callback that implements self-prediction during agent execution (T033).

    Before each step:
    - Captures current network state (W/T/H values)
    - Makes prediction for post-step state

    After each step:
    - Captures actual post-step state
    - Resolves prediction with L2 error calculation
    - Logs prediction accuracy for regularization feedback

    This enables agents to learn their own dynamics, providing
    a regularization signal that reduces model complexity.
    """

    def __init__(self, agent_id: str, enabled: bool = True):
        """
        Initialize callback.

        Args:
            agent_id: The agent this callback is attached to
            enabled: Whether self-modeling is active (respects feature flag)
        """
        super().__init__()
        self.agent_id = agent_id
        self.enabled = enabled and get_network_state_config().self_modeling_enabled

        self._pending_prediction_id: Optional[str] = None
        self._pre_step_state: Optional[dict[str, float]] = None

        if self.enabled:
            logger.info(f"SelfModelingCallback enabled for agent {agent_id}")
        else:
            logger.debug(f"SelfModelingCallback disabled for agent {agent_id}")

    async def _get_current_state(self) -> dict[str, float]:
        """Get current W/T/H state from network state service."""
        service = get_network_state_service()
        state = await service.get_current(self.agent_id)

        if not state:
            return {}

        # Flatten W/T/H into single state dict
        result = {}
        for key, val in state.connection_weights.items():
            result[f"w_{key}"] = val
        for key, val in state.thresholds.items():
            result[f"t_{key}"] = val
        for key, val in state.speed_factors.items():
            result[f"h_{key}"] = val

        return result

    def log_step(self, step: AgentStep, step_number: int) -> None:
        """Called after each agent step. Synchronous wrapper for async resolution."""
        if not self.enabled:
            return

        # Note: smolagents callbacks are sync, so we use fire-and-forget async
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule but don't block
                asyncio.create_task(self._on_step_end(step, step_number))
            else:
                loop.run_until_complete(self._on_step_end(step, step_number))
        except RuntimeError:
            # No event loop - skip self-modeling for this step
            logger.debug("No event loop available for self-modeling callback")

    async def on_step_start(self, step_number: int) -> None:
        """
        Called before agent step execution (T034).

        Captures pre-step state and creates prediction.
        """
        if not self.enabled:
            return

        try:
            # Get current state
            self._pre_step_state = await self._get_current_state()

            if not self._pre_step_state:
                logger.debug(f"No network state available for agent {self.agent_id}")
                return

            # Create prediction for next state
            # For now, we predict state will remain similar (baseline predictor)
            # More sophisticated predictors can be added later
            service = get_self_modeling_service()
            prediction = await service.predict_next_state(
                self.agent_id,
                self._pre_step_state  # Predict no change as baseline
            )

            self._pending_prediction_id = prediction.id
            logger.debug(f"Created prediction {prediction.id} for step {step_number}")

        except Exception as e:
            logger.warning(f"Error in on_step_start: {e}")
            self._pending_prediction_id = None

    async def _on_step_end(self, step: AgentStep, step_number: int) -> None:
        """
        Called after agent step execution (T034).

        Captures post-step state and resolves prediction.
        """
        if not self.enabled or not self._pending_prediction_id:
            return

        try:
            # Get post-step state
            actual_state = await self._get_current_state()

            if not actual_state:
                logger.debug("No post-step state available for resolution")
                return

            # Resolve prediction
            service = get_self_modeling_service()
            resolved = await service.resolve_prediction(
                self._pending_prediction_id,
                actual_state
            )

            if resolved and resolved.prediction_error is not None:
                logger.info(
                    f"Step {step_number} prediction error: {resolved.prediction_error:.4f}"
                )

                # If error is high, log for potential regularization action
                if resolved.prediction_error > 0.15:
                    logger.warning(
                        f"High prediction error ({resolved.prediction_error:.2%}) - "
                        f"agent may benefit from regularization"
                    )

        except Exception as e:
            logger.warning(f"Error in _on_step_end: {e}")

        finally:
            self._pending_prediction_id = None
            self._pre_step_state = None


def create_self_modeling_callback(agent_id: str) -> Optional[SelfModelingCallback]:
    """
    Factory function to create self-modeling callback if enabled.

    Returns None if SELF_MODELING_ENABLED is false.
    """
    config = get_network_state_config()
    if not config.self_modeling_enabled:
        return None

    return SelfModelingCallback(agent_id=agent_id, enabled=True)
