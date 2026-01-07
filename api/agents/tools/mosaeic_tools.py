"""
Class-based tools for MOSAEIC Protocol capture.
Feature: 024-mosaeic-protocol
Tasks: T4.1, T4.2
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.mosaeic_service import get_mosaeic_service
from api.agents.resource_gate import async_tool_wrapper

logger = logging.getLogger("dionysus.mosaeic_tools")

class MosaeicWindow(BaseModel):
    content: str = Field(..., description="The textual content of the window")
    intensity: float = Field(..., ge=0.0, le=1.0, description="The emotional or sensory intensity")

class MosaeicCaptureOutput(BaseModel):
    success: bool = Field(True, description="Whether the capture was successful")
    summary: str = Field(..., description="Overview of the captured experiential state")
    senses: MosaeicWindow = Field(..., description="Senses window (Sight, Sound, etc.)")
    actions: MosaeicWindow = Field(..., description="Actions window (Physical movements)")
    emotions: MosaeicWindow = Field(..., description="Emotions window (Feeling states)")
    impulses: MosaeicWindow = Field(..., description="Impulses window (Action tendencies)")
    cognitions: MosaeicWindow = Field(..., description="Cognitions window (Thoughts, images)")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class MosaeicCaptureTool(Tool):
    name = "mosaeic_capture"
    description = "Capture a deep experiential state using the MOSAEIC protocol (Senses, Actions, Emotions, Impulses, Cognitions)."
    
    inputs = {
        "text": {
            "type": "string",
            "description": "The raw narrative or observed experience."
        },
        "source_id": {
            "type": "string",
            "description": "Optional identifier for the source of this experience.",
            "default": "agent_observation",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, text: str, source_id: str = "agent_observation") -> dict:
        from api.agents.resilience import wrap_with_resilience
        
        async def _capture():
            service = get_mosaeic_service()
            capture = await service.extract_capture(text, source_id)
            await service.persist_capture(capture)
            return capture

        try:
            capture = async_tool_wrapper(_capture)()
            
            output = MosaeicCaptureOutput(
                summary=capture.summary,
                senses=MosaeicWindow(content=capture.senses.content, intensity=capture.senses.intensity),
                actions=MosaeicWindow(content=capture.actions.content, intensity=capture.actions.intensity),
                emotions=MosaeicWindow(content=capture.emotions.content, intensity=capture.emotions.intensity),
                impulses=MosaeicWindow(content=capture.impulses.content, intensity=capture.impulses.intensity),
                cognitions=MosaeicWindow(content=capture.cognitions.content, intensity=capture.cognitions.intensity)
            )
            return output.model_dump()
            
        except Exception as e:
            logger.error(f"MOSAEIC capture failed: {e}")
            # T005: Wrap with resilience hint
            error_msg = f"Error during MOSAEIC capture: {e}"
            hinted_error = wrap_with_resilience(error_msg)
            return {
                "success": False,
                "summary": "Capture failed",
                "error": hinted_error
            }

# Export tool instance
mosaeic_capture = MosaeicCaptureTool()