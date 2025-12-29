"""
Class-based tools for Autobiographical Memory.
Feature: 028-autobiographical-memory
Tasks: T4.1, T4.2
"""

from typing import Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.autobiographical_service import get_autobiographical_service
from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
from api.agents.resource_gate import async_tool_wrapper

class AutobiographicalMemoryOutput(BaseModel):
    success: bool = Field(..., description="Whether the event was successfully recorded")
    message: str = Field(..., description="Details of the recording result")
    event_id: Optional[str] = Field(None, description="The unique UUID of the recorded event")

class RecordSelfMemoryTool(Tool):
    name = "record_self_memory"
    description = "Record a major development or architectural decision in the system's own memory."
    
    inputs = {
        "summary": {
            "type": "string",
            "description": "Concise summary of what changed."
        },
        "rationale": {
            "type": "string",
            "description": "The reason for the change (the 'why')."
        },
        "event_type": {
            "type": "string",
            "description": "Category: 'spec_creation', 'architectural_decision', 'model_pivot', 'system_reflection'.",
            "default": "architectural_decision"
        }
    }
    output_type = "any"

    def forward(self, summary: str, rationale: str, event_type: str = "architectural_decision") -> dict:
        import uuid
        
        async def _record():
            service = get_autobiographical_service()
            event_id = str(uuid.uuid4())
            event = DevelopmentEvent(
                event_id=event_id,
                event_type=DevelopmentEventType(event_type),
                summary=summary,
                rationale=rationale,
                impact="System evolution and integrity"
            )
            await service.record_event(event)
            return event_id

        try:
            event_id = async_tool_wrapper(_record)()
            output = AutobiographicalMemoryOutput(
                success=True,
                message=f"Recorded to Autobiographical Memory: {summary}",
                event_id=event_id
            )
            return output.model_dump()
        except Exception as e:
            return AutobiographicalMemoryOutput(
                success=False,
                message=f"Failed to record memory: {e}"
            ).model_dump()

# Export tool instance
record_self_memory = RecordSelfMemoryTool()