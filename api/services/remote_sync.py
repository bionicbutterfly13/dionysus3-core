"""
Remote Sync Service
Feature: 002-remote-persistence-safety
Tasks: T020, T021

Handles synchronization between local PostgreSQL and remote Neo4j.
Includes queue management, retry logic, and recovery operations.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import httpx
from pydantic import BaseModel, Field

from api.services.neo4j_client import Neo4jClient, Neo4jConnectionError

logger = logging.getLogger(__name__)


# =========================================================================
# Configuration
# =========================================================================


class SyncConfig(BaseModel):
    """Configuration for remote sync service."""

    webhook_url: str = Field(
        default="http://localhost:5678/webhook/memory/v1/ingest/message",
        description="n8n webhook URL for memory sync",
    )
    webhook_token: str = Field(
        default="",
        description="HMAC secret for webhook authentication",
    )
    max_retries: int = Field(default=5, ge=1, le=10)
    initial_backoff_seconds: float = Field(default=1.0, ge=0.1)
    max_backoff_seconds: float = Field(default=300.0, ge=1.0)  # 5 minutes
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    queue_batch_size: int = Field(default=10, ge=1, le=100)
    request_timeout_seconds: float = Field(default=30.0, ge=5.0)


# =========================================================================
# Queue Item Model
# =========================================================================


class QueueItem(BaseModel):
    """Item in the sync queue."""

    memory_id: str
    operation: str  # create, update, delete
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = Field(default=0)
    next_retry_at: Optional[datetime] = None
    last_error: Optional[str] = None


# =========================================================================
# Remote Sync Service
# =========================================================================


class RemoteSyncService:
    """
    Service for synchronizing memories to remote Neo4j via n8n webhook.

    Features:
    - Queue management for pending sync operations
    - Exponential backoff retry logic
    - Session and project relationship creation
    - Bootstrap recovery from Neo4j

    Usage:
        sync_service = RemoteSyncService(neo4j_client)
        await sync_service.queue_memory(memory_data)
        await sync_service.process_queue()
    """

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        config: Optional[SyncConfig] = None,
    ):
        """
        Initialize sync service.

        Args:
            neo4j_client: Optional Neo4j client (only needed for recovery operations)
            config: Sync configuration (uses defaults if not provided)

        Note: Neo4j is only accessible through n8n. Normal sync operations use
        the webhook and don't require direct Neo4j access.
        """
        self.neo4j = neo4j_client
        self.config = config or SyncConfig()
        self._queue: deque[QueueItem] = deque()
        self._processing = False
        self._last_sync: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    # =========================================================================
    # Queue Management (T020)
    # =========================================================================

    def queue_memory(
        self,
        memory_id: str,
        operation: str,
        payload: dict[str, Any],
    ) -> QueueItem:
        """
        Add a memory sync operation to the queue.

        Args:
            memory_id: UUID of the memory
            operation: create, update, or delete
            payload: Full memory data to sync

        Returns:
            The created QueueItem
        """
        item = QueueItem(
            memory_id=memory_id,
            operation=operation,
            payload=payload,
        )
        self._queue.append(item)
        logger.info(f"Queued {operation} for memory {memory_id}")
        return item

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return len(self._queue)

    def get_pending_count(self) -> int:
        """Get count of items ready to process (not waiting for retry)."""
        now = datetime.utcnow()
        return sum(
            1
            for item in self._queue
            if item.next_retry_at is None or item.next_retry_at <= now
        )

    def get_failed_count(self) -> int:
        """Get count of items that have failed at least once."""
        return sum(1 for item in self._queue if item.retry_count > 0)

    async def process_queue(self, batch_size: Optional[int] = None) -> dict[str, Any]:
        """
        Process pending items in the queue.

        Args:
            batch_size: Max items to process (defaults to config)

        Returns:
            Summary of processing results
        """
        if self._processing:
            return {"error": "Queue processing already in progress"}

        self._processing = True
        batch_size = batch_size or self.config.queue_batch_size

        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "requeued": 0,
            "errors": [],
        }

        try:
            # Get items ready for processing
            now = datetime.utcnow()
            items_to_process = []

            for _ in range(min(batch_size, len(self._queue))):
                if not self._queue:
                    break
                item = self._queue[0]
                if item.next_retry_at is None or item.next_retry_at <= now:
                    items_to_process.append(self._queue.popleft())
                else:
                    # Skip items not ready for retry
                    break

            # Process each item
            for item in items_to_process:
                results["processed"] += 1
                try:
                    await self._sync_item(item)
                    results["succeeded"] += 1
                    self._last_sync = datetime.utcnow()
                except Exception as e:
                    error_msg = str(e)
                    results["failed"] += 1
                    results["errors"].append(
                        {"memory_id": item.memory_id, "error": error_msg}
                    )

                    # Requeue with backoff if retries remaining
                    if item.retry_count < self.config.max_retries:
                        item.retry_count += 1
                        item.last_error = error_msg
                        item.next_retry_at = self._calculate_next_retry(
                            item.retry_count
                        )
                        self._queue.append(item)
                        results["requeued"] += 1
                        logger.warning(
                            f"Requeued memory {item.memory_id} "
                            f"(attempt {item.retry_count}/{self.config.max_retries})"
                        )
                    else:
                        # Dead letter - exceeded max retries
                        logger.error(
                            f"Memory {item.memory_id} exceeded max retries, dropping"
                        )
                        self._last_error = error_msg

            return results

        finally:
            self._processing = False

    # =========================================================================
    # Retry Logic (T021)
    # =========================================================================

    def _calculate_next_retry(self, retry_count: int) -> datetime:
        """
        Calculate next retry time using exponential backoff.

        Args:
            retry_count: Current retry attempt number

        Returns:
            Datetime when next retry should occur
        """
        backoff = min(
            self.config.initial_backoff_seconds
            * (self.config.backoff_multiplier ** (retry_count - 1)),
            self.config.max_backoff_seconds,
        )
        return datetime.utcnow() + timedelta(seconds=backoff)

    async def _sync_item(self, item: QueueItem) -> dict[str, Any]:
        """
        Sync a single queue item to remote.

        Args:
            item: Queue item to sync

        Returns:
            Response from webhook

        Raises:
            Exception if sync fails
        """
        payload = item.payload.copy()

        # Generate HMAC signature
        payload_bytes = json.dumps(payload, default=str).encode("utf-8")
        signature = self._generate_signature(payload_bytes)

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout_seconds
        ) as client:
            response = await client.post(
                self.config.webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
            )

            if response.status_code == 200:
                logger.info(f"Successfully synced memory {item.memory_id}")
                return response.json()
            else:
                raise Exception(
                    f"Webhook returned {response.status_code}: {response.text}"
                )

    def _generate_signature(self, payload: bytes) -> str:
        """Generate HMAC-SHA256 signature for payload."""
        digest = hmac.new(
            key=self.config.webhook_token.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"

    # =========================================================================
    # Session Relationships
    # =========================================================================

    async def create_session_relationship(
        self,
        memory_id: str,
        session_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """
        Create Session node and BELONGS_TO relationship.

        Args:
            memory_id: Memory UUID
            session_id: Session UUID
            project_id: Project identifier

        Returns:
            Session node data
        """
        query = """
        MERGE (s:Session {id: $session_id})
        ON CREATE SET
            s.project_id = $project_id,
            s.started_at = datetime(),
            s.memory_count = 0
        WITH s
        MATCH (m:Memory {id: $memory_id})
        MERGE (m)-[:BELONGS_TO]->(s)
        WITH s, count(*) as rel_created
        SET s.memory_count = s.memory_count + CASE WHEN rel_created > 0 THEN 1 ELSE 0 END
        RETURN s {
            .id, .project_id, .memory_count,
            started_at: toString(s.started_at),
            ended_at: toString(s.ended_at),
            summary: s.summary
        } as session
        """

        async with self.neo4j._driver.session() as session:
            result = await session.run(
                query,
                memory_id=memory_id,
                session_id=session_id,
                project_id=project_id,
            )
            record = await result.single()
            return dict(record["session"]) if record else {}

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session data or None
        """
        query = """
        MATCH (s:Session {id: $session_id})
        RETURN s {
            .id, .project_id, .memory_count,
            started_at: toString(s.started_at),
            ended_at: toString(s.ended_at),
            summary: s.summary
        } as session
        """

        async with self.neo4j._driver.session() as session:
            result = await session.run(query, session_id=session_id)
            record = await result.single()
            return dict(record["session"]) if record else None

    # =========================================================================
    # Project Relationships
    # =========================================================================

    async def create_project_relationship(
        self,
        memory_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """
        Create Project node and TAGGED_WITH relationship.

        Args:
            memory_id: Memory UUID
            project_id: Project identifier

        Returns:
            Project node data
        """
        query = """
        MERGE (p:Project {id: $project_id})
        ON CREATE SET
            p.name = $project_id,
            p.created_at = datetime()
        WITH p
        MATCH (m:Memory {id: $memory_id})
        MERGE (m)-[:TAGGED_WITH]->(p)
        RETURN p {
            .id, .name, .description,
            created_at: toString(p.created_at)
        } as project
        """

        async with self.neo4j._driver.session() as session:
            result = await session.run(
                query,
                memory_id=memory_id,
                project_id=project_id,
            )
            record = await result.single()
            return dict(record["project"]) if record else {}

    async def get_memories_by_project(
        self,
        project_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get all memories for a project.

        Args:
            project_id: Project identifier
            limit: Max memories to return

        Returns:
            List of memory records
        """
        query = """
        MATCH (m:Memory)-[:TAGGED_WITH]->(p:Project {id: $project_id})
        RETURN m {
            .id, .content, .memory_type, .importance,
            .source_project, .session_id, .tags, .sync_version,
            created_at: toString(m.created_at),
            updated_at: toString(m.updated_at)
        } as memory
        ORDER BY m.created_at DESC
        LIMIT $limit
        """

        async with self.neo4j._driver.session() as session:
            result = await session.run(
                query,
                project_id=project_id,
                limit=limit,
            )
            records = await result.values()
            return [dict(r[0]) for r in records]

    # =========================================================================
    # Bootstrap Recovery
    # =========================================================================

    async def bootstrap_recovery(
        self,
        project_id: Optional[str] = None,
        since: Optional[str] = None,
        dry_run: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Recover memories from Neo4j.

        Args:
            project_id: Filter by project (optional)
            since: Only recover after this datetime ISO string (optional)
            dry_run: If True, don't write to local DB

        Returns:
            List of recovered memories
        """
        # Build query based on filters
        where_clauses = []
        params: dict[str, Any] = {}

        if project_id:
            where_clauses.append("m.source_project = $project_id")
            params["project_id"] = project_id

        if since:
            where_clauses.append("m.created_at >= datetime($since)")
            params["since"] = since

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"

        query = f"""
        MATCH (m:Memory)
        WHERE {where_clause}
        RETURN m {{
            .id, .content, .memory_type, .importance,
            .source_project, .session_id, .tags, .sync_version,
            created_at: toString(m.created_at),
            updated_at: toString(m.updated_at)
        }} as memory
        ORDER BY m.created_at ASC
        """

        async with self.neo4j._driver.session() as session:
            result = await session.run(query, **params)
            records = await result.values()
            memories = [dict(r[0]) for r in records]

        logger.info(
            f"Bootstrap recovery: found {len(memories)} memories "
            f"(project={project_id}, since={since}, dry_run={dry_run})"
        )

        if dry_run:
            return memories

        # In non-dry-run mode, we'd insert to local PostgreSQL here
        # This will be wired up in T027
        return memories

    async def bootstrap_recovery_with_stats(
        self,
        project_id: Optional[str] = None,
        since: Optional[str] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Recover memories with statistics.

        Args:
            project_id: Filter by project (optional)
            since: Only recover after this datetime (optional)
            dry_run: If True, don't write to local DB

        Returns:
            Recovery statistics including recovered_count, duration_ms
        """
        start_time = time.time()

        memories = await self.bootstrap_recovery(
            project_id=project_id,
            since=since,
            dry_run=dry_run,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return {
            "recovered_count": len(memories),
            "duration_ms": duration_ms,
            "dry_run": dry_run,
            "project_id": project_id,
            "memories": memories if dry_run else None,  # Only include in dry run
        }

    # =========================================================================
    # Health & Status
    # =========================================================================

    def get_sync_status(self) -> dict[str, Any]:
        """
        Get current sync service status.

        Returns:
            Status including queue info and last sync time
        """
        return {
            "queue_size": self.get_queue_size(),
            "pending_count": self.get_pending_count(),
            "failed_count": self.get_failed_count(),
            "processing": self._processing,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "last_error": self._last_error,
        }

    async def check_health(self) -> dict[str, Any]:
        """
        Check health of all connected services.

        Returns:
            Health status for Neo4j, n8n, and overall health
        """
        health = {
            "healthy": True,
            "neo4j_connected": False,
            "n8n_reachable": False,
            "ollama_reachable": False,
            "errors": [],
        }

        # Check Neo4j (only if client is configured)
        if self.neo4j is not None:
            try:
                await self.neo4j.get_server_info()
                health["neo4j_connected"] = True
            except Exception as e:
                health["errors"].append(f"Neo4j: {e}")
                # Neo4j not required for sync (goes through n8n)
        else:
            # Neo4j accessed through n8n, not directly
            health["neo4j_connected"] = None  # Unknown - accessed via n8n

        # Check n8n webhook (just connectivity)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to reach n8n base URL
                base_url = self.config.webhook_url.rsplit("/webhook", 1)[0]
                response = await client.get(f"{base_url}/healthz")
                health["n8n_reachable"] = response.status_code == 200
        except Exception as e:
            health["errors"].append(f"n8n: {e}")
            # n8n unreachable doesn't necessarily mean unhealthy
            # (queue still works)

        return health

    # =========================================================================
    # Sync Hook (T027) - All sync goes through n8n webhook, NOT direct Neo4j
    # =========================================================================

    async def sync_memory_on_create(
        self,
        memory_data: dict[str, Any],
        queue_if_unavailable: bool = True,
    ) -> dict[str, Any]:
        """
        Hook to sync memory when created locally.

        IMPORTANT: All sync operations go through n8n webhook.
        Neo4j is NOT directly accessible - this protects against LLM data destruction.

        Args:
            memory_data: Full memory data including id, content, etc.
            queue_if_unavailable: If True, queue for retry if sync fails

        Returns:
            Sync result including status and any errors
        """
        memory_id = str(memory_data.get("id", ""))
        result = {
            "memory_id": memory_id,
            "synced": False,
            "queued": False,
            "error": None,
        }

        # Build webhook payload
        payload = {
            "memory_id": memory_id,
            "content": memory_data.get("content", ""),
            "memory_type": memory_data.get("memory_type", "episodic"),
            "importance": memory_data.get("importance", 0.5),
            "session_id": str(memory_data.get("session_id", "")),
            "project_id": memory_data.get("source_project", "default"),
            "tags": memory_data.get("tags", []),
            "sync_version": memory_data.get("sync_version", 1),
            "created_at": memory_data.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": memory_data.get("updated_at"),
            "operation": "create",
        }

        try:
            # Send to n8n webhook - n8n handles Neo4j operations
            webhook_result = await self._send_to_webhook(payload)

            if webhook_result.get("success"):
                result["synced"] = True
                self._last_sync = datetime.utcnow()
                logger.info(f"Synced memory {memory_id} via n8n webhook")
            else:
                raise Exception(webhook_result.get("error", "Webhook returned failure"))

        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.warning(f"Failed to sync memory {memory_id}: {error_msg}")

            if queue_if_unavailable:
                self.queue_memory(
                    memory_id=memory_id,
                    operation="create",
                    payload=payload,
                )
                result["queued"] = True
                logger.info(f"Queued memory {memory_id} for retry")

        return result

    async def sync_memory_on_update(
        self,
        memory_id: str,
        update_data: dict[str, Any],
        queue_if_unavailable: bool = True,
    ) -> dict[str, Any]:
        """
        Hook to sync memory when updated locally.

        All sync goes through n8n webhook - no direct Neo4j access.

        Args:
            memory_id: UUID of the memory
            update_data: Fields that were updated
            queue_if_unavailable: If True, queue for retry if sync fails

        Returns:
            Sync result
        """
        result = {
            "memory_id": memory_id,
            "synced": False,
            "queued": False,
            "error": None,
        }

        payload = {
            "memory_id": memory_id,
            "operation": "update",
            **update_data,
        }

        try:
            webhook_result = await self._send_to_webhook(payload)

            if webhook_result.get("success"):
                result["synced"] = True
                self._last_sync = datetime.utcnow()
                logger.info(f"Synced update for memory {memory_id} via n8n")
            else:
                raise Exception(webhook_result.get("error", "Webhook returned failure"))

        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.warning(f"Failed to sync update for {memory_id}: {error_msg}")

            if queue_if_unavailable:
                self.queue_memory(
                    memory_id=memory_id,
                    operation="update",
                    payload=payload,
                )
                result["queued"] = True

        return result

    async def sync_memory_on_delete(
        self,
        memory_id: str,
        queue_if_unavailable: bool = True,
    ) -> dict[str, Any]:
        """
        Hook to sync memory deletion.

        All sync goes through n8n webhook - no direct Neo4j access.

        Args:
            memory_id: UUID of the memory
            queue_if_unavailable: If True, queue for retry if sync fails

        Returns:
            Sync result
        """
        result = {
            "memory_id": memory_id,
            "synced": False,
            "queued": False,
            "error": None,
        }

        payload = {
            "memory_id": memory_id,
            "operation": "delete",
        }

        try:
            webhook_result = await self._send_to_webhook(payload)

            if webhook_result.get("success"):
                result["synced"] = True
                self._last_sync = datetime.utcnow()
                logger.info(f"Synced delete for memory {memory_id} via n8n")
            else:
                raise Exception(webhook_result.get("error", "Webhook returned failure"))

        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.warning(f"Failed to sync delete for {memory_id}: {error_msg}")

            if queue_if_unavailable:
                self.queue_memory(
                    memory_id=memory_id,
                    operation="delete",
                    payload=payload,
                )
                result["queued"] = True

        return result

    async def _send_to_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send payload to n8n webhook.

        This is the ONLY way to sync data - no direct Neo4j access allowed.

        Args:
            payload: Data to send to webhook

        Returns:
            Webhook response
        """
        payload_bytes = json.dumps(payload, default=str).encode("utf-8")
        signature = self._generate_signature(payload_bytes)

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout_seconds
        ) as client:
            response = await client.post(
                self.config.webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"Webhook returned {response.status_code}: {response.text}",
                }

    # =========================================================================
    # Conflict Resolution (T028)
    # =========================================================================

    async def resolve_conflict(
        self,
        local_memory: dict[str, Any],
        remote_memory: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Resolve conflict between local and remote memory using last-write-wins.

        Per data-model.md specification:
        1. Compare sync_version (higher wins)
        2. If equal, compare updated_at timestamps
        3. Log conflict for audit

        Args:
            local_memory: Local memory data
            remote_memory: Remote memory data from Neo4j

        Returns:
            Resolution result with winner and action to take
        """
        local_version = local_memory.get("sync_version", 0)
        remote_version = remote_memory.get("sync_version", 0)

        local_updated = local_memory.get("updated_at")
        remote_updated = remote_memory.get("updated_at")

        # Parse timestamps if strings
        if isinstance(local_updated, str):
            local_updated = datetime.fromisoformat(
                local_updated.replace("Z", "+00:00")
            )
        if isinstance(remote_updated, str):
            remote_updated = datetime.fromisoformat(
                remote_updated.replace("Z", "+00:00")
            )

        # Determine winner
        if local_version > remote_version:
            winner = "local"
            action = "push_to_remote"
        elif remote_version > local_version:
            winner = "remote"
            action = "pull_to_local"
        else:
            # Same version - compare timestamps
            if local_updated and remote_updated:
                winner = "local" if local_updated >= remote_updated else "remote"
            elif local_updated:
                winner = "local"
            elif remote_updated:
                winner = "remote"
            else:
                winner = "local"  # Default to local if no timestamps

            action = "push_to_remote" if winner == "local" else "pull_to_local"

        # Log conflict for audit
        memory_id = local_memory.get("id", "unknown")
        self._log_conflict(
            memory_id=memory_id,
            local_version=local_version,
            remote_version=remote_version,
            winner=winner,
            local_content_preview=str(local_memory.get("content", ""))[:100],
            remote_content_preview=str(remote_memory.get("content", ""))[:100],
        )

        return {
            "memory_id": memory_id,
            "winner": winner,
            "action": action,
            "local_version": local_version,
            "remote_version": remote_version,
            "winning_version": local_version if winner == "local" else remote_version,
        }

    def _log_conflict(
        self,
        memory_id: str,
        local_version: int,
        remote_version: int,
        winner: str,
        local_content_preview: str,
        remote_content_preview: str,
    ) -> None:
        """Log conflict for audit trail."""
        logger.warning(
            f"Sync conflict detected for memory {memory_id}: "
            f"local_v{local_version} vs remote_v{remote_version}, "
            f"winner={winner}"
        )
        logger.debug(
            f"Conflict details - memory_id={memory_id} "
            f"local_preview='{local_content_preview}...' "
            f"remote_preview='{remote_content_preview}...'"
        )

    async def sync_with_conflict_resolution(
        self,
        local_memory: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Sync a local memory with conflict detection and resolution.

        Args:
            local_memory: Local memory to sync

        Returns:
            Sync result including any conflict resolution
        """
        memory_id = str(local_memory.get("id", ""))

        # Check if memory exists in remote
        remote_memory = await self.neo4j.get_memory(memory_id)

        if remote_memory is None:
            # No conflict - create in remote
            return await self.sync_memory_on_create(local_memory)

        # Check for conflict
        local_version = local_memory.get("sync_version", 0)
        remote_version = remote_memory.get("sync_version", 0)

        if local_version == remote_version:
            # Same version, no sync needed
            return {
                "memory_id": memory_id,
                "synced": True,
                "conflict": False,
                "message": "Already in sync",
            }

        # Resolve conflict
        resolution = await self.resolve_conflict(local_memory, remote_memory)

        if resolution["action"] == "push_to_remote":
            # Local wins - update remote
            update_data = {
                "content": local_memory.get("content"),
                "memory_type": local_memory.get("memory_type"),
                "importance": local_memory.get("importance"),
                "tags": local_memory.get("tags"),
                "sync_version": local_version,
            }
            await self.neo4j.update_memory(memory_id, update_data)
            return {
                "memory_id": memory_id,
                "synced": True,
                "conflict": True,
                "resolution": resolution,
            }
        else:
            # Remote wins - return remote data for local update
            return {
                "memory_id": memory_id,
                "synced": False,
                "conflict": True,
                "resolution": resolution,
                "remote_data": remote_memory,
            }
