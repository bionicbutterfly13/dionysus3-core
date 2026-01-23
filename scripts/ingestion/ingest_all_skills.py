
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

SKILLS_LIBRARY_ROOT = "/Volumes/Asylum/skills_library"
PROGRESS_FILE = "scripts/skills_library_ingestion_progress.txt"
SLEEP_INTERVAL = 1  # Seconds between skills to avoid overwhelming

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
    logger.info(f"🚀 Starting ingestion of ALL Skills from {SKILLS_LIBRARY_ROOT}")
    
    # 1. Check environment
    if not os.getenv("NEO4J_PASSWORD"):
        logger.error("NEO4J_PASSWORD not set.")
        return

    # 2. Initialize Services
    sync_service = RemoteSyncService()
    graphiti_service = await get_graphiti_service()
    
    library_dir = Path(SKILLS_LIBRARY_ROOT)
    if not library_dir.exists():
        logger.error(f"Skills library directory not found: {SKILLS_LIBRARY_ROOT}")
        return

    # Load progress
    processed = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            processed = {line.strip() for line in f if line.strip()}

    # 3. Find all SKILL.md files recursively
    skill_files = list(library_dir.glob("**/SKILL.md"))
    logger.info(f"Found {len(skill_files)} skill files.")

    # Track successes
    stats = {"skill_nodes": 0, "graphiti_episodes": 0, "errors": 0, "skipped": 0, "processed_this_run": 0}
    MAX_PER_RUN = 30 # Increased batch size

    for skill_file in skill_files:
        if stats["processed_this_run"] >= MAX_PER_RUN:
            logger.info(f"Reached MAX_PER_RUN ({MAX_PER_RUN}). Stopping for now.")
            break

        if str(skill_file) in processed:
            stats["skipped"] += 1
            continue

        # Get category name from path relative to root
        rel_path = skill_file.parent.relative_to(library_dir)
        category = str(rel_path).replace("/", ":")
        
        logger.info(f"Processing [{category}] {skill_file}...")
        
        skill_data = parse_skill_md(skill_file)
        skill_name = skill_data.get("name")
        
        if not skill_name:
            # Fallback to category/dir name
            skill_name = str(rel_path).replace("/", "-")
        
        # Use a more descriptive skill_id including category to avoid collisions
        skill_id = f"{category.replace(':', '-')}-{skill_name.lower().replace(' ', '-')}"
        description = skill_data.get("description", "")
        full_content = skill_data.get("content", "")
        
        # 1. Upsert Skill node via RemoteSyncService (webhook/n8n)
        logger.info(f"  Upserting Skill node: {skill_id}")
        upsert_payload = {
            "skill_id": skill_id,
            "name": skill_name,
            "description": description[:1000], 
            "proficiency": 0.7,
            "practice_count": 1,
            "last_practiced": datetime.now().isoformat()
        }
        
        try:
            res = await sync_service.skill_upsert(upsert_payload)
            if res.get("success", True):
                stats["skill_nodes"] += 1
            else:
                logger.error(f"  ✗ Failed to upsert skill {skill_id}: {res.get('error')}")
                # We count this as error but don't record progress so we retry
                stats["errors"] += 1
                continue
        except Exception as e:
            logger.error(f"  ✗ Exception upserting skill {skill_id}: {e}")
            stats["errors"] += 1
            continue

        # 2. Ingest full content into Graphiti
        try:
            source_id = f"skills-library:{category}:{skill_id}"
            
            # Find auxiliary files in the same directory
            aux_files = []
            for p in skill_file.parent.glob("**/*"):
                if p.is_file() and p.name != "SKILL.md":
                    aux_files.append(str(p.relative_to(skill_file.parent)))
            
            meta_content = ""
            if aux_files:
                meta_content = "\n\n### Related Artifacts\n- " + "\n- ".join(aux_files)

            graph_res = await graphiti_service.ingest_message(
                content=f"# Skill: {skill_name}\nCategory: {category}\n\n{description}\n\n## Content\n\n{full_content}{meta_content}",
                source_description=source_id,
                group_id="procedural_memory"
            )
            stats["graphiti_episodes"] += 1
            logger.info(f"  ✓ Ingested into Graphiti: {len(graph_res.get('nodes', []))} nodes.")
            
            # Record progress ONLY if both succeeded
            with open(PROGRESS_FILE, "a") as f:
                f.write(f"{skill_file}\n")
            
            stats["processed_this_run"] += 1
            await asyncio.sleep(SLEEP_INTERVAL)

        except Exception as e:
            logger.error(f"  ✗ Exception ingesting into Graphiti for {skill_id}: {e}")
            stats["errors"] += 1

    logger.info(f"✅ Batch Complete. Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
