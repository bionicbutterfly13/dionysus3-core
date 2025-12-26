import os
import asyncio
from smolagents import CodeAgent, LiteLLMModel, ToolCollection
from mcp import StdioServerParameters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    print("=== Testing smolagents MCP Tool Bridge ===")
    
    # 1. Setup Model
    model_id = os.getenv("OPENAI_MODEL", "openai/gpt-5-nano-2025-08-07")
    model = LiteLLMModel(
        model_id=model_id,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 2. Setup MCP Server Parameters
    # We point to the local dionysus_mcp server
    # FastMCP uses stdio by default when run via python
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "dionysus_mcp.server"],
        env={**os.environ, "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/agi_memory")}
    )
    
    print(f"Connecting to MCP server and bridging tools...")
    
    # 3. Create Agent with Bridged Tools
    try:
        # ToolCollection.from_mcp is a context manager that handles server lifecycle
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tools:
            print(f"Successfully bridged {len(tools.tools)} tools from MCP.")
            
            # Print available tools for verification
            for tool in tools.tools:
                print(f" - [{tool.name}] {tool.description[:60]}...")
            
            agent = CodeAgent(
                tools=[*tools.tools],
                model=model,
                max_steps=5,
                executor_type="local"
            )
            
            # 4. Run Test Task
            prompt = """
            Use the 'semantic_recall' tool to search for 'smolagents integration'.
            If you find anything, summarize it. 
            Then use 'get_energy_status' to check my current state.
            """
            
            print("\nRunning bridged agent task...")
            print("-" * 60)
            
            # Run in executor since Agent.run is sync
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, agent.run, prompt)
            
            print("-" * 60)
            print("\nFinal Result:")
            print(result)
            
    except Exception as e:
        print(f"\nBridge Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
