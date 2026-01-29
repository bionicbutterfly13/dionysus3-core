"""
Hexis Memory Service
Feature: 101-hexis-core-migration

Facade over Graphiti/MemEvolve providing Hexis-style memory API.
Supports recall(), store(), and neighborhood retrieval.

Inlets:
    - Agent queries for memory recall
    - Content to store from agents/services
Outlets:
    - GraphitiService (search, persist_fact)
    - MemEvolveAdapter (trajectory ingestion)
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field

from api.services.graphiti_service import get_graphiti_service
from api.models.hexis_ontology import MemoryType, Neighborhood, NeighborhoodType

logger = logging.getLogger(__name__)


class MemoryItem(BaseModel):
    """A single memory item returned from recall."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    content: str
    memory_type: MemoryType = MemoryType.SEMANTIC
    relevance: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)


class HexisMemoryService:
    """
    Hexis-style memory API facade over Graphiti/MemEvolve.

    Provides unified recall/store interface while routing through
    the established memory stack (GraphitiService → Neo4j).
    """

    # Basin prefix for hexis memory operations
    BASIN_PREFIX = "hexis_memory"

    def __init__(self):
        pass

    async def recall(
        self,
        query: str,
        agent_id: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None
    ) -> List[MemoryItem]:
        """
        Recall memories matching the query.

        Args:
            query: Search query
            agent_id: Agent/session identifier
            limit: Maximum results to return
            memory_type: Optional filter by memory type

        Returns:
            List of MemoryItem objects
        """
        try:
            graphiti = await get_graphiti_service()

            # Search with agent context
            results = await graphiti.search(
                query=query,
                group_ids=[agent_id],
                limit=limit
            )

            # Convert edges to MemoryItems
            items: List[MemoryItem] = []
            edges = results.get("edges", [])

            for edge in edges[:limit]:  # Enforce limit
                fact = edge.get("fact", "")
                if fact:
                    items.append(MemoryItem(
                        id=edge.get("uuid", uuid4().hex),
                        content=fact,
                        memory_type=memory_type or MemoryType.SEMANTIC,
                        relevance=edge.get("score", 0.0),
                        metadata={"source": "graphiti_search"}
                    ))

            return items

        except Exception as e:
            logger.error(f"recall() failed for agent {agent_id}: {e}")
            return []

    async def store(
        self,
        content: str,
        agent_id: str,
        memory_type: MemoryType = MemoryType.SEMANTIC
    ) -> Optional[str]:
        """
        Store a memory through Graphiti.

        Args:
            content: Memory content to store
            agent_id: Agent/session identifier
            memory_type: Type of memory (affects basin routing)

        Returns:
            ID of stored memory, or None on failure
        """
        try:
            graphiti = await get_graphiti_service()

            # Construct basin_id from memory type
            basin_id = f"{self.BASIN_PREFIX}_{memory_type.value}"

            # Persist through Graphiti
            await graphiti.persist_fact(
                fact_text=content,
                source_episode_id=f"hexis_store_{uuid4().hex[:8]}",
                valid_at=datetime.now(timezone.utc),
                basin_id=basin_id,
                confidence=1.0,
                group_id=agent_id
            )

            memory_id = uuid4().hex
            logger.info(f"Stored memory for {agent_id} in basin {basin_id}")
            return memory_id

        except Exception as e:
            logger.error(f"store() failed for agent {agent_id}: {e}")
            return None

    async def get_neighborhoods(
        self,
        agent_id: str
    ) -> List[Neighborhood]:
        """
        Retrieve pre-computed memory neighborhoods for the agent.

        Neighborhoods are clusters of related memories that enable
        rapid 'warm path' retrieval.

        Args:
            agent_id: Agent/session identifier

        Returns:
            List of Neighborhood objects
        """
        try:
            graphiti = await get_graphiti_service()

            # Query for neighborhood nodes
            rows = await graphiti.execute_cypher(
                """
                MATCH (n:Neighborhood {group_id: $group_id})
                RETURN n.name as name, n.type as type,
                       size((n)-[:CONTAINS]->()) as member_count
                ORDER BY member_count DESC
                LIMIT 20
                """,
                {"group_id": agent_id}
            )

            neighborhoods: List[Neighborhood] = []
            for row in rows:
                try:
                    neighborhoods.append(Neighborhood(
                        name=row.get("name", "Unknown"),
                        type=NeighborhoodType(row.get("type", "topic")),
                        member_uuids=[]  # Would need separate query for members
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse neighborhood: {e}")

            return neighborhoods

        except Exception as e:
            logger.warning(f"get_neighborhoods() failed for {agent_id}: {e}")
            return []


# Singleton
_hexis_memory_service: Optional[HexisMemoryService] = None


def get_hexis_memory_service() -> HexisMemoryService:
    """Get singleton HexisMemoryService instance."""
    global _hexis_memory_service
    if _hexis_memory_service is None:
        _hexis_memory_service = HexisMemoryService()
    return _hexis_memory_service
