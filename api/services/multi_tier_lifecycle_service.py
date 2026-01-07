"""
Multi-Tier Memory Lifecycle Service (Feature 044)
Implements Hot/Warm/Cold biological memory lifecycle.

Hot: Immediate high-fidelity context (Episodic Memories in Neo4j).
Warm: Summarized transitional context (Summarized Episodes in Neo4j).
Cold: Deep archival consolidated wisdom (Entities/Relationships in Graphiti).
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from uuid import uuid4

from api.services.webhook_neo4j_driver import get_neo4j_driver
from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.consolidation_service import get_consolidation_service

logger = logging.getLogger("dionysus.multi_tier_lifecycle")

class MultiTierLifecycleService:
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()
        self._consolidation_svc = get_consolidation_service()

    async def run_lifecycle_management(self):
        """
        Execute migration and compression policies across tiers.
        """
        logger.info("Starting Multi-Tier Memory Lifecycle Management...")
        
        # 1. Migration: Hot -> Warm (Summarize episodic memories older than 24h)
        warm_count = await self._migrate_hot_to_warm(age_hours=24)
        
        # 2. Migration: Warm -> Cold (Consolidate summaries into Graphiti)
        cold_count = await self._migrate_warm_to_cold(min_access=2)
        
        return {
            "status": "success",
            "hot_to_warm": warm_count,
            "warm_to_cold": cold_count
        }

    async def _migrate_hot_to_warm(self, age_hours: int = 24) -> int:
        """
        Move old 'hot' episodic memories to 'warm' summaries.
        """
        threshold = (datetime.utcnow() - timedelta(hours=age_hours)).isoformat()
        
        # Find unsummarized episodic memories
        # We look for nodes labeled Memory with memory_type episodic
        cypher = """
        MATCH (m:Memory)
        WHERE m.memory_type = 'episodic'
          AND m.created_at < $threshold
          AND NOT (m)-[:SUMMARIZED_BY]->()
        RETURN m
        LIMIT 20
        """
        
        try:
            result = await self._driver.execute_query(cypher, {"threshold": threshold})
            memories = [row["m"] for row in result]
        except Exception as e:
            logger.error(f"Failed to fetch hot memories for migration: {e}")
            return 0
        
        if not memories:
            return 0
            
        count = 0
        for m in memories:
            try:
                # Compress / Summarize
                content = m.get("content") or m.get("text") or ""
                if not content:
                    continue
                    
                summary = await self._compress_memory(content)
                
                # Create Warm Memory node
                warm_id = str(uuid4())
                create_warm_cypher = """
                MATCH (m:Memory {id: $id})
                CREATE (s:WarmMemory {
                    id: $warm_id,
                    content: $summary,
                    original_id: $id,
                    created_at: datetime(),
                    access_count: 0
                })
                CREATE (m)-[:SUMMARIZED_BY]->(s)
                SET m.tier = 'warm'
                """
                await self._driver.execute_query(create_warm_cypher, {
                    "id": m["id"],
                    "warm_id": warm_id,
                    "summary": summary
                })
                count += 1
            except Exception as e:
                logger.warning(f"Failed to migrate individual memory {m.get('id')}: {e}")
            
        logger.info(f"Migrated {count} memories from Hot to Warm.")
        return count

    async def _migrate_warm_to_cold(self, min_access: int = 2) -> int:
        """
        Move 'warm' summaries to 'cold' semantic knowledge in Graphiti.
        """
        cypher = """
        MATCH (s:WarmMemory)
        WHERE NOT (s)-[:CONSOLIDATED_TO]->()
        RETURN s
        LIMIT 20
        """
        
        try:
            result = await self._driver.execute_query(cypher)
            warm_memories = [row["s"] for row in result]
        except Exception as e:
            logger.error(f"Failed to fetch warm memories for migration: {e}")
            return 0
        
        if not warm_memories:
            return 0
            
        try:
            graphiti = await get_graphiti_service()
        except Exception as e:
            logger.error(f"Could not initialize Graphiti for cold migration: {e}")
            return 0

        count = 0
        for s in warm_memories:
            try:
                # Ingest to Graphiti
                extraction = await graphiti.ingest_message(
                    content=s["content"],
                    source_description=f"warm_migration_of_{s['original_id']}"
                )
                
                if extraction.get("episode_uuid"):
                    link_cypher = """
                    MATCH (s:WarmMemory {id: $warm_id})
                    MERGE (e:Episode {uuid: $ep_id})
                    CREATE (s)-[:CONSOLIDATED_TO]->(e)
                    SET s.tier = 'cold'
                    """
                    await self._driver.execute_query(link_cypher, {
                        "warm_id": s["id"],
                        "ep_id": extraction["episode_uuid"]
                    })
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to migrate warm memory {s.get('id')} to cold: {e}")
                
        logger.info(f"Migrated {count} warm memories to Cold storage (Graphiti).")
        return count

    async def _compress_memory(self, content: str) -> str:
        """
        Use LLM to compress a raw episodic memory into a dense semantic summary.
        """
        prompt = f"""Summarize the following interaction log into a single dense sentence 
        that captures the core 'wisdom' or 'lesson learned'. 
        Discard exact syntax, focus on strategic value.
        
        LOG:
        {content[:2000]}
        """
        
        return await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a biological memory compressor.",
            model=GPT5_NANO,
            max_tokens=128
        )

_lifecycle_instance: Optional[MultiTierLifecycleService] = None

def get_multi_tier_lifecycle_service() -> MultiTierLifecycleService:
    global _lifecycle_instance
    if _lifecycle_instance is None:
        _lifecycle_instance = MultiTierLifecycleService()
    return _lifecycle_instance
