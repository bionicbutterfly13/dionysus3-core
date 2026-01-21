"""
System Event Bus (Feature 050)
Centralized bus for cognitive and system events.

Ensures that events from any source (OODA, background workers, API) 
can trigger the Consciousness Integration Pipeline.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from api.services.consciousness_integration_pipeline import get_consciousness_pipeline
from api.models.meta_tot import ActiveInferenceState

logger = logging.getLogger("dionysus.event_bus")

class EventBus:
    def __init__(self):
        self.pipeline = get_consciousness_pipeline()

    async def emit_cognitive_event(
        self,
        source: str,
        problem: str,
        reasoning: str,
        state: Optional[ActiveInferenceState] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Emit a cognitive event to be processed by the integration pipeline.
        """
        logger.info(f"EventBus: Emitting cognitive event from {source}")
        
        # Ensure we have a state
        if state is None:
            state = ActiveInferenceState(
                surprise=0.1,
                prediction_error=0.05,
                precision=0.9
            )
            
        try:
            await self.pipeline.process_cognitive_event(
                problem=problem,
                reasoning_trace=reasoning,
                active_inference_state=state,
                context=context
            )
        except Exception as e:
            logger.error(f"EventBus: Pipeline processing failed for {source}: {e}")

    async def emit_system_event(self, source: str, event_type: str, summary: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Record non-cognitive system events (maintenance, health checks, etc.)
        in the autobiographical memory.
        """
        from api.services.autobiographical_service import get_autobiographical_service
        from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
        
        logger.info(f"EventBus: Emitting system event [{event_type}] from {source}")
        
        auto_svc = get_autobiographical_service()
        
        import uuid
        event = DevelopmentEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=DevelopmentEventType.TASK_COMPLETED,
            summary=f"System [{source}]: {summary}",
            rationale=f"Background event triggered by {source}.",
            impact="System maintenance and continuity.",
            lessons_learned=[],
            metadata=metadata or {}
        )
        
        try:
            await auto_svc.record_event(event)
        except Exception as e:
            logger.error(f"EventBus: Failed to record system event: {e}")

# Singleton
_event_bus_instance: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance
