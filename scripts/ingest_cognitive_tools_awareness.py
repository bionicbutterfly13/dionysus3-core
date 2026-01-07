"""
Script to ingest research-validated cognitive tool definitions into Graphiti.
Feature 042 / 043 awareness bootstrapping.
"""
import asyncio
import logging
from api.services.graphiti_service import get_graphiti_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOLS_KNOWLEDGE = [
    {
        "name": "understand_question",
        "description": "Decomposes complex problems into structured steps and mathematical concepts. Research-validated to improve accuracy.",
        "usage": "Use this tool first for any complex or ambiguous query to break it down."
    },
    {
        "name": "recall_related",
        "description": "Retrieves analogous solved examples to guide reasoning. Based on analogical reasoning principles.",
        "usage": "Use after understand_question to find similar solved patterns."
    },
    {
        "name": "examine_answer",
        "description": "Critically verifies reasoning traces for errors, miscalculations, or unjustified leaps.",
        "usage": "Use before finalizing an answer to self-correct and ensure high fidelity."
    },
    {
        "name": "backtracking",
        "description": "Identifies where reasoning went wrong and proposes alternative strategies. High impact on error recovery.",
        "usage": "Use if examine_answer detects flaws in the current reasoning path."
    }
]

async def bootstrap_tools_awareness():
    service = await get_graphiti_service()
    
    for tool in TOOLS_KNOWLEDGE:
        content = f"Tool Capability: {tool['name']}. Description: {tool['description']} Best practice: {tool['usage']}"
        logger.info(f"Ingesting awareness for {tool['name']}...")
        await service.ingest_message(
            content=content,
            source_description="system_bootstrapping",
            group_id="dionysus_capabilities"
        )
    
    logger.info("Cognitive tools awareness successfully ingested into Knowledge Graph.")

if __name__ == "__main__":
    asyncio.run(bootstrap_tools_awareness())
