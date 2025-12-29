"""
Class-based tools for Cognitive Reasoning and EFE reflection.
Feature: 003-thoughtseed-active-inference
Tasks: T4.1, T4.2
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.graphiti_service import get_graphiti_service
from api.services.efe_engine import get_efe_engine
from api.agents.resource_gate import async_tool_wrapper

logger = logging.getLogger("dionysus.cognitive_tools")

class ExplorerOutput(BaseModel):
    project_id: str = Field(..., description="Scoping project identifier")
    query: str = Field(..., description="Original search query")
    attractors: List[str] = Field(..., description="List of detected semantic attractors")
    recommendation: str = Field(..., description="Actionable recommendation based on EFE")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class ContextExplorerTool(Tool):
    name = "context_explorer"
    description = "Explorer Agent tool. Scans knowledge graph for semantic attractors and prunes context."
    
    inputs = {
        "project_id": {
            "type": "string",
            "description": "Scoping ID for the research."
        },
        "query": {
            "type": "string",
            "description": "Specific domain or task query."
        }
    }
    output_type = "any"

    def forward(self, project_id: str, query: str) -> dict:
        async def _run():
            graphiti = await get_graphiti_service()
            return await graphiti.search(f"attractor basins for {query} in project {project_id}", limit=5)
        
        try:
            search_results = async_tool_wrapper(_run)()
            edges = search_results.get("edges", [])
            
            attractors = [e.get('fact') for e in edges if e.get('fact')]
            
            if not attractors:
                return ExplorerOutput(
                    project_id=project_id,
                    query=query,
                    attractors=[],
                    recommendation="No semantic attractors found. Increase epistemic search."
                ).model_dump()

            return ExplorerOutput(
                project_id=project_id,
                query=query,
                attractors=attractors,
                recommendation="Ground reasoning in the 'Analytical Professional' basin to minimize free energy."
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Explorer search failed: {e}")
            return ExplorerOutput(
                project_id=project_id,
                query=query,
                attractors=[],
                recommendation="Fallback to base context.",
                error=str(e)
            ).model_dump()

class CognitiveCheckOutput(BaseModel):
    efe_score: float = Field(..., description="The calculated Expected Free Energy score")
    recommended_mode: str = Field(..., description="PRAGMATIC or EPISTEMIC based on EFE")
    reasoning: str = Field(..., description="Detailed explanation of the EFE calculation")

class CognitiveCheckTool(Tool):
    name = "cognitive_check"
    description = "Autonomous EFE self-reflection tool. Calculates the agent's current Expected Free Energy."
    
    inputs = {
        "uncertainty_level": {
            "type": "number",
            "description": "0.0-1.0 (Entropy)"
        },
        "goal_alignment": {
            "type": "number",
            "description": "0.0-1.0 (Similarity to goal)"
        }
    }
    output_type = "any"

    def forward(self, uncertainty_level: float, goal_alignment: float) -> dict:
        efe = float(uncertainty_level + (1.0 - goal_alignment))
        status = "PRAGMATIC" if efe < 0.5 else "EPISTEMIC"
        
        output = CognitiveCheckOutput(
            efe_score=efe,
            recommended_mode=status,
            reasoning=f"EFE is {efe:.2f}. " + ("Context is stable, proceed to execution." if status == "PRAGMATIC" else "Uncertainty high, prioritize research/recall.")
        )
        return output.model_dump()

# Export tool instances
context_explorer = ContextExplorerTool()
cognitive_check = CognitiveCheckTool()
