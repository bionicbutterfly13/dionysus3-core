import os
from smolagents import CodeAgent, LiteLLMModel
from api.agents.tools.reflect_tool import ReflectTool
from api.agents.tools.synthesize_tool import SynthesizeTool

class ReasoningAgent:
    """
    Specialized agent for the ORIENT phase of the OODA loop.
    Analyzes observations, reflects on patterns, and synthesizes insights.
    Uses CodeAgent for deeper reasoning capabilities.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.tools = [
            ReflectTool(),
            SynthesizeTool()
        ]
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            name="reasoning",
            description="Specialized in analysis, reflection, and synthesis of information."
        )

    def run(self, task: str):
        """
        Run the reasoning cycle.
        """
        return self.agent.run(task)
