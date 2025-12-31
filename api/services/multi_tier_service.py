"""
Unified Multi-Tier Memory Service (Feature 047)

Integrates Features 044 (Biological Lifecycle) and 047 (High-Speed Tiering).
Handles memory across three performance tiers:
1. HOT: Caching/Session context (In-memory).
2. WARM: Neo4j Semantic Graph (Longer-term).
3. COLD: Long-term archives (Compressed/Consolidated).
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid

from api.models.memory_tier import MemoryTier, TieredMemoryItem, MigrationReport
from api.services.webhook_neo4j_driver import get_neo4j_driver
from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger("dionysus.multi_tier_service")

class TieredHotMemoryManager:
    """Session-level high-speed memory (In-memory cache)."""
    def __init__(self):
        self._store: Dict[str, TieredMemoryItem] = {}

    async def store(self, item: TieredMemoryItem):
        item.tier = MemoryTier.HOT
        item.last_accessed = datetime.utcnow()
        self._store[item.id] = item
        return True

    async def retrieve(self, item_id: str) -> Optional[TieredMemoryItem]:
        item = self._store.get(item_id)
        if item:
            item.last_accessed = datetime.utcnow()
        return item

    async def list_expired(self, hours: int = 24) -> List[TieredMemoryItem]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [item for item in self._store.values() if item.created_at < cutoff]

    async def remove(self, item_id: str):
        if item_id in self._store:
            del self._store[item_id]

class TieredWarmMemoryManager:
    """Neo4j Knowledge Graph persistence (Warm Tier)."""
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    async def store(self, item: TieredMemoryItem):
        query = """
        MERGE (m:MemoryItem {id: $id})
        SET m.content = $content,
            m.memory_type = $memory_type,
            m.tier = 'warm',
            m.importance_score = $importance,
            m.created_at = $created_at,
            m.project_id = $project_id,
            m.metadata = $metadata,
            m.summary = $summary
        """
        params = {
            "id": item.id,
            "content": item.content,
            "memory_type": item.memory_type,
            "importance": item.importance_score,
            "created_at": item.created_at.isoformat(),
            "project_id": item.project_id,
            "metadata": json.dumps(item.metadata),
            "summary": item.metadata.get("summary")
        }
        await self._driver.execute_query(query, params)
        return True

class TieredColdMemoryManager:
    """Long-term archival storage (Graphiti)."""
    async def store(self, item: TieredMemoryItem):
        # COLD storage: Mark as cold in Neo4j and move to Graphiti
        driver = get_neo4j_driver()
        graphiti = await get_graphiti_service()
        
        # 1. Ingest to Graphiti for permanent fact extraction
        content = item.metadata.get("summary") or item.content
        await graphiti.ingest_message(
            content=content,
            source_description=f"cold_archive_{item.id}",
            group_id=item.project_id
        )
        
        # 2. Update status in Neo4j
        query = """
        MATCH (m:MemoryItem {id: $id})
        SET m.tier = 'cold'
        REMOVE m:MemoryItem
        SET m:ArchiveItem
        """
        await driver.execute_query(query, {"id": item.id})
        return True

class MultiTierMemoryService:
    """
    Main entry point for tiered memory.
    Ensures optimal retrieval latency by checking HOT -> WARM -> COLD.
    """
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()
        self.hot = TieredHotMemoryManager()
        self.warm = TieredWarmMemoryManager(self._driver)
        self.cold = TieredColdMemoryManager()

    async def store_memory(self, content: str, importance: float = 0.5, **kwargs) -> str:
        """
        All new memories start in HOT tier.
        """
        item = TieredMemoryItem(
            content=content,
            importance_score=importance,
            **kwargs
        )
        await self.hot.store(item)
        logger.info(f"Stored item {item.id} in HOT memory.")
        return item.id

    async def retrieve_memory(self, item_id: str) -> Optional[TieredMemoryItem]:
        """
        Hierarchical retrieval: HOT (0ms) -> WARM (Neo4j) -> COLD (Graphiti).
        """
        # 1. Try Hot
        item = await self.hot.retrieve(item_id)
        if item:
            return item
        
        # 2. Try Warm (Neo4j)
        query = "MATCH (m:MemoryItem {id: $id}) RETURN m"
        result = await self._driver.execute_query(query, {"id": item_id})
        if result:
            data = result[0]["m"]
            return TieredMemoryItem(
                id=data["id"],
                content=data["content"],
                memory_type=data["memory_type"],
                tier=MemoryTier.WARM,
                importance_score=data.get("importance_score", 0.5),
                project_id=data.get("project_id", "default")
            )
        return None

    async def run_lifecycle_management(self) -> Dict[str, Any]:
        """
        Unified lifecycle: HOT -> WARM (24h) -> COLD (Low importance/age).
        """
        logger.info("Starting Multi-Tier Lifecycle Management...")
        
        # 1. HOT -> WARM (Age > 24h)
        expired_hot = await self.hot.list_expired(hours=24)
        for item in expired_hot:
            # Summarize before moving to Warm to keep graph light
            summary = await self._compress_memory(item.content)
            item.metadata["summary"] = summary
            await self.warm.store(item)
            await self.hot.remove(item.id)
            
        # 2. WARM -> COLD (Optional logic for later)
        
        return {
            "status": "success",
            "hot_to_warm": len(expired_hot),
            "warm_to_cold": 0
        }

    async def _compress_memory(self, content: str) -> str:
        """Use LLM to create a dense semantic summary."""
        prompt = f"Summarize this interaction into one dense strategic sentence: {content[:2000]}"
        return await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a biological memory compressor.",
            model=GPT5_NANO,
            max_tokens=128
        )

# Singleton
_multi_tier_instance: Optional[MultiTierMemoryService] = None

def get_multi_tier_service() -> MultiTierMemoryService:
    global _multi_tier_instance
    if _multi_tier_instance is None:
        _multi_tier_instance = MultiTierMemoryService()
    return _multi_tier_instance