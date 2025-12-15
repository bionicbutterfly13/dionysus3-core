"""
Neo4j Client
Feature: 002-remote-persistence-safety
Task: T015

Neo4j connection management.

IMPORTANT: Per architecture decision, all Neo4j access goes through n8n webhooks.
This client provides the interface but delegates to RemoteSyncService.

For direct Neo4j access (testing/admin only), use the neo4j Python driver.
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


# =============================================================================
# Neo4j Client (Webhook-based)
# =============================================================================

class Neo4jClient:
    """
    Neo4j client that routes through n8n webhooks.

    This is the recommended approach for production use.
    For direct connections (testing only), use Neo4jDirectClient.
    """

    def __init__(self):
        from api.services.remote_sync import RemoteSyncService
        self._sync_service = RemoteSyncService()

    async def get_memory(self, memory_id: str) -> Optional[dict[str, Any]]:
        """Get memory from Neo4j via webhook."""
        return await self._sync_service.get_memory_from_neo4j(memory_id)

    async def query_memories(
        self,
        query: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Query memories via webhook."""
        if session_id:
            return await self._sync_service.query_by_session(session_id, query)
        elif project_id:
            return await self._sync_service.query_by_project(project_id, query, limit)
        elif query:
            return await self._sync_service.search_memories(query, limit=limit)
        return []

    async def check_health(self) -> dict[str, Any]:
        """Check Neo4j connectivity via webhook."""
        return await self._sync_service.check_health()


# =============================================================================
# Neo4j Direct Client (Testing/Admin Only)
# =============================================================================

class Neo4jDirectClient:
    """
    Direct Neo4j connection for testing and admin operations.

    WARNING: Only use via SSH tunnel in development.
    Production should use Neo4jClient (webhook-based).
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self._driver = None

    async def connect(self):
        """Establish direct connection to Neo4j."""
        try:
            from neo4j import AsyncGraphDatabase
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except ImportError:
            logger.error("neo4j package not installed. Run: pip install neo4j")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self):
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """Execute Cypher query."""
        if not self._driver:
            await self.connect()

        async with self._driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def get_memory(self, memory_id: str) -> Optional[dict[str, Any]]:
        """Get memory directly from Neo4j."""
        query = """
        MATCH (m:Memory {id: $memory_id})
        RETURN m
        """
        results = await self.execute_query(query, {"memory_id": memory_id})
        return results[0]["m"] if results else None

    async def check_health(self) -> dict[str, Any]:
        """Check direct Neo4j connectivity."""
        try:
            if not self._driver:
                await self.connect()

            result = await self.execute_query("RETURN 1 as test")
            return {
                "status": "healthy",
                "connection": "direct",
                "uri": self.uri,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# =============================================================================
# Factory Function
# =============================================================================

def get_neo4j_client(direct: bool = False) -> Neo4jClient | Neo4jDirectClient:
    """
    Get Neo4j client instance.

    Args:
        direct: If True, return direct connection client (testing only)

    Returns:
        Neo4j client instance
    """
    if direct:
        return Neo4jDirectClient()
    return Neo4jClient()
