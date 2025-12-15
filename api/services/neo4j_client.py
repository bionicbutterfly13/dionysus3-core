"""
Neo4j Client with Connection Pooling
Feature: 002-remote-persistence-safety
Task: T015

Async Neo4j client for remote persistence to VPS Neo4j instance.
Provides connection management, CRUD operations for Memory nodes,
and proper error handling.
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Raised when Neo4j connection fails."""

    pass


class Neo4jClient:
    """
    Async Neo4j client with connection pooling.

    Usage:
        client = Neo4jClient(uri, user, password)
        await client.connect()
        try:
            memory = await client.get_memory(memory_id)
        finally:
            await client.close()

    Or as async context manager:
        async with Neo4jClient(uri, user, password) as client:
            memory = await client.get_memory(memory_id)
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "",
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 50,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j bolt URI (e.g., bolt://localhost:7687)
            user: Neo4j username
            password: Neo4j password
            max_connection_lifetime: Max lifetime of pooled connections in seconds
            max_connection_pool_size: Max number of connections in pool
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.max_connection_lifetime = max_connection_lifetime
        self.max_connection_pool_size = max_connection_pool_size
        self._driver = None

    async def connect(self) -> bool:
        """
        Establish connection to Neo4j.

        Returns:
            True if connection successful

        Raises:
            Neo4jConnectionError: If connection fails
        """
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
            )

            # Verify connection
            async with self._driver.session() as session:
                result = await session.run("RETURN 1 as n")
                record = await result.single()
                if record and record["n"] == 1:
                    logger.info(f"Connected to Neo4j at {self.uri}")
                    return True

            raise Neo4jConnectionError("Connection verification failed")

        except AuthError as e:
            raise Neo4jConnectionError(f"Authentication failed: {e}")
        except ServiceUnavailable as e:
            raise Neo4jConnectionError(f"Neo4j service unavailable: {e}")
        except Exception as e:
            raise Neo4jConnectionError(f"Connection failed: {e}")

    async def close(self):
        """Close the Neo4j driver and release connections."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get_server_info(self) -> dict:
        """
        Get Neo4j server information.

        Returns:
            Dictionary with server version and other info
        """
        if not self._driver:
            raise Neo4jConnectionError("Not connected")

        async with self._driver.session() as session:
            result = await session.run(
                "CALL dbms.components() YIELD name, versions, edition "
                "RETURN name, versions[0] as version, edition"
            )
            record = await result.single()
            if record:
                return {
                    "name": record["name"],
                    "version": record["version"],
                    "edition": record["edition"],
                }
            return {}

    # =========================================================================
    # Memory CRUD Operations
    # =========================================================================

    async def create_memory(self, memory_data: dict) -> dict:
        """
        Create a Memory node in Neo4j.

        Args:
            memory_data: Dictionary with memory fields

        Returns:
            Created memory record
        """
        if not self._driver:
            raise Neo4jConnectionError("Not connected")

        query = """
        CREATE (m:Memory {
            id: $id,
            content: $content,
            memory_type: $memory_type,
            importance: $importance,
            source_project: $source_project,
            session_id: $session_id,
            tags: coalesce($tags, []),
            sync_version: $sync_version,
            created_at: datetime($created_at),
            updated_at: datetime(coalesce($updated_at, $created_at))
        })
        RETURN m {
            .id, .content, .memory_type, .importance,
            .source_project, .session_id, .tags, .sync_version,
            created_at: toString(m.created_at),
            updated_at: toString(m.updated_at)
        } as memory
        """

        async with self._driver.session() as session:
            result = await session.run(
                query,
                id=str(memory_data.get("id")),
                content=memory_data.get("content"),
                memory_type=memory_data.get("memory_type"),
                importance=memory_data.get("importance", 0.5),
                source_project=memory_data.get("source_project"),
                session_id=str(memory_data.get("session_id")),
                tags=memory_data.get("tags", []),
                sync_version=memory_data.get("sync_version", 1),
                created_at=memory_data.get(
                    "created_at", datetime.utcnow().isoformat()
                ),
                updated_at=memory_data.get("updated_at"),
            )
            record = await result.single()
            return dict(record["memory"]) if record else None

    async def get_memory(self, memory_id: str) -> Optional[dict]:
        """
        Get a Memory node by ID.

        Args:
            memory_id: UUID string of the memory

        Returns:
            Memory record or None if not found
        """
        if not self._driver:
            raise Neo4jConnectionError("Not connected")

        query = """
        MATCH (m:Memory {id: $id})
        RETURN m {
            .id, .content, .memory_type, .importance,
            .source_project, .session_id, .tags, .sync_version,
            created_at: toString(m.created_at),
            updated_at: toString(m.updated_at)
        } as memory
        """

        async with self._driver.session() as session:
            result = await session.run(query, id=str(memory_id))
            record = await result.single()
            return dict(record["memory"]) if record else None

    async def update_memory(
        self, memory_id: str, update_data: dict
    ) -> Optional[dict]:
        """
        Update a Memory node with sync version conflict resolution.

        Only updates if the new sync_version is greater than existing.

        Args:
            memory_id: UUID string of the memory
            update_data: Dictionary with fields to update (must include sync_version)

        Returns:
            Updated memory record
        """
        if not self._driver:
            raise Neo4jConnectionError("Not connected")

        query = """
        MATCH (m:Memory {id: $id})
        WITH m,
             CASE WHEN $sync_version > m.sync_version THEN true ELSE false END as should_update
        SET m.content = CASE WHEN should_update THEN coalesce($content, m.content) ELSE m.content END,
            m.memory_type = CASE WHEN should_update THEN coalesce($memory_type, m.memory_type) ELSE m.memory_type END,
            m.importance = CASE WHEN should_update THEN coalesce($importance, m.importance) ELSE m.importance END,
            m.tags = CASE WHEN should_update THEN coalesce($tags, m.tags) ELSE m.tags END,
            m.sync_version = CASE WHEN should_update THEN $sync_version ELSE m.sync_version END,
            m.updated_at = CASE WHEN should_update THEN datetime() ELSE m.updated_at END
        RETURN m {
            .id, .content, .memory_type, .importance,
            .source_project, .session_id, .tags, .sync_version,
            created_at: toString(m.created_at),
            updated_at: toString(m.updated_at)
        } as memory
        """

        async with self._driver.session() as session:
            result = await session.run(
                query,
                id=str(memory_id),
                content=update_data.get("content"),
                memory_type=update_data.get("memory_type"),
                importance=update_data.get("importance"),
                tags=update_data.get("tags"),
                sync_version=update_data.get("sync_version", 1),
            )
            record = await result.single()
            return dict(record["memory"]) if record else None

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a Memory node and its relationships.

        Args:
            memory_id: UUID string of the memory

        Returns:
            True if deleted, False if not found
        """
        if not self._driver:
            raise Neo4jConnectionError("Not connected")

        query = """
        MATCH (m:Memory {id: $id})
        DETACH DELETE m
        RETURN count(m) as deleted
        """

        async with self._driver.session() as session:
            result = await session.run(query, id=str(memory_id))
            record = await result.single()
            return record["deleted"] > 0 if record else False

    # =========================================================================
    # Bulk Operations (for recovery)
    # =========================================================================

    async def get_all_memories(
        self, project_id: Optional[str] = None, limit: int = 1000
    ) -> list[dict]:
        """
        Get all memories, optionally filtered by project.

        Args:
            project_id: Optional project filter
            limit: Maximum number of memories to return

        Returns:
            List of memory records
        """
        if not self._driver:
            raise Neo4jConnectionError("Not connected")

        if project_id:
            query = """
            MATCH (m:Memory)
            WHERE m.source_project = $project_id
            RETURN m {
                .id, .content, .memory_type, .importance,
                .source_project, .session_id, .tags, .sync_version,
                created_at: toString(m.created_at),
                updated_at: toString(m.updated_at)
            } as memory
            ORDER BY m.created_at ASC
            LIMIT $limit
            """
            params = {"project_id": project_id, "limit": limit}
        else:
            query = """
            MATCH (m:Memory)
            RETURN m {
                .id, .content, .memory_type, .importance,
                .source_project, .session_id, .tags, .sync_version,
                created_at: toString(m.created_at),
                updated_at: toString(m.updated_at)
            } as memory
            ORDER BY m.created_at ASC
            LIMIT $limit
            """
            params = {"limit": limit}

        async with self._driver.session() as session:
            result = await session.run(query, **params)
            records = await result.values()
            return [dict(r[0]) for r in records]

    async def get_memory_count(self, project_id: Optional[str] = None) -> int:
        """
        Get count of memories, optionally filtered by project.

        Args:
            project_id: Optional project filter

        Returns:
            Number of memories
        """
        if not self._driver:
            raise Neo4jConnectionError("Not connected")

        if project_id:
            query = """
            MATCH (m:Memory)
            WHERE m.source_project = $project_id
            RETURN count(m) as count
            """
            params = {"project_id": project_id}
        else:
            query = "MATCH (m:Memory) RETURN count(m) as count"
            params = {}

        async with self._driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record["count"] if record else 0
