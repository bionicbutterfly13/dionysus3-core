"""
Smolagent tools for Autobiographical Memory.
Feature: 028-autobiographical-memory
"""

from smolagents import tool
from api.services.autobiographical_service import get_autobiographical_service
from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType


@tool
def record_self_memory(summary: str, rationale: str, event_type: str = "architectural_decision") -> str:
    """
    Record a major development or architectural decision in the system's own memory.
    Ensures we remember why things changed.
    
    Args:
        summary: Concise summary of what changed.
        rationale: The reason for the change (the 'why').
        event_type: Category: 'spec_creation', 'architectural_decision', 'model_pivot', 'system_reflection'.
    """
    import asyncio
    import uuid
    service = get_autobiographical_service()
    
    event = DevelopmentEvent(
        event_id=str(uuid.uuid4()),
        event_type=DevelopmentEventType(event_type),
        summary=summary,
        rationale=rationale,
        impact="System evolution and integrity"
    )
    
    # Run async in sync tool
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(service.record_event(event))
    else:
        asyncio.run(service.record_event(event))
        
    return f"Recorded to Autobiographical Memory: {summary}"
