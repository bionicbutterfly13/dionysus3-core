"""
Unit tests for Action Planner Service (Feature 046).
"""
import pytest
from unittest.mock import AsyncMock, patch
from api.services.action_planner_service import ActionPlannerService
from api.models.policy import ActionPolicy, PolicyAction

@pytest.mark.asyncio
async def test_generate_policies():
    planner = ActionPlannerService()
    
    mock_response = """
    [
      {
        "name": "Test Plan",
        "actions": [
          {"tool_name": "tool1", "rationale": "rat1", "expected_outcome": "out1"}
        ]
      }
    ]
    """
    
    with patch("api.services.action_planner_service.chat_completion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response
        
        policies = await planner.generate_policies("task", {}, "goal")
        
        assert len(policies) == 1
        assert policies[0].name == "Test Plan"
        assert policies[0].actions[0].tool_name == "tool1"

@pytest.mark.asyncio
async def test_evaluate_policy():
    planner = ActionPlannerService()
    policy = ActionPolicy(
        name="Plan A",
        actions=[PolicyAction(tool_name="t1", rationale="r1", expected_outcome="o1")]
    )
    
    with patch("api.services.action_planner_service.chat_completion", new_callable=AsyncMock) as mock_llm:
        # Mocking the batched JSON response: a list of one object for one action
        mock_llm.return_value = '[{"uncertainty": 0.2, "divergence": 0.3}]'
        
        evaluated = await planner.evaluate_policy(policy, "task", {}, "goal")
        
        # total_efe = 0.2 + 0.3 = 0.5
        assert evaluated.total_efe == 0.5
        assert evaluated.confidence > 0.0

@pytest.mark.asyncio
async def test_select_best_policy():
    planner = ActionPlannerService()
    
    # Mocking generate_policies and evaluate_policy
    p1 = ActionPolicy(name="Bad Plan", total_efe=2.0)
    p2 = ActionPolicy(name="Good Plan", total_efe=0.5)
    
    with patch.object(planner, "generate_policies", new_callable=AsyncMock) as mock_gen, \
         patch.object(planner, "evaluate_policy", new_callable=AsyncMock) as mock_eval:
        
        mock_gen.return_value = [p1, p2]
        mock_eval.side_effect = lambda p, t, c, g: p
        
        result = await planner.select_best_policy("task", {}, "goal")
        
        assert result.best_policy.name == "Good Plan"
        assert len(result.candidates) == 2
