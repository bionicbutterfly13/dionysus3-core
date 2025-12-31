import os
from smolagents import ToolCallingAgent, MCPClient
from mcp import StdioServerParameters

class ReasoningAgent:
    """
    Specialized agent for the ORIENT phase of the OODA loop.
    Analyzes observations, reflects on patterns, and synthesizes insights via MCP tools.
    Uses ToolCallingAgent for efficient, parallel analysis and reflection.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        from api.services.llm_service import get_router_model
        self.model = get_router_model(model_id=model_id)
        self.server_params = StdioServerParameters(
            command="python3",
            args=["-m", "dionysus_mcp.server"],
            env={**os.environ, "PYTHONPATH": "."}
        )
        self.mcp_client = None
        self.agent = None
        self.name = "reasoning"
        self.description = """
            Specialized in analysis, reflection, and synthesis of information.
            Uses ToolCallingAgent to perform parallel reasoning over observations.
            """

    def __enter__(self):
        from api.agents.audit import get_audit_callback
        self.mcp_client = MCPClient(self.server_params, structured_output=True)
        tools = self.mcp_client.__enter__()
        
        audit = get_audit_callback()
        
        # T1.1: Migrate to ToolCallingAgent
        # T039-002: Enable planning_interval for OODA agents
        self.agent = ToolCallingAgent(
            tools=tools,
            model=self.model,
            name=self.name,
            description=self.description,
            max_steps=5,
            planning_interval=2,  # Re-plan every 2 steps (FR-039-002)
            max_tool_threads=4,  # Enable parallel tool execution (T1.3)
            step_callbacks=audit.get_registry("reasoning")
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mcp_client:
            self.mcp_client.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        self.__exit__(None, None, None)

    def run(self, task: str):
        """Run the reasoning cycle."""
        if not self.agent:
            with self:
                return self.agent.run(task)
        return self.agent.run(task)
