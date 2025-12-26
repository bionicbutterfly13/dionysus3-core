#!/usr/bin/env python3
"""
Test script for the Multi-Agent Consciousness Manager.
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

from api.agents.consciousness_manager import ConsciousnessManager

async def main():
    print("=== Testing Multi-Agent Consciousness Manager ===")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment.")
        return

    # Initialize Consciousness Manager
    print("Initializing ConsciousnessManager and sub-agents...")
    try:
        manager = ConsciousnessManager()
    except Exception as e:
        print(f"Failed to initialize manager or sub-agents: {e}")
        return

    # Mock Initial Context
    initial_context = {
        "heartbeat_number": 43,
        "current_energy": 18.0,
        "max_energy": 20.0,
        "user_present": True,
        "time_since_user": "15 minutes",
        "primary_goal": {
            "id": "g1", 
            "title": "Implement smolagents integration", 
            "status": "in_progress",
            "description": "Integrate smolagents framework into Dionysus core for code-first agency."
        },
        "recent_activity_summary": "User recently reviewed the smolagents integration plan and asked for next steps on multi-agent architecture."
    }

    print("\nRunning OODA cycle (this will take a moment, involves multiple LLM calls)...")
    print("-" * 80)
    
    try:
        full_cycle_result = await asyncio.to_thread(manager.run_ooda_cycle, initial_context)
        # Note: manager.run_ooda_cycle internally calls agent.run which is sync,
        # so we run it in a separate thread using asyncio.to_thread to avoid blocking.
        
        print("-" * 80)
        print("\nFull OODA Cycle Result:")
        print(json.dumps(full_cycle_result, indent=2))
        print("\n=== Multi-Agent Test Complete ===")
    except Exception as e:
        print(f"\nError during OODA cycle execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
