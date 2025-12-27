
import asyncio
import os
import sys
import json
from api.agents.knowledge.tools import ingest_avatar_insight
from api.agents.knowledge.wisdom_tools import ingest_wisdom_insight

async def ingest_frameworks():
    print("🚀 Ingesting CopyHackers and RMBC Frameworks into Wisdom Graph...")
    
    # 1. CopyHackers Bag of Tricks
    tricks = [
        {"name": "The Open Loop", "description": "Tell people just enough to pique curiosity and leave them itching to close the loop."}, 
        {"name": "The Battlefield Principle", "description": "Drop readers right into the action. Don't waste time or space on topics that make eyes glaze over."}, 
        {"name": "The Superman Principle", "description": "Showcase the prospect moving toward achieving a goal, or revelling in the aftermath."}, 
        {"name": "Future Pacing", "description": "Create a future for your prospects with words. Commit them by getting them to imagine their lives with it."}, 
        {"name": "Loss Aversion", "description": "Focus on the losses of NOT using your solution."}, 
        {"name": "The Even If Technique", "description": "Connect a desirable outcome with the objection/anxiety that keeps people from believing it."}, 
        {"name": "The CPTS Technique", "description": "Color, Pattern, Texture, Shine. Turn non-visual words into visual words."}, 
        {"name": "Urgency", "description": "Plan emails such that they focus on the urgency of taking the offer as the deadline nears."}, 
        {"name": "Scarcity", "description": "Limit offer quantity and help prospects imagine the disappointment of missing out."} 
    ]
    
    for trick in tricks:
        print(f"Ingesting CopyHackers: {trick['name']}...")
        await asyncio.to_thread(ingest_wisdom_insight, 
            content=f"CopyHackers Technique: {trick['name']} - {trick['description']}",
            insight_type="strategic_idea",
            source="CopyHackers Resources"
        )

    # 2. Stefan Georgi RMBC / Georgia System
    rmbc = [
        {"name": "RMBC", "description": "Research, Mechanism, Brief, Copy. The core architecture for high-converting sales pages."}, 
        {"name": "Georgia Advertorial Structure", "description": "Story-driven lead -> Crisis/Agitation -> Expert/Medical Validation -> Unique Mechanism -> Solution -> CTA."}, 
        {"name": "Unique Mechanism of Problem (UMP)", "description": "The specific, non-obvious reason why the customer has been failing (e.g., 'You're not burned out, you're split')."}, 
        {"name": "Unique Mechanism of Solution (UMS)", "description": "The specific, scientific reason why the new solution works (e.g., 'Memory Reconsolidation')."}
    ]
    
    for item in rmbc:
        print(f"Ingesting RMBC: {item['name']}...")
        await asyncio.to_thread(ingest_wisdom_insight,
            content=f"RMBC Concept: {item['name']} - {item['description']}",
            insight_type="process_insight",
            source="Stefan Georgi RMBC II"
        )

    print("\n✅ Framework ingestion complete.")

if __name__ == "__main__":
    if not os.getenv("NEO4J_PASSWORD") or not os.getenv("OPENAI_API_KEY") or not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: Missing environment variables")
        sys.exit(1)
        
    asyncio.run(ingest_frameworks())
