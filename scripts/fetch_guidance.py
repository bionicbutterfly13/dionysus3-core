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
    
    # For verification/demo purposes without active DB tunnel:
    print("⚠️  Running in Verification Mode (Mocked DB)...")
    from api.services.dream_service import DreamService
    from api.models.hexis_ontology import DriveType
    
    # Instantiate without graphiti (offline mode)
    dream_service = DreamService(graphiti=None)
    
    # Initialize some interesting state for the demo
    dream_service._state.drives[DriveType.REST].level = 0.1
    dream_service._state.blocks["project_context"].value = "Refactoring Auth Service to use JWT."
    dream_service._state.blocks["pending_items"].value = "- [ ] Validate Token Expiry\n- [ ] Update Integration Tests"
    
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
    
    # except Exception as e:
    #     print(f"❌  Failed to fetch guidance: {e}")
    #     sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
