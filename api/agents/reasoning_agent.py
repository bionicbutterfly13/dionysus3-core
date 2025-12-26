import os
from smolagents import CodeAgent, LiteLLMModel, ToolCollection
from mcp import StdioServerParameters

class ReasoningAgent:
    """
    Specialized agent for the ORIENT phase of the OODA loop.
    Analyzes observations, reflects on patterns, and synthesizes insights via MCP tools.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
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
            print(f"Warning: ReasoningAgent MCP Bridge failed: {e}")
        
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
