import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from api.services.remote_sync import RemoteSyncService, SyncConfig

async def check_worldview():
    token = os.getenv("MEMORY_WEBHOOK_TOKEN", "")
    vps_ip = "72.61.78.89"
    config = SyncConfig(
        webhook_token=token,
        recall_webhook_url=f"http://{vps_ip}:5678/webhook/memory/v1/recall",
        webhook_url=f"http://{vps_ip}:5678/webhook/memory/v1/ingest/message",
        cypher_webhook_url=f"http://{vps_ip}:5678/webhook/neo4j/v1/cypher"
    )
    
    sync = RemoteSyncService(config=config)
    
    queries = [
        "Split Self",
        "Analytical Empath",
        "MOSAEIC protocol",
        "Genesis Moment",
        "15-Point PDP Blueprint",
        "Macro-to-Micro Funnel"
    ]
    
    print("🔍 Checking Knowledge Graph for Worldview Data Units...\n")
    
    for query in queries:
        print(f"Querying: '{query}'...")
        try:
            results = await sync.search_memories(query, limit=3)
            if results:
                print(f"  ✅ Found {len(results)} matches:")
                for res in results:
                    content = res.get('content', '')[:100]
                    print(f"    - [{res.get('type')}] {content}...")
            else:
                print("  ❌ No direct matches found.")
        except Exception as e:
            print(f"  ⚠️ Search failed: {e}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(check_worldview())
