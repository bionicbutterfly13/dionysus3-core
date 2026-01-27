"""
System Event Bus (Feature 050)
Centralized bus for cognitive and system events.

Ensures that events from any source (OODA, background workers, API) 
can trigger the Consciousness Integration Pipeline.
"""

import logging
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime

from api.services.consciousness_integration_pipeline import get_consciousness_pipeline
from api.models.meta_tot import ActiveInferenceState

logger = logging.getLogger("dionysus.event_bus")

class EventBus:
    def __init__(self):
        self.pipeline = get_consciousness_pipeline()
        self._subscribers: Dict[str, List[Callable]] = {
            "cognitive_event": [],
            "system_event": [],
            "precision_update": []
        }

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Register a subscriber for an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"EventBus: Subscribed to {event_type}")

    async def emit_cognitive_event(
        self,
        source: str,
        problem: str,
        reasoning: str,
        state: Optional[ActiveInferenceState] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
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
            
        # 1. Integration Pipeline (Synchronous processing)
        try:
            await self.pipeline.process_cognitive_event(
                problem=problem,
                reasoning_trace=reasoning,
                active_inference_state=state,
                context=context
            )
        except Exception as e:
            logger.error(f"EventBus: Pipeline processing failed for {source}: {e}")

        # 2. Notify Subscribers (Asynchronous notifications)
        event_data = {
            "source": source,
            "problem": problem,
            "reasoning": reasoning,
            "state": state,
            "context": context
        }
        await self._notify_subscribers("cognitive_event", event_data)

    async def _notify_subscribers(self, event_type: str, data: Dict[str, Any]) -> None:
        """Helper to run all subscriber callbacks for an event."""
        subscribers = self._subscribers.get(event_type, [])
        for callback in subscribers:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.warning(f"EventBus: Subscriber for {event_type} failed: {e}")

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
