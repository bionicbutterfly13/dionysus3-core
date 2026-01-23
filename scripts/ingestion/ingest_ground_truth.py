"""
Persistent background script to ingest 'Ground Truth' strategy files.
This script runs as a persistent process to avoid CLI timeouts.
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.agents.knowledge_agent import KnowledgeAgent
from api.services.llm_service import GPT5_NANO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/Users/manisaintvictor/.gemini/tmp/ground_truth_master.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ground_truth_ingest")

GROUND_TRUTH_DIR = "/home/mani/dionysus-api/data/ground-truth/"
LOG_DIR = "/Users/manisaintvictor/.gemini/tmp/ground_truth_logs"

FILES = [
    "analytical-empath-avatar-source-of-truth.md",
    "97-product-architecture.md",
    "be-funnel-analysis.md",
    "ias-landing-page-be-protocol.md",
    "propaganda-machine-6-beliefs.md"
]

async def read_vps_file(filename):
    import subprocess
    cmd = f"ssh -i /Users/manisaintvictor/.ssh/mani_vps mani@72.61.78.89 'cat {GROUND_TRUTH_DIR}{filename}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    return None

async def process_file(agent, filename):
    log_path = Path(LOG_DIR) / f"{filename}.log"
    
    # Skip if already marked complete in log
    if log_path.exists():
        with open(log_path, "r") as f:
            if "--- Ingestion Complete ---" in f.read():
                logger.info(f"Skipping {filename} - already complete.")
                return

    logger.info(f"Processing: {filename}")
    content = await read_vps_file(filename)
    if not content:
        logger.error(f"Failed to read {filename}")
        return

    with open(log_path, "w") as f_log:
        f_log.write(f"--- Ingestion Start: {filename} ---\\n")
        f_log.flush()
        
        try:
            # Map avatar data - this takes a long time
            result = await agent.map_avatar_data(
                raw_data=content,
                source=f"ground_truth:{filename}",
                project_id="ias-knowledge-base"
            )
            
            f_log.write(f"Status: {result['status']}\\n")
            f_log.write(f"Summary: {result['summary']}\\n")
            f_log.write("--- Ingestion Complete ---\\n")
            logger.info(f"Completed: {filename}")
        except Exception as e:
            logger.error(f"Error in {filename}: {e}")
            f_log.write(f"ERROR: {str(e)}\\n")

async def main():
    logger.info("=== Ground Truth Ingestion Daemon Start ===")
    os.makedirs(LOG_DIR, exist_ok=True)
    
    agent = KnowledgeAgent(model_id=GPT5_NANO)
    
    for filename in FILES:
        await process_file(agent, filename)
        
    logger.info("=== All Ground Truth Tasks Processed ===")

if __name__ == "__main__":
    asyncio.run(main())