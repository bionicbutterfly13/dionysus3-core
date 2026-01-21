from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

class PolicyAction(BaseModel):
    """A single action in a policy sequence."""
    tool_name: str
    rationale: str
    expected_outcome: str

class ActionPolicy(BaseModel):
    """A sequence of actions forming a plan."""
    id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    name: str = Field(..., description="Short name for the policy (e.g., 'Epistemic Search')")
    actions: List[PolicyAction] = Field(default_factory=list)
    total_efe: float = Field(0.0, description="Cumulative Expected Free Energy for this path.")
    confidence: float = Field(0.0, description="Estimated probability of goal achievement.")

class PolicyResult(BaseModel):
    """The outcome of an active inference planning session."""
    best_policy: ActionPolicy
    candidates: List[ActionPolicy]
    planning_trace: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
