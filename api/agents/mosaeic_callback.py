import asyncio
import logging
from typing import Any, Dict
from smolagents.memory import ActionStep
from api.services.mosaeic_service import get_mosaeic_service

logger = logging.getLogger(__name__)

def create_mosaeic_callback(agent_id: str):
    """
    Creates a callback that performs a MOSAEIC capture on every agent step.
    """
    async def run_capture(text: str, source_id: str):
        try:
            service = get_mosaeic_service()
            capture = await service.extract_capture(text, source_id)
            await service.persist_capture(capture)
            logger.info(f"MOSAEIC capture successful for {agent_id}")
        except Exception as e:
            logger.error(f"MOSAEIC capture failed for {agent_id}: {e}")

    def mosaeic_callback(step: Any, **kwargs):
        if not isinstance(step, ActionStep):
            return

        # Extract relevant text from the step
        # Observations usually contain the most "experiential" data
        observation = getattr(step, "observation", "")
        if not observation:
            return

        source_id = f"callback:{agent_id}:step_{getattr(step, 'step_number', 0)}"
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(run_capture(str(observation), source_id), loop)
            else:
                asyncio.run(run_capture(str(observation), source_id))
        except Exception as e:
            logger.warning(f"Could not trigger MOSAEIC capture: {e}")

    return mosaeic_callback
