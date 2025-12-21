"""
Graphiti Service - Real-time knowledge graph for entity tracking.

Direct Neo4j access (exception to n8n-only rule for this trusted component).
Uses Graphiti for temporal entity extraction and hybrid search.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    EDGE_HYBRID_SEARCH_RRF,
)

logger = logging.getLogger(__name__)


class GraphitiConfig:
    """Configuration for Graphiti service."""

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        group_id: str = "dionysus",
    ):
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://72.61.78.89:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.group_id = group_id

        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")


class GraphitiService:
    """
    Service wrapper for Graphiti knowledge graph operations.

    Provides:
    - Episode ingestion with entity extraction
    - Hybrid search (semantic + keyword + graph)
    - Temporal tracking of facts
    """

    _instance: Optional["GraphitiService"] = None
    _graphiti: Optional[Graphiti] = None

    def __init__(self, config: Optional[GraphitiConfig] = None):
        self.config = config or GraphitiConfig()
        self._initialized = False

    @classmethod
    async def get_instance(cls, config: Optional[GraphitiConfig] = None) -> "GraphitiService":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        if not cls._instance._initialized:
            await cls._instance.initialize()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize Graphiti connection and indexes."""
        if self._initialized:
            return

        logger.info(f"Initializing Graphiti with Neo4j at {self.config.neo4j_uri}")

        self._graphiti = Graphiti(
            uri=self.config.neo4j_uri,
            user=self.config.neo4j_user,
            password=self.config.neo4j_password,
        )

        # Build indexes (safe, won't delete existing)
        await self._graphiti.build_indices_and_constraints(delete_existing=False)

        self._initialized = True
        logger.info("Graphiti initialized successfully")

    async def close(self) -> None:
        """Close Graphiti connection."""
        if self._graphiti:
            await self._graphiti.close()
            self._initialized = False
            logger.info("Graphiti connection closed")

    async def ingest_message(
        self,
        content: str,
        source_description: str = "conversation",
        group_id: Optional[str] = None,
        valid_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Ingest a message/episode and extract entities.

        Args:
            content: The message content to process
            source_description: Description of the source (e.g., "user message", "session 123")
            group_id: Partition ID for multi-tenant separation
            valid_at: When the event occurred (defaults to now)

        Returns:
            Dict with extracted nodes and edges
        """
        if not self._graphiti:
            raise RuntimeError("GraphitiService not initialized")

        group = group_id or self.config.group_id
        timestamp = valid_at or datetime.now()

        logger.info(f"Ingesting message into group '{group}': {content[:100]}...")

        result = await self._graphiti.add_episode(
            name=f"episode_{uuid4().hex[:8]}",
            episode_body=content,
            source=EpisodeType.message,
            source_description=source_description,
            group_id=group,
            reference_time=timestamp,
        )

        logger.info(
            f"Extracted {len(result.nodes)} entities, "
            f"{len(result.edges)} relationships"
        )

        return {
            "episode_uuid": str(result.episode.uuid) if result.episode else None,
            "nodes": [
                {
                    "uuid": str(n.uuid),
                    "name": n.name,
                    "labels": getattr(n, "labels", []),
                    "summary": getattr(n, "summary", None),
                }
                for n in result.nodes
            ],
            "edges": [
                {
                    "uuid": str(e.uuid),
                    "name": e.name,
                    "fact": e.fact,
                    "source": str(e.source_node_uuid),
                    "target": str(e.target_node_uuid),
                }
                for e in result.edges
            ],
        }

    async def search(
        self,
        query: str,
        group_ids: Optional[list[str]] = None,
        limit: int = 10,
        use_cross_encoder: bool = False,
    ) -> dict[str, Any]:
        """
        Hybrid search across entities and relationships.

        Args:
            query: Search query
            group_ids: Filter by group IDs (default: service group_id)
            limit: Max results
            use_cross_encoder: Use LLM reranking (slower but better)

        Returns:
            Dict with nodes, edges, episodes found
        """
        if not self._graphiti:
            raise RuntimeError("GraphitiService not initialized")

        groups = group_ids or [self.config.group_id]
        config = COMBINED_HYBRID_SEARCH_CROSS_ENCODER if use_cross_encoder else EDGE_HYBRID_SEARCH_RRF

        logger.info(f"Searching for: {query}")

        results = await self._graphiti.search(
            query=query,
            group_ids=groups,
            config=config,
            num_results=limit,
        )

        return {
            "nodes": [
                {
                    "uuid": str(n.uuid),
                    "name": n.name,
                    "summary": getattr(n, "summary", None),
                    "labels": getattr(n, "labels", []),
                }
                for n in results.nodes
            ],
            "edges": [
                {
                    "uuid": str(e.uuid),
                    "name": e.name,
                    "fact": e.fact,
                    "valid_at": e.valid_at.isoformat() if e.valid_at else None,
                    "invalid_at": e.invalid_at.isoformat() if e.invalid_at else None,
                }
                for e in results.edges
            ],
            "episodes": [
                {
                    "uuid": str(ep.uuid),
                    "content": ep.content[:500] if ep.content else None,
                    "valid_at": ep.valid_at.isoformat() if ep.valid_at else None,
                }
                for ep in results.episodes
            ],
        }

    async def get_entity(self, name: str, group_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Get entity by name."""
        results = await self.search(name, group_ids=[group_id or self.config.group_id], limit=1)
        nodes = results.get("nodes", [])
        return nodes[0] if nodes else None

    async def health_check(self) -> dict[str, Any]:
        """Check Graphiti and Neo4j health."""
        try:
            if not self._graphiti:
                return {"healthy": False, "error": "Not initialized"}

            # Simple search to verify connectivity
            await self._graphiti.search(
                query="test",
                group_ids=[self.config.group_id],
                num_results=1,
            )

            return {
                "healthy": True,
                "neo4j_uri": self.config.neo4j_uri,
                "group_id": self.config.group_id,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}


# Convenience function
async def get_graphiti_service(config: Optional[GraphitiConfig] = None) -> GraphitiService:
    """Get the GraphitiService singleton."""
    return await GraphitiService.get_instance(config)
