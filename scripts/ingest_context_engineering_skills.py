
import asyncio
import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.services.remote_sync import RemoteSyncService
from api.services.graphiti_service import get_graphiti_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dionysus.ingest_skills")

SKILLS_ROOT = "/Volumes/Asylum/skills/community/context-engineering-skills"

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
    logger.info(f"🚀 Starting ingestion of Context Engineering Skills from {SKILLS_ROOT}")
    
    sync_service = RemoteSyncService()
    graphiti_service = await get_graphiti_service()
    
    skills_dir = Path(SKILLS_ROOT)
    skill_files = list(skills_dir.glob("**/SKILL.md"))
    logger.info(f"Found {len(skill_files)} skill files.")

    for skill_file in skill_files:
        logger.info(f"Processing {skill_file}...")
        skill_data = parse_skill_md(skill_file)
        skill_name = skill_data.get("name") or skill_file.parent.name
        skill_id = skill_name.lower().replace(" ", "-")
        description = skill_data.get("description", "")
        full_content = skill_data.get("content", "")
        
        # 1. Upsert Skill node via RemoteSyncService
        upsert_payload = {
            "skill_id": skill_id,
            "name": skill_name,
            "description": description,
            "proficiency": 0.8,
            "practice_count": 1,
            "last_practiced": datetime.now().isoformat()
        }
        
        res = await sync_service.skill_upsert(upsert_payload)
        logger.info(f"  ✓ Skill node upserted: {skill_id}")

        # 2. Ingest full content into Graphiti
        source_id = f"skills-library:context-engineering:{skill_id}"
        await graphiti_service.ingest_message(
            content=f"# Skill: {skill_name}\n\n{description}\n\n## Core Instructions\n\n{full_content}",
            source_description=source_id,
            group_id="procedural_memory"
        )
        logger.info(f"  ✓ Ingested into Graphiti: {skill_id}")

    logger.info("✅ Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())
