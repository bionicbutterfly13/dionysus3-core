"""
Script to generate IAS Marketing Suite assets using the MarketingAgent.
Feature: 017-ias-marketing-suite
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

from api.agents.marketing_agent import MarketingAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("generate_marketing")

# Define target export directory
EXPORT_DIR = "/Volumes/Arkham/Marketing/stefan/assets/"

async def generate_assets():
    agent = MarketingAgent()
    
    # Ensure export directory exists (might need sudo or manual mount)
    if not os.path.exists(EXPORT_DIR):
        logger.warning(f"Export directory {EXPORT_DIR} not found. Saving to local 'assets' folder.")
        os.makedirs("assets", exist_ok=True)
        export_path = "assets/"
    else:
        export_path = EXPORT_DIR

    # 1. Generate Nurture Emails (5-10)
    emails_to_generate = [
        {"topic": "Conviction Gauntlet mechanism", "framework": "Conviction Gauntlet", "file": "email_05.json"},
        {"topic": "Safety protocol keeping you small", "framework": "Neuro-Safety", "file": "email_06.json"},
        {"topic": "What therapy misses", "framework": "Active Inference Coaching", "file": "email_07.json"},
        {"topic": "60-second MOSAEIC reset", "framework": "MOSAEIC Protocol", "file": "email_08.json"},
        {"topic": "The cost of waiting", "framework": "Opportunity Cost Analysis", "file": "email_09.json"},
        {"topic": "Your story + why I built this", "framework": "Authentic Leadership", "file": "email_10.json"},
    ]

    for item in emails_to_generate:
        logger.info(f"Generating email: {item['topic']}")
        try:
            result = await agent.generate_email(item['topic'], item['framework'])
            with open(os.path.join(export_path, item['file']), "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"  ✓ Saved to {item['file']}")
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")

    # 2. Generate Sales Page
    logger.info("Generating $97 Tripwire Sales Page (Blueprint Bundle)")
    try:
        sales_page = await agent.generate_sales_page(
            product="IAS Blueprint Bundle",
            positioning="A step-by-step cognitive toolkit for high-performing professionals to end burnout and reclaim 10+ hours per week."
        )
        with open(os.path.join(export_path, "sales_page_tripwire.json"), "w") as f:
            json.dump(sales_page, f, indent=2)
        logger.info("  ✓ Saved to sales_page_tripwire.json")
    except Exception as e:
        logger.error(f"  ✗ Failed: {e}")

    logger.info("Marketing asset generation session complete.")

if __name__ == "__main__":
    asyncio.run(generate_assets())
