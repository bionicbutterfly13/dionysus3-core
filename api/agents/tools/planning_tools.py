"""
Active Inference Planning Tools (Feature 046)
"""

import logging
from typing import Optional
from smolagents import Tool
from pydantic import BaseModel, Field

from api.services.action_planner_service import get_action_planner
from api.agents.resource_gate import async_tool_wrapper

logger = logging.getLogger("dionysus.planning_tools")

class PlanningOutput(BaseModel):
    best_plan: str = Field(..., description="The recommended action sequence.")
    total_efe: float = Field(..., description="The EFE score of the best plan.")
    rationale: str = Field(..., description="Why this plan was selected.")
    candidates: list = Field(default_factory=list, description="All evaluated plans.")

class ActivePlannerTool(Tool):
    name = "active_planner"
    description = "Strategic Lookahead Planner. Generates and evaluates multi-step action plans using Active Inference."
    
    inputs = {
        "task": {
            "type": "string",
            "description": "The task to plan for."
        },
        "goal": {
            "type": "string",
            "description": "The desired end state or criteria."
        },
        "context": {
            "type": "string",
            "description": "Optional background or current state description.",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, task: str, goal: str, context: Optional[str] = "") -> dict:
        async def _run():
            planner = get_action_planner()
            # Use provided context or build from inputs
            ctx_dict = {"original_task": task, "extra_context": context}
            result = await planner.select_best_policy(task, ctx_dict, goal)
            return result

        try:
            result = async_tool_wrapper(_run)()
            plan_str = "\n".join([f"{i+1}. {a.tool_name}: {a.expected_outcome}" for i, a in enumerate(result.best_policy.actions)])
            
            output = PlanningOutput(
                best_plan=plan_str,
                total_efe=result.best_policy.total_efe,
                rationale=result.planning_trace,
                candidates=[{"name": c.name, "efe": c.total_efe} for c in result.candidates]
            )
            return output.model_dump()
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return {"error": str(e)}

# Export tool instance
active_planner = ActivePlannerTool()
