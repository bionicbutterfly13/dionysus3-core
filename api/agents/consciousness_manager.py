import os
import json
from typing import Any, Dict

from smolagents import CodeAgent, LiteLLMModel
from api.agents.perception_agent import PerceptionAgent
from api.agents.reasoning_agent import ReasoningAgent
from api.agents.metacognition_agent import MetacognitionAgent
from api.services.bootstrap_recall_service import BootstrapRecallService
from api.models.bootstrap import BootstrapConfig

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
        
        # Instantiate bootstrap recall service
        self.bootstrap_svc = BootstrapRecallService()
        
        # Instantiate sub-agents (these are ToolCallingAgent or CodeAgent internally)
        self.perception_agent_wrapper = PerceptionAgent()
        self.reasoning_agent_wrapper = ReasoningAgent()
        self.metacognition_agent_wrapper = MetacognitionAgent()
        
        self.perception = self.perception_agent_wrapper.agent
        self.reasoning = self.reasoning_agent_wrapper.agent
        self.metacognition = self.metacognition_agent_wrapper.agent

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
        
        # T012: Bootstrap Recall Integration
        project_id = initial_context.get("project_id", "default")
        task_query = initial_context.get("task", "")
        
        # Check if bootstrap is requested or allowed
        if initial_context.get("bootstrap_recall", True):
            config = BootstrapConfig(
                project_id=project_id,
                enabled=True,
                include_trajectories=True
            )
            
            # Perform recall
            bootstrap_result = await self.bootstrap_svc.recall_context(
                query=task_query,
                project_id=project_id,
                config=config
            )
            
            # Inject into context
            initial_context["bootstrap_past_context"] = bootstrap_result.formatted_context
            print(f"DEBUG: Bootstrap Recall injected {bootstrap_result.source_count} sources (summarized={bootstrap_result.summarized})")

        prompt = f"""
        Execute a full OODA (Observe-Orient-Decide-Act) cycle based on the current context.
        
        Initial Context:
        {json.dumps(initial_context, indent=2)}
        
        Your Goal:
        1. Delegate to 'perception' to gather current state and relevant memories. 
           NOTE: Check 'bootstrap_past_context' in initial_context for automatic grounding.
        2. Delegate to 'reasoning' to analyze the perception results and initial context.
        3. Delegate to 'metacognition' to review goals and decide on strategic updates.
        4. Synthesize everything into a final actionable plan.

        OUTPUT FORMAT:
        You MUST respond with a JSON object in this exact format:
        {{
            "reasoning": "Your summary of the situation and strategic plan",
            "actions": [
                {{"action": "recall", "params": {{"query": "..."}} }},
                {{"action": "reflect", "params": {{"topic": "..."}} }}
            ],
            "confidence": 0.9
        }}
        """
        
        import asyncio
        loop = asyncio.get_event_loop()
        # CodeAgent.run is sync
        raw_result = await loop.run_in_executor(None, self.orchestrator.run, prompt)
        
        # Try to parse JSON result
        try:
            cleaned = str(raw_result).strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            structured_result = json.loads(cleaned)
        except Exception as e:
            print(f"ERROR: ConsciousnessManager failed to parse structured actions: {e}")
            structured_result = {
                "reasoning": str(raw_result),
                "actions": [],
                "confidence": 0.5,
                "error": str(e)
            }
        
        print("\n=== CONSCIOUSNESS OODA CYCLE COMPLETE ===")

        return {
            "final_plan": structured_result.get("reasoning", str(raw_result)),
            "actions": structured_result.get("actions", []),
            "confidence": structured_result.get("confidence", 0.5),
            "orchestrator_log": self.orchestrator.memory.steps
        }

    def close(self):
        """Cascade close to all managed sub-agents."""
        for agent_wrapper in [self.perception_agent_wrapper, self.reasoning_agent_wrapper, self.metacognition_agent_wrapper]:
            if hasattr(agent_wrapper, 'close'):
                agent_wrapper.close()
