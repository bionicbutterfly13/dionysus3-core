"""
Cognitive Meta-Coordinator (Feature 049)
Active management layer for reasoning mode selection and tool enforcement.

Dynamically selects between Direct Reasoning, Cognitive Tools (Surgeon), 
and Meta-ToT based on task complexity and entropy.
Integrates Affordance awareness to guide agent attention.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from api.models.meta_tot import MetaToTDecision
from api.services.meta_tot_decision import get_meta_tot_decision_service
from api.services.affordance_context_service import get_affordance_service

logger = logging.getLogger("dionysus.meta_coordinator")

class ReasoningMode(str, Enum):
    DIRECT = "direct"
    SURGEON = "surgeon" # Checklist-driven
    META_TOT = "meta_tot" # Tree-of-thought

class CoordinationPlan:
    mode: ReasoningMode
    afforded_tools: List[str]
    enforce_checklist: bool
    rationale: str

class CognitiveMetaCoordinator:
    def __init__(self):
        self.decision_svc = get_meta_tot_decision_service()
        self.affordance_svc = get_affordance_service()

    async def coordinate(self, task: str, available_tools: List[str], context: Optional[Dict[str, Any]] = None) -> CoordinationPlan:
        """
        Determine the optimal reasoning strategy for the given task.
        """
        context = context or {}
        
        # 1. Decide on Meta-ToT activation (Strategic Layer)
        meta_tot_decision = self.decision_svc.decide(task, context)
        
        # 2. Get Affordances (Attention Layer)
        affordance_map = await self.affordance_svc.get_affordances(task, available_tools, context)
        
        # 3. Final Strategy Selection
        plan = CoordinationPlan()
        plan.afforded_tools = affordance_map.afforded_tools
        
        if meta_tot_decision.use_meta_tot:
            plan.mode = ReasoningMode.META_TOT
            plan.enforce_checklist = True
            plan.rationale = f"High entropy detected ({meta_tot_decision.complexity_score:.2f}). Activating Tree-of-Thought planning."
        elif meta_tot_decision.complexity_score > 0.4:
            plan.mode = ReasoningMode.SURGEON
            plan.enforce_checklist = True
            plan.rationale = "Medium complexity detected. Enforcing Surgeon protocol for verification."
        else:
            plan.mode = ReasoningMode.DIRECT
            plan.enforce_checklist = False
            plan.rationale = "Low complexity task. Proceeding with direct response."
            
        logger.info(f"Cognitive coordination complete: Mode={plan.mode.value}")
        return plan

_coordinator_instance: Optional[CognitiveMetaCoordinator] = None

def get_meta_coordinator() -> CognitiveMetaCoordinator:
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = CognitiveMetaCoordinator()
    return _coordinator_instance
