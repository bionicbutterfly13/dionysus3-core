"""
Script to run the Wisdom Distiller on raw fragments.
Feature: 031-wisdom-distillation
Task: T009
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.wisdom_service import get_wisdom_service
from api.agents.knowledge.wisdom_distiller import WisdomDistiller
from api.models.wisdom import MentalModel, StrategicPrinciple, CaseStudy, WisdomType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_wisdom_distiller")

async def run_distillation():
    service = get_wisdom_service()
    distiller = WisdomDistiller()
    
    raw_file = "wisdom_extraction_raw.json"
    if not os.path.exists(raw_file):
        logger.error(f"Raw file {raw_file} not found.")
        return

    with open(raw_file, "r") as f:
        raw_extracts = json.load(f)

    logger.info(f"Loaded {len(raw_extracts)} raw fragments.")

    # Group fragments by type (heuristic)
    # The raw extracts from KnowledgeAgent might have different formats
    # For now, let's just group them into a single 'mental_model' cluster for testing
    # Or try to find type hints in the fragments
    
    clusters = {
        "mental_model": [],
        "strategic_principle": [],
        "case_study": []
    }
    
    for fragment in raw_extracts[:50]: # Limit to first 50 for trial
        content = str(fragment.get("content", "")).lower()
        if "principle" in content or "rule" in content:
            clusters["strategic_principle"].append(fragment)
        elif "case" in content or "study" in content or "transformed" in content:
            clusters["case_study"].append(fragment)
        else:
            clusters["mental_model"].append(fragment)

    for w_type, fragments in clusters.items():
        if not fragments:
            continue
            
        logger.info(f"Distilling {len(fragments)} fragments into a canonical {w_type}...")
        
        try:
            # The distiller agent uses tools to synthesize
            result = await distiller.distill_cluster(fragments, w_type)
            # result['result'] is the string output from the agent
            
            logger.info(f"Distillation result for {w_type}: {result['result'][:200]}...")
            
            # In a real run, we'd parse the result string into a Pydantic model
            # and call service.persist_distilled_unit(unit)
            
        except Exception as e:
            logger.error(f"Failed to distill {w_type}: {e}")

    logger.info("Wisdom distillation run complete.")

if __name__ == "__main__":
    asyncio.run(run_distillation())
