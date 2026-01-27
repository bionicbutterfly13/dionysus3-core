import logging
import numpy as np
from typing import Dict, Any, List, Optional
from smolagents import Tool
from pydantic import BaseModel, Field

from api.services.active_inference_service import get_active_inference_service
from api.models.belief_state import BeliefState as CanonicalBeliefState

logger = logging.getLogger("dionysus.agents.tools.active_inference")

class EFEOutput(BaseModel):
    policy_id: str = Field(..., description="Identifier for the policy trajectory")
    efe: float = Field(..., description="Expected Free Energy (G-score)")
    pragmatic_value: float = Field(..., description="Preference fulfillment (accuracy)")
    epistemic_value: float = Field(..., description="Information gain (complexity reduction)")

class ComputePolicyEFETool(Tool):
    name = "compute_policy_efe"
    description = """
    Computes the formal Expected Free Energy (G-score) for a proposed action or policy trajectory.
    Lower G-scores indicate better policies.
    Use this to proactively evaluate multiple candidate plans before deciding on one.
    """
    
    inputs = {
        "policy_id": {
            "type": "string",
            "description": "A unique identifier for this plan/trajectory."
        },
        "action_indices": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "List of action indices representing the policy trajectory (e.g., [0, 1, 0])."
        },
        "num_states": {
            "type": "integer",
            "description": "Dimensionality of the state space.",
            "default": 2,
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, policy_id: str, action_indices: list, num_states: int = 2) -> dict:
        try:
            service = get_active_inference_service()
            
            # 1. Prepare default/current model
            # In a more advanced implementation, we'd retrieve this from the agent's world-model container
            model = service._get_default_model(num_states)
            
            # 2. Prepare Belief State (Placeholder - in real OODA, this comes from Perception)
            mean = [1.0 / num_states] * num_states
            belief = CanonicalBeliefState.from_mean_and_variance(mean=mean, variance=[0.1]*num_states)
            
            # 3. Calculate EFE
            policy_np = np.array(action_indices)
            efe = service.calculate_efe(belief, model, policy_np, horizon=len(policy_np))
            
            return {
                "policy_id": policy_id,
                "efe": float(efe),
                "status": "computed",
                "recommendation": "LOW_G" if efe < 0 else "HIGH_G"
            }
        except Exception as e:
            logger.error(f"EFE calculation failed: {e}")
            return {"status": "error", "error": str(e)}

class UpdateBeliefPrecisionTool(Tool):
    name = "update_belief_precision"
    description = """
    Actively adjusts the precision (inverse variance) of internal agent models based on surprisal.
    Use this when observations conflict with expectations to force a model update.
    """
    
    inputs = {
        "agent_name": {
            "type": "string",
            "description": "The name of the target cognitive agent (e.g., 'perception', 'reasoning')."
        },
        "precision_delta": {
            "type": "number",
            "description": "Amount to adjust confidence (positive for focus, negative for exploration/openness)."
        }
    }
    output_type = "any"

    def forward(self, agent_name: str, precision_delta: float) -> dict:
        from api.agents.metacognition_agent import MetacognitionAgent
        try:
            # We use the service-level modulation directly to avoid circular agent imports if possible
            from api.services.efe_engine import adjust_agent_precision, get_agent_precision
            
            old_p = get_agent_precision(agent_name)
            new_p = adjust_agent_precision(agent_name, precision_delta)
            
            return {
                "agent_name": agent_name,
                "old_precision": float(old_p),
                "new_precision": float(new_p),
                "status": "modulated"
            }
        except Exception as e:
            logger.error(f"Precision update failed: {e}")
            return {"status": "error", "error": str(e)}

# Export instances
compute_policy_efe = ComputePolicyEFETool()
update_belief_precision = UpdateBeliefPrecisionTool()
