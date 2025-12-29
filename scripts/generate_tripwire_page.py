"""
Script to regenerate the $97 Tripwire Sales Page with Social Proof.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.agents.marketing_agent import MarketingAgent
from api.services.llm_service import GPT5_NANO

async def main():
    print("=== Regenerating $97 Tripwire Sales Page ===")
    
    agent = MarketingAgent()
    
    # Context for the page
    product = "Inner Architect Blueprint System"
    positioning = "A 3-layer AI-backed diagnostic system to rebuild your internal architecture, silence rumination, and integrate your 'Split Self' for sustainable high-performance."
    
    prompt = f"""
    Write a high-converting sales page for the {product}.
    
    POSITIONING: {positioning}
    PRICE: $97 (Tripwire)
    
    STRUCTURE:
    1. HERO: Big Idea headline + Subhead (Architecture/Engineering frame).
    2. THE PROBLEM: Name the 'Split Self' and 'Replay Loop' (SSAR cycle). VISCERAL pain for CEOs/Surgeons.
    3. THE SOLUTION: The 3-layer IAS Suite (Inner OS, Identity Integration, External Ecosystem).
    4. THE MECHANISM: Predictive Identity Recalibration.
    5. THE SOCIAL PROOF: Integrate these specific stories:
       - Dr. Danielle: Physician who integrated her 'iron suit' with her core self.
       - Bryan Rounds: 15-year regret loop broken; inner genius freed.
       - Cynthia Odogwu, MD: Accessed inner landscape; shift in how she shows up.
       - Janier Barton, DDS: Overcame the replay loop.
    6. THE VALUE STACK: 3-layer AI Suite + Blueprint + Diagnostic ($2,000+ total value).
    7. THE GUARANTEE: Risk reversal (Full refund).
    8. THE CLOSE: Two options close.
    9. THE BRIDGE: Invitation to $3,975 Small Group Coaching on the TY page.
    
    STYLE RULES:
    - 5th grade reading level.
    - NO em dashes.
    - Architecture/System vocabulary.
    - Sentence case subject lines (for emails) - not applicable here but keep tone consistent.
    
    Respond ONLY with a JSON object containing 'copy_text', 'confidence', and 'reasoning'.
    """
    
    # We use the agent directly
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, agent.agent.run, prompt)
    
    try:
        cleaned = str(result).strip()
        if "```json" in cleaned: cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        data = json.loads(cleaned)
        
        output_path = "data/ground-truth/97-tripwire-sales-page.md"
        with open(output_path, "w") as f:
            f.write(data['copy_text'])
            
        print(f"✓ Sales page regenerated and saved to {output_path}")
        print(f"Confidence: {data['confidence']}")
    except Exception as e:
        print(f"Error parsing result: {e}")
        print(f"Raw result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
