import os
from smolagents import ToolCallingAgent, LiteLLMModel, ToolCollection
from mcp import StdioServerParameters

class PerceptionAgent:
    """
    Specialized agent for the OBSERVE phase of the OODA loop.
    Gathers environmental context and recalls relevant memories via MCP tools.
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
            # Emergency fallback logic
            self.tools = []
            print(f"Warning: PerceptionAgent MCP Bridge failed: {e}")
        
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
