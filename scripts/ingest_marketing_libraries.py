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

from api.services.graphiti_service import get_graphiti_service, GraphitiConfig
from api.agents.knowledge_agent import KnowledgeAgent
from api.agents.knowledge.wisdom_tools import ingest_wisdom_insight

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dionysus.ingest_marketing")

LIB_PATHS = [
    {
        "root": "/Volumes/Arkham/Marketing/stefan",
        "name": "Stefan Georgi Library"
    },
    {
        "root": "/Volumes/Arkham/Marketing/Jon Benson - Chat VSL (imarketing.courses)",
        "name": "Jon Benson Chat VSL"
    }
]

# File types to process
EXTENSIONS = [".txt", ".docx", ".rtf", ".md"]

async def process_file(file_path, knowledge_agent):
    """Process an individual marketing file and extract process/strategic insights."""
    logger.info(f"  --- Processing: {os.path.basename(file_path)} ---")
    
    try:
        if file_path.endswith(".docx"):
            import docx2txt
            content = docx2txt.process(file_path)
        else:
            with open(file_path, "r", errors="ignore") as f:
                content = f.read()
            
        if not content.strip():
            return

        # Extract Process Insights (Unique Mechanisms, Roadmaps, etc.)
        logger.info("  Extracting process insights...")
        ingest_wisdom_insight(
            content=content[:10000], # First 10k chars for context
            insight_type="process_insight",
            source=file_path
        )
        
        # Extract Strategic Ideas
        logger.info("  Extracting strategic ideas...")
        ingest_wisdom_insight(
            content=content[:10000],
            insight_type="strategic_idea",
            source=file_path
        )
        
    except Exception as e:
        logger.error(f"  ✗ Error processing {file_path}: {e}")

async def main():
    knowledge_agent = KnowledgeAgent()
    
    # Initialize Graphiti connection
    config = GraphitiConfig(
        neo4j_uri="bolt://127.0.0.1:7687",
        neo4j_password="Mmsm2280",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    for lib in LIB_PATHS:
        root = lib["root"]
        name = lib["name"]
        logger.info(f"Starting ingestion for: {name}")
        
        # Recursive glob search
        files = []
        for ext in EXTENSIONS:
            files.extend(glob.glob(f"{root}/**/*{ext}", recursive=True))
            
        logger.info(f"Found {len(files)} potential files in {name}.")
        
        # Prioritize foundational files based on keywords
        foundational = [f for f in files if any(k in f.lower() for k in ["rmbc", "roadmap", "getting started", "module"])]
        others = [f for f in files if f not in foundational]
        
        # Process foundational first
        for i, f in enumerate(foundational[:20]): # Limit per session to protect context/rate limits
            logger.info(f"[{i+1}/{len(foundational)}] Foundational: {f}")
            await process_file(f, knowledge_agent)
            
    logger.info("Marketing Library Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())
