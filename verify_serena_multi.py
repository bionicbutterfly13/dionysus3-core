import asyncio
import sys
import json

# Add project root to path
sys.path.append('/Volumes/Asylum/dev/dionysus3-core')

from dionysus_mcp.server import app

async def double_proof():
    print("--- Serena Multi-Tool Verification ---")
    
    # Tool 1: get_energy_status
    print("\n[Tool 1: get_energy_status]")
    res1 = await app.call_tool("get_energy_status", arguments={})
    print(f"Status: {'✅' if 'error' not in str(res1) else '❌'}")
    print(f"Content: {res1[0].text[:200]}...")

    # Tool 2: observe_environment
    print("\n[Tool 2: observe_environment]")
    res2 = await app.call_tool("observe_environment", arguments={})
    print(f"Status: {'✅' if 'error' not in str(res2) else '❌'}")
    print(f"Content: {res2[0].text[:200]}...")

if __name__ == "__main__":
    asyncio.run(double_proof())
