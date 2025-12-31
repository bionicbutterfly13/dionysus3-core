"""
Action Planner Service (Feature 046)

Generates and evaluates multi-step action policies using Active Inference principles.
"""

import json
import logging
from typing import List, Dict, Any
from api.models.policy import ActionPolicy, PolicyAction, PolicyResult
from api.services.llm_service import chat_completion

logger = logging.getLogger("dionysus.action_planner")

class ActionPlannerService:
    """
    Cognitive planner that uses lookahead simulation to select the action path
    with the lowest cumulative Expected Free Energy.
    """

    async def select_best_policy(
        self, 
        task: str,
        context: Dict[str, Any],
        goal: str
    ) -> PolicyResult:
        """
        Orchestrates the policy generation, evaluation, and selection.
        """
        # 1. Generate candidate policies
        candidates = await self.generate_policies(task, context, goal)
        
        # 2. Evaluate each policy (Active Inference Lookahead)
        evaluated_candidates = []
        for policy in candidates:
            evaluated = await self.evaluate_policy(policy, task, context, goal)
            evaluated_candidates.append(evaluated)
            
        # 3. Select policy with minimum EFE
        if not evaluated_candidates:
            raise ValueError("No policies generated.")
            
        best_policy = min(evaluated_candidates, key=lambda p: p.total_efe)
        
        return PolicyResult(
            best_policy=best_policy,
            candidates=evaluated_candidates,
            planning_trace=f"Selected '{best_policy.name}' with EFE {best_policy.total_efe:.2f}."
        )

    async def generate_policies(
        self,
        task: str,
        context: Dict[str, Any],
        goal: str
    ) -> List[ActionPolicy]:
        """
        Use LLM to propose 3 strategic reasoning paths.
        """
        prompt = f"""
        Given the task: {task}
        And goal: {goal}
        
        Generate 3 distinct strategic action sequences (Policies) to achieve the goal.
        Available tools: understand_question, recall_related, examine_answer, backtracking, context_explorer, cognitive_check.
        
        Respond ONLY with a JSON list of objects:
        [
          {{
            "name": "Pragmatic Execution",
            "actions": [
              {{"tool_name": "...", "rationale": "...", "expected_outcome": "..."}},
              ...
            ]
          }}
        ]
        """
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a strategic planning agent.",
            max_tokens=1024
        )
        
        try:
            # Simple JSON cleanup
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            data = json.loads(cleaned)
            return [ActionPolicy(**p) for p in data]
        except Exception as e:
            logger.error(f"Failed to generate policies: {e}. Raw: {response}")
            return [self._get_fallback_policy()]

    async def evaluate_policy(
        self,
        policy: ActionPolicy,
        task: str,
        context: Dict[str, Any],
        goal: str
    ) -> ActionPolicy:
        """
        Simulate the path and calculate cumulative EFE.
        """
        total_efe = 0.0
        current_context_desc = str(context)
        
        for action in policy.actions:
            # Simulating outcome via LLM heuristic (simplified for performance)
            # Higher uncertainty in outcome = higher entropy (EFE component)
            # Divergence from goal = goal divergence (EFE component)
            
            # For this lightweight version, we ask the LLM to score the step's EFE
            # based on (Uncertainty + Distance to Goal).
            step_efe = await self._simulate_step_efe(action, current_context_desc, goal)
            total_efe += step_efe
            
            # Update simulated context
            current_context_desc += f"\n[Action: {action.tool_name} -> {action.expected_outcome}]"
            
        policy.total_efe = total_efe
        # Confidence is inverse of EFE (normalized)
        policy.confidence = max(0.0, 1.0 - (total_efe / (len(policy.actions) * 2.0 or 1)))
        
        return policy

    async def _simulate_step_efe(self, action: PolicyAction, context: str, goal: str) -> float:
        """
        Ask the LLM to estimate the Expected Free Energy of an action step.
        """
        prompt = f"""
        Context: {context[:500]}
        Action: {action.tool_name} ({action.rationale})
        Goal: {goal}
        
        Score this action step's Expected Free Energy (EFE).
        EFE = Uncertainty (0.0-1.0) + Goal Divergence (0.0-1.0).
        - Uncertainty: How likely is this action to fail or produce ambiguous results?
        - Goal Divergence: How much does this action NOT move us closer to the final goal?
        
        Respond ONLY with a JSON object: {{"uncertainty": 0.5, "divergence": 0.5, "total": 1.0}}
        """
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an Active Inference scoring engine.",
            max_tokens=128
        )
        
        try:
            data = json.loads(response.strip())
            return float(data.get("total", 1.0))
        except:
            return 1.0

    def _get_fallback_policy(self) -> ActionPolicy:
        return ActionPolicy(
            name="Direct Reasoning",
            actions=[
                PolicyAction(
                    tool_name="direct_reason", 
                    rationale="Fallback to standard path.", 
                    expected_outcome="Task completion"
                )
            ]
        )

# Singleton
_planner_instance = None

def get_action_planner() -> ActionPlannerService:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = ActionPlannerService()
    return _planner_instance
