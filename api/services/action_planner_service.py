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
        Simulate the entire path in one batch LLM call to calculate cumulative EFE.
        """
        prompt = f"""
        Initial Context: {str(context)[:1000]}
        Policy to Evaluate: {policy.name}
        Goal: {goal}
        
        Proposed Actions:
        {json.dumps([{"tool": a.tool_name, "rationale": a.rationale} for a in policy.actions], indent=2)}
        
        Analyze this sequence of actions. For EACH step, provide:
        1. uncertainty (0.0 - 1.0): Probability of ambiguous results or failure.
        2. divergence (0.0 - 1.0): Distance from the final goal state.
        
        Respond ONLY with a JSON list of objects, one per action:
        [
          {{"uncertainty": 0.2, "divergence": 0.8}},
          ...
        ]
        """
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a strategic Active Inference simulator.",
            max_tokens=512
        )
        
        try:
            # Cleanup JSON
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            scores = json.loads(cleaned)
            
            total_efe = 0.0
            for i, score in enumerate(scores):
                if i < len(policy.actions):
                    step_efe = float(score.get("uncertainty", 0.5)) + float(score.get("divergence", 0.5))
                    total_efe += step_efe
            
            policy.total_efe = total_efe
            policy.confidence = max(0.0, 1.0 - (total_efe / (len(policy.actions) * 2.0 or 1)))
            
        except Exception as e:
            logger.error(f"Batch evaluation failed: {e}. Falling back to default EFE.")
            policy.total_efe = len(policy.actions) * 1.0
            policy.confidence = 0.5
            
        return policy

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