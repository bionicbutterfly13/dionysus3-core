import pytest
from smolagents import CodeAgent, LiteLLMModel, MCPClient
from mcp import StdioServerParameters
import os


# Skip in unit tests - requires MCP server process
@pytest.mark.skip(reason="Integration test - requires MCP server running")
def test_mcp_client_usage():
    """Verify that MCPClient works as expected."""
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "dionysus_mcp.server"],
        env={**os.environ, "PYTHONPATH": "."}
    )
    
    model = LiteLLMModel(model_id="openai/gpt-5-nano")
    
    with MCPClient(server_params) as tools:
        assert len(tools) > 0
        agent = CodeAgent(tools=tools, model=model)
        assert agent.tools is not None
