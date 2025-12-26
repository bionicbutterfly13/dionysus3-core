import os
import json
from typing import Any, Dict

from smolagents import CodeAgent, LiteLLMModel
from api.agents.perception_agent import PerceptionAgent
from api.agents.reasoning_agent import ReasoningAgent
from api.agents.metacognition_agent import MetacognitionAgent

class ConsciousnessManager:
    """
    Orchestrates the specialized cognitive agents (Perception, Reasoning, Metacognition)
    to execute a full OODA (Observe, Orient, Decide, Act) loop.
    This manager represents the highest level of cognitive function in the system.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        """
        Initialize the Consciousness Manager and its sub-agents.
        """
        # Using a more capable model for orchestration
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Instantiate the specialized sub-agents
        self.perception_agent = PerceptionAgent()
        self.reasoning_agent = ReasoningAgent()
        self.metacognition_agent = MetacognitionAgent()

        # The orchestrator agent that will generate the plan to call the sub-agents
        # NOTE: The 'managed_agents' parameter is a conceptual representation.
        # In practice, the orchestrator's prompt will guide it to generate a plan
        # that we then execute by calling the sub-agents' .run() methods.
        self.orchestrator = CodeAgent(
            tools=[], # The orchestrator does not use tools directly
            model=self.model,
            name="consciousness_manager",
            description="Orchestrates perception, reasoning, and metacognition to form a coherent plan."
        )

    def run_ooda_cycle(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a full OODA loop.

        Args:
            initial_context: The initial state to begin the cycle.

        Returns:
            A dictionary containing the results of each phase and the final plan.
        """
        print("=== CONSCIOUSNESS OODA CYCLE START ===")

        # 1. OBSERVE
        print("\n--- Phase 1: OBSERVE ---")
        perception_task = "Gather a full snapshot of the current environment and recall any memories relevant to the primary goals."
        observation_result = self.perception_agent.run(perception_task)
        print(f"Perception Result: {observation_result}")

        # 2. ORIENT
        print("\n--- Phase 2: ORIENT ---")
        reasoning_task = f"""
        Based on the following observation, analyze the situation, identify patterns, and synthesize key insights.
        
        Observation:
        {observation_result}
        
        Initial Context:
        {json.dumps(initial_context, indent=2)}
        """
        orientation_result = self.reasoning_agent.run(reasoning_task)
        print(f"Reasoning Result: {orientation_result}")

        # 3. DECIDE
        print("\n--- Phase 3: DECIDE ---")
        metacognition_task = f"""
        Given the current orientation and insights, review the goal state and decide on the strategic direction.
        Should goals be reprioritized? Do any mental models need revision based on the new information?

        Orientation:
        {orientation_result}
        """
        decision_result = self.metacognition_agent.run(metacognition_task)
        print(f"Metacognition Result: {decision_result}")

        # 4. ACT (Plan Synthesis)
        print("\n--- Phase 4: ACT (Plan Synthesis) ---")
        synthesis_task = f"""
        You are the final executive function. Based on the entire OODA loop, generate a concrete, final action plan.

        - Observation (What is): {observation_result}
        - Orientation (What it means): {orientation_result}
        - Decision (What to do about it): {decision_result}

        Synthesize these into a final, actionable summary.
        """
        final_plan = self.orchestrator.run(synthesis_task)
        print(f"Final Plan: {final_plan}")
        
        print("\n=== CONSCIOUSNESS OODA CYCLE COMPLETE ===")

        return {
            "observation": observation_result,
            "orientation": orientation_result,
            "decision": decision_result,
            "final_plan": final_plan,
        }
