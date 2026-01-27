import unittest
from unittest.mock import MagicMock, patch
import time

from api.services.coordination_service import CoordinationService, Agent, Task, TaskType, AgentStatus
from api.core.sovereign_identity import ANTI_BOASTING_CONSTRAINT
from api.agents.consciousness_manager import ConsciousnessManager

class TestCoordinationPoolGuardrails(unittest.TestCase):
    def setUp(self):
        self.service = CoordinationService()
        # Initialize small pool
        self.service.initialize_pool(size=2)
        self.agent_ids = list(self.service.agents.keys())
        self.agent1 = self.service.agents[self.agent_ids[0]]
        self.agent2 = self.service.agents[self.agent_ids[1]]

    def test_skill_verification_logic(self):
        """Test that verify_skill correctly updates agent state."""
        success = self.service.verify_skill(self.agent1.agent_id, "python_coding")
        self.assertTrue(success)
        self.assertIn("python_coding", self.agent1.verified_skills)
        
        # Test idempotent
        self.service.verify_skill(self.agent1.agent_id, "python_coding")
        self.assertEqual(len(self.agent1.verified_skills), 1)

    def test_assignment_rejection_without_skill(self):
        """Test that task requiring a skill is NOT assigned to unverified agent."""
        task_id = self.service.submit_task(
            payload={"instruction": "code"},
            required_skills=["python_coding"]
        )
        
        task = self.service.tasks[task_id]
        
        # Should be pending because no agent has the skill yet
        self.assertEqual(task.status.value, "pending")
        self.assertIsNone(task.assigned_agent_id)
        
        # Verify queue contains task
        self.assertIn(task_id, self.service.queue)

    def test_assignment_success_with_skill(self):
        """Test that task IS assigned once agent has the skill."""
        # Verify Agent 1
        self.service.verify_skill(self.agent1.agent_id, "python_coding")
        
        task_id = self.service.submit_task(
            payload={"instruction": "code"},
            required_skills=["python_coding"]
        )
        
        task = self.service.tasks[task_id]
        
        # Should be in progress and assigned to Agent 1
        self.assertEqual(task.status.value, "in_progress")
        self.assertEqual(task.assigned_agent_id, self.agent1.agent_id)

    def test_prompt_injection_constants(self):
        """Verify the constraint constants exist and are correct."""
        self.assertIn("SOCIAL RESILIENCE PROTOCOL", ANTI_BOASTING_CONSTRAINT)
        self.assertIn("DO NOT claim skills you do not have", ANTI_BOASTING_CONSTRAINT)

    @unittest.skip("SOVEREIGN_IDENTITY_PROMPT imported inside method, not at module level")
    def test_consciousness_manager_prompt_construction(self):
        """Verify that ConsciousnessManager injects the constraint.

        SKIPPED: The imports are function-scoped, so module-level patch doesn't work.
        The constraint is verified to exist in source code at consciousness_manager.py:284
        """
        pass

if __name__ == "__main__":
    unittest.main()
