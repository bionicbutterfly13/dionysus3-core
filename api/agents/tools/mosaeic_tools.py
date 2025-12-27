"""
Smolagent tools for MOSAEIC Protocol capture.
Feature: 024-mosaeic-protocol
"""

from smolagents import tool
from api.services.mosaeic_service import get_mosaeic_service


@tool
def mosaeic_capture(text: str, source_id: str = "agent_observation") -> str:
    """
    Capture a deep experiential state using the MOSAEIC protocol.
    Extracts Senses, Actions, Emotions, Impulses, and Cognitions from text.
    
    Args:
        text: The raw narrative or observed experience.
        source_id: Optional identifier for the source of this experience.
    """
    import asyncio
    service = get_mosaeic_service()
    
    # Run async in sync tool
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        capture = loop.run_until_complete(service.extract_capture(text, source_id))
        loop.run_until_complete(service.persist_capture(capture))
    else:
        capture = asyncio.run(service.extract_capture(text, source_id))
        asyncio.run(service.persist_capture(capture))
        
    summary = f"MOSAEIC Capture Successful: {capture.summary}\n"
    summary += f"- Senses: {capture.senses.content} (Intensity: {capture.senses.intensity})\n"
    summary += f"- Actions: {capture.actions.content} (Intensity: {capture.actions.intensity})\n"
    summary += f"- Emotions: {capture.emotions.content} (Intensity: {capture.emotions.intensity})\n"
    summary += f"- Impulses: {capture.impulses.content} (Intensity: {capture.impulses.intensity})\n"
    summary += f"- Cognitions: {capture.cognitions.content} (Intensity: {capture.cognitions.intensity})\n"
    
    return summary
