
import asyncio
import os
import sys
from api.agents.marketing_agent import MarketingAgent

async def generate_advertorials():
    print("🚀 Starting Advertorial Generation with configured LLM...")
    
    agent = MarketingAgent()
    
    # Angle 1: The "Split Self" (Core UMP)
    product = "Inner Architect Blueprint Bundle ($97 Tripwire)"
    positioning = """
    Targeting 'Analytical Empaths' (Doctors, Lawyers, Tech Founders).
    UMP: You're not burned out, you're split.
    Mechanism: Memory Reconsolidation / Identity Prediction System.
    Style: Stefan Georgi RMBC / Georgia System (Story-driven, emotional lead into logical solution).
    Requirement: 5th-grade reading level, no em-dashes, high-status diagnostic tone.
    """
    
    print("\n--- Generating Advertorial Variant 1: The Split Self ---")
    result = await agent.generate_sales_page(product, positioning)
    
    if "copy_text" in result:
        output_path = "/Volumes/Arkham/Marketing/stefan/assets/IAS-advertorial-variant-01.md"
        # We handle the filesystem write via a temporary local file then shell copy if needed, 
        # but the agent can run code to write it. 
        # For now, let's just print the summary and we'll save it.
        print(f"✅ Generated copy. Confidence: {result.get('confidence')}")
        
        # Save locally first
        local_path = "scripts/advertorial_draft_01.md"
        with open(local_path, "w") as f:
            f.write(result["copy_text"])
        print(f"💾 Draft saved to {local_path}")
    else:
        print("❌ Generation failed or queued for review.")
        print(result)

if __name__ == "__main__":
    # Check for required env vars
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: Missing OPENAI_API_KEY")
        sys.exit(1)
        
    asyncio.run(generate_advertorials())
