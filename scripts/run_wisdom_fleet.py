import asyncio
import os
import glob
import json
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.coordination_service import get_coordination_service
from api.agents.knowledge_agent import KnowledgeAgent

logger = logging.getLogger("dionysus.wisdom_fleet")

ARCHIVE_PATH = "/Volumes/Asylum/repos/claude-conversation-extractor/Claude Conversations/*.md"
BATCH_SIZE = 2 # Tiny batch for maximum stability

async def process_batch(file_paths, agent_id):
    """Process a batch of conversation files using a specific agent."""
    knowledge_agent = KnowledgeAgent()
    results = []
    
    for path in file_paths:
        try:
            with open(path, "r") as f:
                content = f.read()
            
            session_id = os.path.basename(path).replace(".md", "")
            print(f"Agent {agent_id} processing: {session_id}")
            
            insight = await knowledge_agent.extract_wisdom_from_archive(content, session_id)
            results.append(insight)
        except Exception as e:
            print(f"Error processing {path}: {e}")
            
    return results

async def main():
    coord_svc = get_coordination_service()
    all_files = glob.glob(ARCHIVE_PATH)
    total_files = len(all_files)
    
    print(f"Starting Wisdom Fleet: {total_files} files found.")
    
    # Partition files into batches
    batches = [all_files[i:i + BATCH_SIZE] for i in range(0, total_files, BATCH_SIZE)]
    
    all_results = []
    # Process ALL batches sequentially to save memory
    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}/{len(batches)}...")
        batch_results = await process_batch(batch, f"agent-{i}")
        all_results.extend(batch_results)
        
        # Incremental save to prevent data loss
        with open("wisdom_extraction_raw.json", "w") as f:
            json.dump(all_results, f, indent=2)
        
    # Save results for consolidation
    with open("wisdom_extraction_raw.json", "w") as f:
        json.dump(all_results, f, indent=2)
        
    print(f"Initial wisdom extraction complete. {len(all_results)} insights saved.")

if __name__ == "__main__":
    asyncio.run(main())
