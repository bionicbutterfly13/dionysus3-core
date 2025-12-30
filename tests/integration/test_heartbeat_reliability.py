import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from api.services.heartbeat_service import HeartbeatService, HeartbeatContext
from api.models.action import EnvironmentSnapshot, ActionType
from api.models.goal import GoalAssessment

@pytest.mark.asyncio
async def test_heartbeat_reliability_retry_recovery():
    """Verify HeartbeatService recovers from malformed agent/LLM output via SchemaContext."""
    
    # 1. Setup mock context
    env = EnvironmentSnapshot(heartbeat_number=1, current_energy=10.0)
    goal_eval = GoalAssessment(active_goals=[], queued_goals=[], blocked_goals=[], stale_goals=[], issues=[])
    context = HeartbeatContext(environment=env, goal_assessment=goal_eval, goals=MagicMock())
    
    # 2. Mock ConsciousnessManager to return raw reasoning
    mock_agent_result = {
        "final_plan": "I should rest.",
        "actions": [{"action": "rest", "params": {}, "reason": "Low energy"}],
        "confidence": 0.9
    }
    
    # 3. Mock SchemaContext's LLM calls
    # First call: Invalid JSON
    # Second call: Valid JSON matching HeartbeatDecisionSchema
    valid_decision_json = json.dumps({
        "reasoning": "Agent suggested resting, I agree.",
        "emotional_state": 0.0,
        "confidence": 1.0,
        "actions": [{"action": "rest", "params": {}, "reason": "Normalized rest"}]
    })
    
    with patch("api.agents.consciousness_manager.ConsciousnessManager.run_ooda_cycle", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = mock_agent_result
        
        # Patch the chat_completion call INSIDE SchemaContext
        with patch("api.utils.schema_context.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = ["INVALID_JSON", valid_decision_json]
            
            service = HeartbeatService(driver=MagicMock())
            decision = await service._make_decision(context)
            
            # Verify result
            assert decision.reasoning == "Agent suggested resting, I agree."
            assert decision.action_plan.actions[0].action_type == ActionType.REST
            assert mock_llm.call_count == 2
            assert mock_agent.call_count == 1

@pytest.mark.asyncio
async def test_heartbeat_reliability_fallback_on_total_failure():
    """Verify HeartbeatService falls back gracefully if SchemaContext exhausts retries."""
    
    env = EnvironmentSnapshot(heartbeat_number=1, current_energy=10.0)
    goal_eval = GoalAssessment(active_goals=[], queued_goals=[], blocked_goals=[], stale_goals=[], issues=[])
    context = HeartbeatContext(environment=env, goal_assessment=goal_eval, goals=MagicMock())
    
    mock_agent_result = {
        "final_plan": "Agent reasoning.",
        "actions": [{"action": "recall", "params": {"q": "test"}, "reason": "testing"}],
        "confidence": 0.7
    }
    
    with patch("api.agents.consciousness_manager.ConsciousnessManager.run_ooda_cycle", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = mock_agent_result
        
        with patch("api.utils.schema_context.chat_completion", new_callable=AsyncMock) as mock_llm:
            # Always return garbage
            mock_llm.return_value = "TRASH"
            
            service = HeartbeatService(driver=MagicMock())
            decision = await service._make_decision(context)
            
            # Should fallback to mapping agent result directly
            assert "Agent reasoning" in decision.reasoning
            assert decision.action_plan.actions[0].action_type == ActionType.RECALL
            assert "normalization failed" in decision.action_plan.actions[0].reason
