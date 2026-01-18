import asyncio
import sys
import os

# Add project root to path
sys.path.append('/Volumes/Asylum/dev/dionysus3-core')

async def main():
    print("🔮 Connecting to Dionysus Core...")
    try:
        from dionysus_mcp.server import semantic_recall
        # Also import other useful tools to prove breadth
        from dionysus_mcp.server import get_heartbeat_status
        
        print("🧠 Querying Memory: 'Memory Systems Integration'...")
        
        # Call the tool directly (assuming decorator keeps it callable)
        # If FastMCP wraps it, we might need semantic_recall.fn or similar
        # But usually they are callable.
        
        result = await semantic_recall(
            query="Memory Systems Integration plan", 
            top_k=3,
            threshold=0.5
        )
        
        print("\n--- RECALL RESULT ---")
        print(result)
        print("---------------------\n")
        
        print("💓 Checking Heartbeat Status...")
        hb_status = await get_heartbeat_status()
        print(hb_status)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
    except TypeError as e:
        print(f"❌ Type Error (Invocation): {e}")
    except Exception as e:
        print(f"❌ Execution Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
