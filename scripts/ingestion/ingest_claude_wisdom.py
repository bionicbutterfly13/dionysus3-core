
import asyncio
import os
import sys
from api.agents.knowledge_agent import KnowledgeAgent

# Ensure we can find the archives
ARCHIVE_DIR = "/Volumes/Asylum/repos/claude-conversation-extractor/Claude Conversations/"

async def ingest_wisdom():
    print("🚀 Starting Wisdom Extraction from Claude Archives...")
    
    if not os.path.exists(ARCHIVE_DIR):
        print(f"Error: Archive directory not found at {ARCHIVE_DIR}")
        return

    agent = KnowledgeAgent()
    
    # Get last 20 conversations for the first pass
    files = sorted([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".md")], reverse=True)[:20]
    
    print(f"Found {len(files)} recent conversations to process.")

    for filename in files:
        file_path = os.path.join(ARCHIVE_DIR, filename)
        print(f"\n--- Processing: {filename} ---")
        
        try:
            with open(file_path, "r") as f:
                content = f.read()
            
            # The "Conceptual Pivot" instructions
            instructions = f"""
            You are analyzing an ARCHIVED conversation from Claude to extract wisdom for the CURRENT Dionysus/IAS model.
            
            CONTEXT FOR EXTRACTION:
            - TRUE MODEL: The Analytical Empath (Doctor, tech founder, lawyer) who feels a 'Split Self'.
            - CURRENT OFFER: $97 Blueprint Bundle tripwire (selling the MAP/DIAGNOSTIC).
            - GOAL: Extract 'lost richness', deep pain points, and specific 'voice' phrases that are still relevant.
            
            IMPORTANT: 
            - Discard old offer names or outdated avatar definitions if they contradict the 'Analytical Empath' profile.
            - Focus on finding the 'lost work'—specific descriptions of pain or desired outcomes that make the model richer.
            - Use your sub-agents (Pain, Objection, Voice) to map these into the knowledge graph.
            - Use the 'mosaeic_capture' tool to record any deep experiential states (Senses, Actions, Emotions, Impulses, Cognitions) found in the text.
            """
            
            # We use the agent's multi-agent mapping logic
            result = await agent.map_avatar_data(
                raw_data=f"{instructions}\n\nARCHIVE CONTENT:\n{content[:8000]}", 
                source=f"claude_archive_{filename}"
            )
            
            print(f"Result for {filename}: {result.get('status', 'completed')}")
            if result.get("summary"):
                print(f"Summary: {result['summary'][:200]}...")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("\n✅ Wisdom extraction pass complete.")

if __name__ == "__main__":
    # Check for required env vars
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("NEO4J_PASSWORD"):
        print("Error: Missing OPENAI_API_KEY or NEO4J_PASSWORD")
        sys.exit(1)
        
    asyncio.run(ingest_wisdom())
