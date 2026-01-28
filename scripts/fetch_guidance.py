"""
Fetch Guidance Script
Feature: 069-hexis-subconscious-integration

Usage: python3 scripts/fetch_guidance.py

Updates `active_context.md` with the latest Subconscious Guidance from the DreamService.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from api.services.dream_service import get_dream_service
from dotenv import load_dotenv

load_dotenv()

GUIDANCE_FILE = ".gemini/active_context.md"

async def main():
    print("🔮  Connecting to Subconscious Stream...")
    
    try:
        dream_service = await get_dream_service()
        
        # In a real scenario, this context summary would come from recent heartbeat logs
        # For now, we fetch the baseline guidance
        guidance = await dream_service.generate_guidance(
            context_summary="User has requested guidance update."
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(GUIDANCE_FILE), exist_ok=True)
        
        with open(GUIDANCE_FILE, "w") as f:
            f.write(guidance)
            
        print(f"✅  Guidance updated in {GUIDANCE_FILE}")
        print("-" * 40)
        print(guidance)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌  Failed to fetch guidance: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
