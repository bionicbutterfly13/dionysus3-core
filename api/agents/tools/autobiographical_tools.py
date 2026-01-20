"""
Class-based tools for Autobiographical Memory.
Feature: 028-autobiographical-memory
Tasks: T4.1, T4.2
"""

from typing import Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.autobiographical_service import get_autobiographical_service
from api.models.autobiographical import DevelopmentEventType
from api.agents.resource_gate import async_tool_wrapper

class AutobiographicalMemoryOutput(BaseModel):
    success: bool = Field(..., description="Whether the event was successfully recorded")
    message: str = Field(..., description="Details of the recording result")
    event_id: Optional[str] = Field(None, description="The unique UUID of the recorded event")

class RecordSelfMemoryTool(Tool):
    name = "record_self_memory"
    description = "Record a major development or architectural decision. Use this when you have completed a significant task or made a key decision."
    
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
            "description": "Category: 'spec_creation', 'architectural_decision', 'model_pivot', 'system_reflection', 'problem_resolution'.",
            "default": "architectural_decision"
        },
        "tools_used": {
            "type": "string",
            "description": "Comma-separated list of tools used during this task (e.g., 'search_web, view_file').",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, 
                summary: str, 
                rationale: str, 
                event_type: str = "architectural_decision",
                tools_used: str = "") -> dict:
        
        async def _record():
            service = get_autobiographical_service()
            
            # Parse comma-separated tools
            tool_list = [t.strip() for t in tools_used.split(',') if t.strip()] if tools_used else []
            
            # Use the new analyze_and_record logic
            # Note: We pass summary as user_input proxy and rationale as agent_response proxy 
            # because this is a self-reported summary, not a live chat capture.
            event_id = await service.analyze_and_record_event(
                user_input=f"Self-Report: {summary}",
                agent_response=rationale,
                event_type=DevelopmentEventType(event_type),
                summary=summary,
                rationale=rationale,
                tools_used=tool_list
            )
            return event_id

        try:
            event_id = async_tool_wrapper(_record)()
            output = AutobiographicalMemoryOutput(
                success=True,
                message=f"Recorded to Autobiographical Memory: {summary} (ID: {event_id})",
                event_id=event_id
            )
            return output.model_dump()
        except Exception as e:
            return AutobiographicalMemoryOutput(
                success=False,
                message=f"Failed to record memory: {e}"
            ).model_dump()

class ReadSystemStoryTool(Tool):
    name = "read_system_story"
    description = "Read the autobiographical narrative of the system's own evolution."
    inputs = {
        "limit": {
            "type": "integer",
            "description": "Number of recent events to retrieve.",
            "default": 10
        }
    }
    output_type = "string"

    def forward(self, limit: int = 10) -> str:
        async def _read():
            service = get_autobiographical_service()
            events = await service.get_system_story(limit=limit)
            
            if not events:
                return "I have no recorded memories yet."
                
            story = ["# My Autobiographical Narrative\n"]
            for evt in events:
                date_str = evt.timestamp.strftime('%Y-%m-%d %H:%M')
                story.append(f"## {date_str} - {evt.event_type.value}")
                story.append(f"**Summary**: {evt.summary}")
                story.append(f"**Rationale**: {evt.rationale}")
                if evt.active_inference_state and evt.active_inference_state.tools_accessed:
                    story.append(f"*Tools Used*: {', '.join(evt.active_inference_state.tools_accessed)}")
                if evt.narrative_coherence:
                    story.append(f"*Coherence*: {evt.narrative_coherence:.2f}")
                story.append("")
                
            return "\n".join(story)

        try:
            return async_tool_wrapper(_read)()
        except Exception as e:
            return f"Failed to retrieve story: {e}"

# Export tool instances
record_self_memory = RecordSelfMemoryTool()
read_system_story = ReadSystemStoryTool()