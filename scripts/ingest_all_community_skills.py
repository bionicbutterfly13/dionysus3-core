
import asyncio
import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.remote_sync import RemoteSyncService
from api.services.graphiti_service import get_graphiti_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dionysus.ingest_all_skills")

COMMUNITY_ROOT = "/Volumes/Asylum/skills/community"
PROGRESS_FILE = "scripts/ingestion_progress.txt"
SLEEP_INTERVAL = 2  # Seconds between skills to avoid overwhelming

def parse_skill_md(file_path: Path) -> Dict[str, Any]:
    """Parse SKILL.md with YAML frontmatter."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    return {**frontmatter, "content": body}
                except Exception as e:
                    logger.error(f"Error parsing YAML in {file_path}: {e}")
        
        return {"content": content}
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return {"content": ""}

async def main():
    logger.info(f"🚀 Starting ingestion of ALL Community Skills from {COMMUNITY_ROOT}")
    
    # 1. Check environment
    if not os.getenv("NEO4J_PASSWORD"):
        logger.error("NEO4J_PASSWORD not set.")
        return

    # 2. Initialize Services
    sync_service = RemoteSyncService()
    graphiti_service = await get_graphiti_service()
    
    community_dir = Path(COMMUNITY_ROOT)
    if not community_dir.exists():
        logger.error(f"Community directory not found: {COMMUNITY_ROOT}")
        return

    # Load progress
    processed = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            processed = {line.strip() for line in f if line.strip()}

    # 3. Find all SKILL.md files recursively
    # Note: some categories might have nested skills or just one SKILL.md at the top
    skill_files = list(community_dir.glob("**/SKILL.md"))
    logger.info(f"Found {len(skill_files)} skill files.")

    # Track successes
    stats = {"skill_nodes": 0, "graphiti_episodes": 0, "errors": 0, "skipped": 0, "processed_this_run": 0}
    MAX_PER_RUN = 15

    for skill_file in skill_files:
        if stats["processed_this_run"] >= MAX_PER_RUN:
            logger.info(f"Reached MAX_PER_RUN ({MAX_PER_RUN}). Stopping for now.")
            break

        if str(skill_file) in processed:
            stats["skipped"] += 1
            continue

        # ... (rest of the loop)
        # Record progress
        with open(PROGRESS_FILE, "a") as f:
            f.write(f"{skill_file}\n")
        
        stats["processed_this_run"] += 1
        await asyncio.sleep(SLEEP_INTERVAL)

    logger.info(f"✅ Batch Complete. Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
