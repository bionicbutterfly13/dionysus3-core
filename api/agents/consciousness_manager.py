import os
import json
from typing import Any, Dict

from smolagents import CodeAgent, LiteLLMModel
from api.agents.perception_agent import PerceptionAgent
from api.agents.reasoning_agent import ReasoningAgent
from api.agents.metacognition_agent import MetacognitionAgent

class ConsciousnessManager:
    """
    Orchestrates specialized cognitive agents (Perception, Reasoning, Metacognition)
    using smolagents hierarchical managed_agents architecture.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        """
        Initialize the Consciousness Manager and its managed sub-agents.
        """
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Instantiate sub-agents (these are ToolCallingAgent or CodeAgent internally)
        self.perception = PerceptionAgent().agent
        self.reasoning = ReasoningAgent().agent
        self.metacognition = MetacognitionAgent().agent

        # The orchestrator agent manages the specialized agents
        self.orchestrator = CodeAgent(
            tools=[],
            model=self.model,
            managed_agents=[self.perception, self.reasoning, self.metacognition],
            name="consciousness_manager",
            description="High-level cognitive orchestrator. Use 'perception' to gather data, 'reasoning' to analyze, and 'metacognition' to decide on strategy."
        )

    async def run_ooda_cycle(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a full OODA loop via the managed agent hierarchy.
        """
        print("=== CONSCIOUSNESS OODA CYCLE START (MANAGED AGENTS) ===")
        
        prompt = f"""
        Execute a full OODA (Observe-Orient-Decide-Act) cycle based on the current context.
        
        Initial Context:
        {json.dumps(initial_context, indent=2)}
        
        Your Goal:
        1. Delegate to 'perception' to gather current state and relevant memories.
        2. Delegate to 'reasoning' to analyze the perception results and initial context.
        3. Delegate to 'metacognition' to review goals and decide on strategic updates.
        4. Synthesize everything into a final actionable plan.
        """
        
        import asyncio
        loop = asyncio.get_event_loop()
        # CodeAgent.run is sync
        result = await loop.run_in_executor(None, self.orchestrator.run, prompt)
        
        print("\n=== CONSCIOUSNESS OODA CYCLE COMPLETE ===")

        return {
            "final_plan": str(result),
            "orchestrator_log": self.orchestrator.logs
        }
