"""
Self-Modeling Callback for smolagents integration.

Part of 034-network-self-modeling feature.
Implements T033-T034: Prediction/resolution cycle during agent execution.
"""

from __future__ import annotations

import logging
from typing import Optional

from smolagents.memory import ActionStep
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

    def log_step(self, step: ActionStep, step_number: int) -> None:
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

    async def _on_step_end(self, step: ActionStep, step_number: int) -> None:
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

                # ACTIVE METACOGNITION: Trigger correction when error exceeds threshold
                # Per Metacognitive Particles paper: mental actions modulate precision
                if resolved.prediction_error > 0.15:
                    logger.warning(
                        f"High prediction error ({resolved.prediction_error:.2%}) - "
                        f"triggering active metacognitive correction"
                    )
                    # Trigger active correction via metacognition agent
                    await self._trigger_active_correction(
                        prediction_error=resolved.prediction_error,
                        step_number=step_number,
                        step=step
                    )

        except Exception as e:
            logger.warning(f"Error in _on_step_end: {e}")

        finally:
            self._pending_prediction_id = None
            self._pre_step_state = None

    async def _trigger_active_correction(
        self,
        prediction_error: float,
        step_number: int,
        step: ActionStep
    ) -> None:
        """
        Trigger active metacognitive correction when prediction error is high.

        This is the bridge between passive observation (self-modeling) and
        active metacognition (mental actions). When prediction error exceeds
        threshold, we engage the metacognition agent to modulate precision.

        Per Metacognitive Particles paper:
        - High prediction error -> decrease precision (be more open to surprise)
        - Mental actions modulate parameters, not content

        Args:
            prediction_error: The magnitude of prediction error
            step_number: Current step number
            step: The ActionStep that produced the error
        """
        try:
            # Import here to avoid circular imports
            from api.agents.metacognition_agent import MetacognitionAgent

            # Build error context for potentially more targeted correction
            error_context = {
                "step_number": step_number,
                "prediction_error": prediction_error,
            }

            # Extract any useful context from the step
            if step and hasattr(step, 'tool_calls') and step.tool_calls:
                # If we can identify what tools were used, include that context
                tool_names = [tc.name for tc in step.tool_calls if hasattr(tc, 'name')]
                if tool_names:
                    error_context["tools_used"] = tool_names

            # Use a temporary metacognition agent for the correction
            # Note: In production, this should use a singleton or pool
            metacog = MetacognitionAgent()

            # Execute active correction
            correction_result = await metacog.active_correction(
                agent_name=self.agent_id,
                prediction_error=prediction_error,
                error_context=error_context
            )

            if correction_result.get("correction_type") != "none":
                logger.info(
                    f"Active correction applied for '{self.agent_id}': "
                    f"type={correction_result['correction_type']}, "
                    f"actions={len(correction_result.get('actions_taken', []))}"
                )

        except Exception as e:
            # Active correction should not crash the callback
            logger.warning(f"Active correction failed for '{self.agent_id}': {e}")


def create_self_modeling_callback(agent_id: str) -> Optional[SelfModelingCallback]:
    """
    Factory function to create self-modeling callback if enabled.

    Returns None if SELF_MODELING_ENABLED is false.
    """
    config = get_network_state_config()
    if not config.self_modeling_enabled:
        return None

    return SelfModelingCallback(agent_id=agent_id, enabled=True)
