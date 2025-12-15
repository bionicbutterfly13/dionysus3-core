"""
Remote Sync Service
Feature: 002-remote-persistence-safety
Tasks: T020, T021

Handles synchronization between local PostgreSQL and remote Neo4j via n8n webhooks.
Includes queue management, retry logic, and recovery operations.

IMPORTANT: All Neo4j access goes through n8n webhooks. No direct Neo4j connections.
"""

import hashlib
import hmac
import json
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =========================================================================
# Configuration
# =========================================================================


class SyncConfig(BaseModel):
    """Configuration for remote sync service."""

    webhook_url: str = Field(
        default="http://localhost:5678/webhook/memory/v1/ingest/message",
        description="n8n webhook URL for memory sync (ingest)",
    )
    recall_webhook_url: str = Field(
        default="http://localhost:5678/webhook/memory/v1/recall",
        description="n8n webhook URL for memory recall (query)",
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
    Service for synchronizing memories to remote Neo4j via n8n webhooks.

    All Neo4j access goes through n8n - no direct database connections.

    Features:
    - Queue management for pending sync operations
    - Exponential backoff retry logic
    - Bootstrap recovery via n8n recall webhook

    Usage:
        sync_service = RemoteSyncService(config)
        await sync_service.sync_memory_on_create(memory_data)
        await sync_service.process_queue()
    """

    def __init__(self, config: Optional[SyncConfig] = None):
        """
        Initialize sync service.

        Args:
            config: Sync configuration (uses defaults if not provided)
        """
        self.config = config or SyncConfig()
        self._queue: deque[QueueItem] = deque()
        self._processing = False
        self._last_sync: Optional[datetime] = None
        self._last_error: Optional[str] = None

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
        Sync a single queue item to remote via webhook.

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
                return response.json() if response.text else {"success": True}
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
        Check health of n8n webhook connectivity.

        Returns:
            Health status for n8n
        """
        health = {
            "healthy": True,
            "n8n_reachable": False,
            "errors": [],
        }

        # Check n8n webhook connectivity
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                base_url = self.config.webhook_url.rsplit("/webhook", 1)[0]
                response = await client.get(f"{base_url}/healthz")
                health["n8n_reachable"] = response.status_code == 200
        except Exception as e:
            health["errors"].append(f"n8n: {e}")
            health["healthy"] = False

        return health

    # =========================================================================
    # Sync Hooks - All sync goes through n8n webhook
    # =========================================================================

    async def sync_memory_on_create(
        self,
        memory_data: dict[str, Any],
        queue_if_unavailable: bool = True,
    ) -> dict[str, Any]:
        """
        Hook to sync memory when created locally.

        All sync operations go through n8n webhook.

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
            webhook_result = await self._send_to_webhook(payload)

            if webhook_result.get("success", True):  # Empty response = success
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

            if webhook_result.get("success", True):
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

            if webhook_result.get("success", True):
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

    async def _send_to_webhook(
        self, payload: dict[str, Any], webhook_url: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Send payload to n8n webhook.

        Args:
            payload: Data to send to webhook
            webhook_url: Override webhook URL (defaults to config.webhook_url)

        Returns:
            Webhook response
        """
        url = webhook_url or self.config.webhook_url
        payload_bytes = json.dumps(payload, default=str).encode("utf-8")
        signature = self._generate_signature(payload_bytes)

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout_seconds
        ) as client:
            response = await client.post(
                url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
            )

            if response.status_code == 200:
                return response.json() if response.text else {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Webhook returned {response.status_code}: {response.text}",
                }

    # =========================================================================
    # Bootstrap Recovery - via n8n recall webhook
    # =========================================================================

    async def bootstrap_recovery(
        self,
        project_id: Optional[str] = None,
        since: Optional[str] = None,
        dry_run: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Recover memories from Neo4j via n8n recall webhook.

        Args:
            project_id: Filter by project (optional)
            since: Only recover after this datetime ISO string (optional)
            dry_run: If True, don't write to local DB

        Returns:
            List of recovered memories
        """
        # Build recall query payload
        payload = {
            "operation": "recall",
            "project_id": project_id,
            "since": since,
            "limit": 1000,  # Reasonable batch size
        }

        try:
            result = await self._send_to_webhook(
                payload, webhook_url=self.config.recall_webhook_url
            )

            memories = result.get("memories", [])

            logger.info(
                f"Bootstrap recovery: found {len(memories)} memories "
                f"(project={project_id}, since={since}, dry_run={dry_run})"
            )

            return memories

        except Exception as e:
            logger.error(f"Bootstrap recovery failed: {e}")
            return []

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
            "memories": memories if dry_run else None,
        }
