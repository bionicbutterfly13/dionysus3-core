"""
Initialize Boardroom Identity
Feature: 015-agentic-unified-model

Ensures the 'dionysus_system' user exists and has the standard boardroom aspects.
"""

import asyncio
import os
import logging
from api.services.aspect_service import get_aspect_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dionysus.init_boardroom")

CORE_ASPECTS = [
    {
        "name": "Protector",
        "role": "Ensures system safety and data integrity. Prevents destructive actions.",
        "status": "Active"
    },
    {
        "name": "Inner CEO",
        "role": "Strategic decision maker. Prioritizes goals and allocates energy.",
        "status": "Active"
    },
    {
        "name": "Visionary",
        "role": "Drives long-term growth and new feature emergence.",
        "status": "Active"
    },
    {
        "name": "Inner Child",
        "role": "Curiosity and exploration drive. Learns from play and new experiences.",
        "status": "Active"
    }
]

async def main():
    logger.info("Initializing Boardroom for 'dionysus_system'...")
    service = get_aspect_service()
    
    # 1. Ensure User exists (Implicit in upsert_aspect but good to be explicit)
    # 2. Upsert each core aspect
    for aspect in CORE_ASPECTS:
        try:
            await service.upsert_aspect(
                user_id="dionysus_system",
                name=aspect["name"],
                role=aspect["role"],
                status=aspect["status"]
            )
            logger.info(f"Initialized aspect: {aspect['name']}")
        except Exception as e:
            logger.error(f"Failed to initialize aspect {aspect['name']}: {e}")

    logger.info("Boardroom initialization complete.")

if __name__ == "__main__":
    asyncio.run(main())
