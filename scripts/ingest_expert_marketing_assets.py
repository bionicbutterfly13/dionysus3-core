import asyncio
import os
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.graphiti_service import get_graphiti_service, GraphitiConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dionysus.ingest_assets")

ASSETS_TO_INGEST = [
    {
        "path": "/Volumes/Asylum/dev/email-sequence/1. Macro to Micro.txt",
        "description": "Dr. Mani's Macro-to-Micro Funnel Script and Strategic Stance"
    },
    {
        "path": "/Volumes/Asylum/dev/email-sequence/Deep Research Brief_ Advertorial Best Practices fo.md",
        "description": "Evidence-Based Advertorial Guidelines for Analytical Empaths"
    },
    {
        "path": "/Volumes/Asylum/dev/email-sequence/analytical-empath-hooks.md",
        "description": "Master Hook Database for Analytical Empaths"
    }
]

async def main():
    # Initialize Graphiti service
    config = GraphitiConfig(
        neo4j_uri="bolt://127.0.0.1:7687",
        neo4j_password="Mmsm2280",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    graphiti_svc = await get_graphiti_service(config)

    for asset in ASSETS_TO_INGEST:
        path = asset["path"]
        desc = asset["description"]
        
        if not os.path.exists(path):
            logger.warning(f"Asset not found: {path}")
            continue
            
        logger.info(f"Ingesting asset: {desc} ({path})")
        
        try:
            with open(path, "r") as f:
                content = f.read()
            
            # Use a specialized prompt for these high-value assets if needed, 
            # but standard ingest_message works well for general knowledge mapping.
            result = await graphiti_svc.ingest_message(
                content=content,
                source_description=f"expert_asset_{os.path.basename(path)}",
                group_id="marketing-framework"
            )
            logger.info(f"  ✓ Created episode {result.get('episode_uuid')}")
            logger.info(f"  Nodes: {len(result.get('nodes', []))}, Edges: {len(result.get('edges', []))}")
            
        except Exception as e:
            logger.error(f"  ✗ Failed to ingest {path}: {e}")

    await graphiti_svc.close()
    logger.info("Expert Asset Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())
