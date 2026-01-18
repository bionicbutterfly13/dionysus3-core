import asyncio
import sys
import os

# Add project root to path
sys.path.append('/Volumes/Asylum/dev/dionysus3-core')

try:
    from dionysus_mcp.server import app
    print("✅ Successfully imported 'app' from dionysus_mcp.server")
except ImportError as e:
    print(f"❌ Failed to import server: {e}")
    sys.exit(1)

async def run_proof():
    print("\n--- 1. Inspecting Registered Tools ---")
    tools = await app.list_tools()  # FastMCP method to get tool definitions
    if tools:
        print(f"✅ Found {len(tools)} tools registered.")
        for t in tools[:5]: # List first 5
            print(f"   - {t.name}")
        if len(tools) > 5: print("   ... and more")
    else:
        print("❌ No tools found registered on the app!")

    print(f"   App attributes: {[d for d in dir(app) if not d.startswith('__')]}")
    
    try:
        # Try public call_tool method if exists
        if hasattr(app, 'call_tool'):
            print("   Invoking via app.call_tool()...")
            # call_tool might return a CallToolResult which needs parsing
            result = await app.call_tool("get_energy_status", arguments={})
            print(f"✅ Result: {result}")
        else:
            # Fallback: look for the function in the decorated registry
            # FastMCP often stores them in _function_registry or similar
            pass

    except Exception as e:
        print(f"❌ Error invoking tool: {e}")

if __name__ == "__main__":
    asyncio.run(run_proof())
