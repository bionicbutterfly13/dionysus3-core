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

# Local settings (VPS path: /app/data/archives/*.md)
ARCHIVE_PATH = "/Volumes/Asylum/repos/claude-conversation-extractor/Claude Conversations/*.md"
BATCH_SIZE = 5 # Parallel batches for speed
FLEET_MODEL = "openai/gpt-5-nano"

async def process_batch(file_paths, agent_id):
    """Process a batch of conversation files using a specific agent."""
    knowledge_agent = KnowledgeAgent(model_id=FLEET_MODEL)
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
    all_files = sorted(glob.glob(ARCHIVE_PATH))
    total_files = len(all_files)
    
    output_file = "wisdom_extraction_raw.json"
    
    # 1. Load existing results for resumption
    all_results = []
    processed_ids = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                all_results = json.load(f)
                processed_ids = {r.get("session_id") for r in all_results if r.get("session_id")}
            print(f"Resuming: {len(processed_ids)} files already processed.")
        except Exception as e:
            print(f"Warning: Could not load existing results: {e}")

    # 2. Filter remaining files
    remaining_files = [f for f in all_files if os.path.basename(f).replace(".md", "") not in processed_ids]
    print(f"Starting Wisdom Fleet: {len(remaining_files)} remaining of {total_files} total files.")
    
    # Partition files into batches
    batches = [remaining_files[i:i + BATCH_SIZE] for i in range(0, len(remaining_files), BATCH_SIZE)]
    
    # Point the internal sync service to the local tunnel
    os.environ["N8N_WEBHOOK_URL"] = "http://localhost:8000/webhook/memevolve/v1/ingest"
    
    # Process remaining batches sequentially
    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}/{len(batches)} (Remaining)...")
        batch_results = await process_batch(batch, f"agent-{i}")
        
        # Valid results only
        valid_results = [r for r in batch_results if r]
        all_results.extend(valid_results)
        
        # Incremental save to prevent data loss
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
        
    print(f"Wisdom extraction session complete. Total insights now: {len(all_results)}")

if __name__ == "__main__":
    asyncio.run(main())
