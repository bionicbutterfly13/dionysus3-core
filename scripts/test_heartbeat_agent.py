#!/usr/bin/env python3
"""
Test script for HeartbeatAgent PoC.
"""

import asyncio
import os
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from api.agents.heartbeat_agent import HeartbeatAgent

async def main():
    print("=== Testing HeartbeatAgent PoC ===")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment.")
        return

    # Initialize Agent
    print("Initializing HeartbeatAgent...")
    try:
        agent = HeartbeatAgent()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    # Mock Context
    context = {
        "heartbeat_number": 42,
        "current_energy": 15.0,
        "max_energy": 20.0,
        "user_present": True,
        "time_since_user": "5 minutes",
        "active_goals": [
            {"id": "g1", "title": "Implement smolagents integration", "status": "in_progress"},
            {"id": "g2", "title": "Improve memory recall accuracy", "status": "todo"}
        ],
        "recent_memories": [
            {"content": "User asked to explore smolagents framework.", "type": "chat", "importance": 0.8},
            {"content": "Analyzed architecture and found high synergy with Dionysus.", "type": "reflection", "importance": 0.9}
        ]
    }

    print("\nRunning decision cycle...")
    print("-" * 60)
    
    try:
        decision = await agent.decide(context)
        print("-" * 60)
        print("\nAgent Decision Summary:")
        print(decision)
        print("\n=== Test Complete ===")
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
