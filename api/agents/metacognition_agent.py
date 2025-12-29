from smolagents import ToolCallingAgent, LiteLLMModel, MCPClient
from mcp import StdioServerParameters

class MetacognitionAgent:
    """
    Specialized agent for the DECIDE phase of the OODA loop.
    Reviews goal states, assesses model accuracy, and revises mental models via MCP tools.
    Uses ToolCallingAgent for efficient, parallel self-reflection and goal management.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.server_params = StdioServerParameters(
            command="python3",
            args=["-m", "dionysus_mcp.server"],
            env={**os.environ, "PYTHONPATH": "."}
        )
        self.mcp_client = None
        self.agent = None
        self.name = "metacognition"
        self.description = """
            Specialized in self-reflection, goal management, and mental model revision.
            Uses ToolCallingAgent to evaluate system performance and adjust internal models.
            """

    def __enter__(self):
        from api.agents.audit import get_audit_callback
        self.mcp_client = MCPClient(self.server_params, structured_output=True)
        tools = self.mcp_client.__enter__()
        
        audit = get_audit_callback()
        
        # T1.1: Migrate to ToolCallingAgent
        self.agent = ToolCallingAgent(
            tools=tools,
            model=self.model,
            name=self.name,
            description=self.description,
            max_steps=5,
            max_tool_threads=4, # Enable parallel tool execution (T1.3)
            step_callbacks=audit.get_registry("metacognition")
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mcp_client:
            self.mcp_client.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        self.__exit__(None, None, None)

    def run(self, task: str):
        """Run the metacognition cycle."""
        if not self.agent:
            with self:
                return self.agent.run(task)
        return self.agent.run(task)
