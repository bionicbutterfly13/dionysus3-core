
import asyncio
import os
import sys

# Set VPS IP for webhooks if not already set
os.environ.setdefault("N8N_CYPHER_URL", "http://72.61.78.89:5678/webhook/neo4j/v1/cypher")
os.environ.setdefault("N8N_RECALL_URL", "http://72.61.78.89:5678/webhook/memory/v1/recall")

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

from api.agents.knowledge_agent import KnowledgeAgent

async def test_avatar_ingestion():
    print("Initializing KnowledgeAgent...")
    agent = KnowledgeAgent()
    
    raw_data = """
    Target Audience: Analytical Professionals (Doctors, tech founders, lawyers)
    Ages: 35-55
    Net Worth: $1M - $5M
    
    Psychographics: 'Analytical Empath'. High performers who feel like they are 
    wearing a mask. They have achieved external success but feel internally empty.
    
    Core Pain: The 'Split Self'. Performing a version of themselves for others 
    while their true self remains hidden and exhausted.
    
    Objections:
    - 'Therapy is too slow and doesn't understand my high-pressure world.'
    - 'I've tried retreats and biohacking, but the results don't last.'
    
    Desires: Identity integration. To feel as successful as they look.
    """
    
    print("Starting Avatar Mapping and Ingestion...")
    result = await agent.map_avatar_data(raw_data, source="test_copy_brief")
    
    print("\nResult:")
    print(result)
    
    if result.get("status") == "completed":
        print("\nSUCCESS: Avatar data mapped and ingested.")
    elif result.get("status") == "human_review_queued":
        print("\nINFO: Extraction needs human review (low confidence).")
    else:
        print("\nUNKNOWN STATUS:", result.get("status"))

if __name__ == "__main__":
    # Ensure environment variables are set
    if not os.getenv("NEO4J_PASSWORD") or not os.getenv("OPENAI_API_KEY") or not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: Missing required environment variables (NEO4J_PASSWORD, OPENAI_API_KEY, ANTHROPIC_API_KEY)")
        sys.exit(1)
        
    asyncio.run(test_avatar_ingestion())
