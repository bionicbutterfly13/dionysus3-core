"""
Marketing Tools for specialized Strategist agent.
"""

import os
import logging
from smolagents import Tool
from pydantic import BaseModel, Field
from api.services.graphiti_service import get_graphiti_service
from api.agents.resource_gate import async_tool_wrapper

logger = logging.getLogger("dionysus.marketing_tools")

class AvatarIntelOutput(BaseModel):
    findings: str
    deep_desires: list = Field(default_factory=list)
    pain_points: list = Field(default_factory=list)

class GetAvatarIntelTool(Tool):
    name = "get_avatar_intel"
    description = "Searches the Knowledge Graph for deep psychological insights on the [LEGACY_AVATAR_HOLDER]."
    
    inputs = {
        "topic": {
            "type": "string",
            "description": "Specific trait or behavior (e.g., 'replay loops', 'safety drives')."
        }
    }
    output_type = "any"

    def forward(self, topic: str) -> dict:
        async def _run():
            graphiti = await get_graphiti_service()
            # Target the avatar_intel group we used during ingestion
            results = await graphiti.search(f"[LEGACY_AVATAR_HOLDER] traits related to {topic}", group_ids=["avatar_intel"], limit=10)
            return results

        try:
            results = async_tool_wrapper(_run)()
            findings = "\n".join([e.get("fact", "") for e in results.get("edges", [])])
            return {"findings": findings}
        except Exception as e:
            return {"error": str(e)}

class GetMarketingFrameworkTool(Tool):
    name = "get_marketing_framework"
    description = "Retrieves specific conversion templates from the 21 Forbidden Frameworks library."
    
    inputs = {
        "framework_name": {
            "type": "string",
            "description": "The name or number of the framework (e.g., 'Contrarian Truth', 'Socratic Teaser')."
        }
    }
    output_type = "any"

    def forward(self, framework_name: str) -> dict:
        path = "/Volumes/Asylum/dev/email-sequence/21ForbiddenEmailFrameworks (Email Bundle).docx.txt"
        if not os.path.exists(path):
            return {"error": "Framework library not found."}
            
        try:
            with open(path, "r") as f:
                content = f.read()
            
            # Simple keyword search within the file for the framework
            # In a more robust version, we would parse this into chunks
            if framework_name.lower() in content.lower():
                # Extract a 2000-char window around the name
                idx = content.lower().find(framework_name.lower())
                window = content[idx:idx+3000]
                return {"framework_context": window}
            else:
                return {"error": f"Framework '{framework_name}' not found in library."}
        except Exception as e:
            return {"error": str(e)}

# Export tool instances
get_avatar_intel = GetAvatarIntelTool()
get_marketing_framework = GetMarketingFrameworkTool()
