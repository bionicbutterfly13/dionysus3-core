#!/usr/bin/env python3
"""
Distills wisdom from Graphiti-ingested book chapters.
Fetches messages from 'book-inner-architect-ch*' groups and runs WisdomDistiller.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.graphiti_service import get_graphiti_service
from api.agents.knowledge.wisdom_distiller import WisdomDistiller
from api.services.wisdom_service import get_wisdom_service, WisdomUnit

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("distill_book_wisdom")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters", nargs="+", type=int, default=[1, 2, 3, 4], help="Chapters to distill")
    args = parser.parse_args()
    
    graphiti = await get_graphiti_service()
    distiller = WisdomDistiller()
    wisdom_service = get_wisdom_service()
    
    chapters = args.chapters
    
    for ch in chapters:
        group_id = f"book-inner-architect-ch{ch}"
        logger.info(f"--- Processing {group_id} ---")
        
        # 1. Fetch episodes (chunks)
        # 1. Fetch episodes (chunks)
        query = """
        MATCH (e:Episode)-[:BELONGS_TO]->(g:Group {id: $group_id})
        RETURN e.content as content
        """
        results = await graphiti.execute_cypher(query, {"group_id": group_id})
        
        if not results:
            logger.warning(f"No content found for {group_id}")
            continue
            
        chunks = [r["content"] for r in results]
        logger.info(f"Found {len(chunks)} chunks.")
        
        # 2. Distill
        # We treat the whole chapter's chunks as a single context for distillation
        # But we need to chunk it for the LLM if it's too big.
        # For now, let's take the first 30 chunks 
        
        combined_text = "\n\n".join(chunks[:30]) 
        
        # Create a mock 'cluster' of fragments
        fragments = [{"content": chunk} for chunk in chunks[:30]]
        
        logger.info("Running Distiller Agent...")
        try:
            # Distill Principles
            result_p = await distiller.distill_cluster(fragments, "strategic_principle")
            logger.info(f"Principles: {result_p['result'][:100]}...")
            
            # Store
            await wisdom_service.store_manual_wisdom(
                name=f"Principles from Chapter {ch}",
                summary=result_p['result'],
                wisdom_type="strategic_principle",
                richness=0.9
            )
            
            # Distill Mental Models
            result_m = await distiller.distill_cluster(fragments, "mental_model")
            logger.info(f"Models: {result_m['result'][:100]}...")
             
            await wisdom_service.store_manual_wisdom(
                name=f"Mental Models from Chapter {ch}",
                summary=result_m['result'],
                wisdom_type="mental_model",
                richness=0.9
            )
            
            print(f"✅ Distilled Wisdom for Chapter {ch}")

        except Exception as e:
            logger.error(f"Distillation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
