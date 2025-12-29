"""
Script to ingest 'Ground Truth' strategy files in background.
Feature: 018-ias-knowledge-base
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.agents.knowledge_agent import KnowledgeAgent
from api.services.llm_service import GPT5_NANO

GROUND_TRUTH_DIR = "/home/mani/dionysus-api/data/ground-truth/"

FILES = [
    "analytical-empath-avatar-source-of-truth.md",
    "97-product-architecture.md",
    "be-funnel-analysis.md",
    "ias-landing-page-be-protocol.md",
    "propaganda-machine-6-beliefs.md"
]

LOG_DIR = "/Users/manisaintvictor/.gemini/tmp/ground_truth_logs"

async def ingest_file(agent, filename):
    log_file = os.path.join(LOG_DIR, f"{filename}.log")
    print(f"Starting background ingestion for: {filename} (Log: {log_file})")
    
    # We read the file once
    local_path = Path("data/ground-truth") / filename
    if local_path.exists():
        with open(local_path, "r") as f:
            content = f.read()
    else:
        import subprocess
        cmd = f"ssh -i /Users/manisaintvictor/.ssh/mani_vps mani@72.61.78.89 'cat {GROUND_TRUTH_DIR}{filename}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            content = result.stdout
        else:
            print(f"Error reading {filename} from VPS")
            return

    try:
        with open(log_file, "w") as f_log:
            f_log.write(f"--- Ingestion Start: {filename} ---\n")
            f_log.flush()
            
            # Map avatar data
            result = await agent.map_avatar_data(
                raw_data=content,
                source=f"ground_truth:{filename}",
                project_id="ias-knowledge-base"
            )
            
            f_log.write(f"Status: {result['status']}\n")
            f_log.write(f"Summary: {result['summary']}\n")
            f_log.write("--- Ingestion Complete ---\n")
    except Exception as e:
        with open(log_file, "a") as f_log:
            f_log.write(f"ERROR: {str(e)}\n")

async def main():
    print("=== Ground Truth Ingestion (Sequencing) ===")
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs("data/ground-truth", exist_ok=True)
    
    agent = KnowledgeAgent(model_id=GPT5_NANO)
    
    for filename in FILES:
        # Check if already done (check log for "Complete")
        log_file = os.path.join(LOG_DIR, f"{filename}.log")
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                if "Ingestion Complete" in f.read():
                    print(f"Skipping {filename} (already complete)")
                    continue
        
        await ingest_file(agent, filename)
        
    print("=== All Ground Truth Tasks Initiated/Completed ===")

if __name__ == "__main__":
    asyncio.run(main())
