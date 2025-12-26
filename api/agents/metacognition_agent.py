import os
from smolagents import CodeAgent, LiteLLMModel, ToolCollection
from mcp import StdioServerParameters

class MetacognitionAgent:
    """
    Specialized agent for the DECIDE phase of the OODA loop.
    Reviews goal states, assesses model accuracy, and revises mental models via MCP tools.
    """

    def __init__(self, model_id: str = "openai/gpt-4o-mini"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Bridge tools from local MCP server
        server_params = StdioServerParameters(
            command="python3",
            args=["-m", "dionysus_mcp.server"],
            env={**os.environ, "PYTHONPATH": "."}
        )
        
        try:
            self.tool_collection = ToolCollection.from_mcp(server_params, trust_remote_code=True)
            self.tools = [*self.tool_collection.tools]
        except Exception as e:
            self.tools = []
            print(f"Warning: MetacognitionAgent MCP Bridge failed: {e}")
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            name="metacognition",
            description="Specialized in self-reflection, goal management, and mental model revision."
        )

    def run(self, task: str):
        """
        Run the metacognition cycle.
        """
        return self.agent.run(task)
