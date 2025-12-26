import os
from smolagents import ToolCallingAgent, LiteLLMModel
from api.agents.tools.observe_tool import ObserveTool
from api.agents.tools.recall_tool import RecallTool

class PerceptionAgent:
    """
    Specialized agent for the OBSERVE phase of the OODA loop.
    Gathers environmental context and recalls relevant memories.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.tools = [
            ObserveTool(),
            RecallTool()
        ]
        
        self.agent = ToolCallingAgent(
            tools=self.tools,
            model=self.model,
            name="perception",
            description="Specialized in environmental observation and memory retrieval."
        )

    def run(self, task: str):
        """
        Run the perception cycle.
        """
        return self.agent.run(task)
