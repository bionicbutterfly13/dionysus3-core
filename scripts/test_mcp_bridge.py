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
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        return

    model = LiteLLMModel(model_id=model_id, api_key=api_key)
    
    # 2. Setup MCP Server Parameters
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "dionysus_mcp.server"],
        env={**os.environ, **config, "PYTHONPATH": "."} # Set PYTHONPATH
    )

    
    print(f"Connecting to MCP server and bridging tools...")
    
    # 3. Create Agent with Bridged Tools
    try:
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tools:
            print(f"Successfully bridged {len(tools.tools)} tools from MCP.")
            
            agent = CodeAgent(
                tools=[*tools.tools],
                model=model,
                max_steps=3,
                executor_type="local"
            )
            
            # 4. Run Test Task
            prompt = """
            Use the 'semantic_recall' tool to search for 'smolagents'.
            Then, use 'get_energy_status' to check the current state.
            Finally, summarize the results.
            """
            
            print("\nRunning bridged agent task...")
            print("-" * 60)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, agent.run, prompt)
            
            print("-" * 60)
            print("\nFinal Result:")
            print(result)
            print("\n✅ MCP Bridge Test Passed!")
            
    except Exception as e:
        print(f"\n❌ MCP Bridge Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
