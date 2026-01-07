"""
Remote Sync Service
Feature: 002-remote-persistence-safety
Tasks: T020, T021

Handles synchronization of memory payloads to Neo4j via n8n webhooks.
Includes queue management, retry logic, and recovery operations.

IMPORTANT: Sync operations use n8n webhooks.
"""

import hashlib
import hmac
import json
import logging
import os
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# =========================================================================
# Neo4j "Driver" (compatibility layer)
# =========================================================================

_neo4j_driver = None


def get_neo4j_driver():
    """
    Compatibility shim for services that expect a Neo4j driver.

    Returns a Graphiti-backed driver for Neo4j access.
    """
    global _neo4j_driver
    if _neo4j_driver is None:
        from api.services.webhook_neo4j_driver import WebhookNeo4jDriver

        _neo4j_driver = WebhookNeo4jDriver()
    return _neo4j_driver



async def close_neo4j_driver() -> None:
    global _neo4j_driver
    if _neo4j_driver is not None:
        await _neo4j_driver.close()
        _neo4j_driver = None

# =========================================================================
# Configuration
# =========================================================================


class SyncConfig(BaseModel):
    """Configuration for remote sync service."""

    webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_WEBHOOK_URL", "http://n8n:5678/webhook/memory/v1/ingest/message"
        ),
        description="n8n webhook URL for memory sync (ingest)",
    )
    recall_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_RECALL_URL", "http://n8n:5678/webhook/memory/v1/recall"
        ),
        description="n8n webhook URL for memory recall (query)",
    )
    traverse_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_TRAVERSE_URL", "http://n8n:5678/webhook/memory/v1/traverse"
        ),
        description="n8n webhook URL for graph traversal queries (read-only)",
    )
    cypher_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_CYPHER_URL", "http://n8n:5678/webhook/neo4j/v1/cypher"
        ),
        description="n8n webhook URL for executing vetted Cypher (read/write).",
    )
    skill_upsert_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_SKILL_UPSERT_URL", "http://n8n:5678/webhook/memory/v1/skill/upsert"
        ),
        description="n8n webhook URL for Skill upsert (write).",
    )
    skill_practice_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_SKILL_PRACTICE_URL", "http://n8n:5678/webhook/memory/v1/skill/practice"
        ),
        description="n8n webhook URL for Skill practice updates (write).",
    )
    # MoSAEIC Protocol webhooks (Neo4j-Only Architecture)
    mosaeic_capture_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_MOSAEIC_CAPTURE_URL", "http://n8n:5678/webhook/mosaeic/v1/capture/create"
        ),
        description="n8n webhook URL for MoSAEIC capture creation.",
    )
    mosaeic_profile_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_MOSAEIC_PROFILE_URL", "http://n8n:5678/webhook/mosaeic/v1/profile/initialize"
        ),
        description="n8n webhook URL for MoSAEIC profile initialization.",
    )
    mosaeic_pattern_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_MOSAEIC_PATTERN_URL", "http://n8n:5678/webhook/mosaeic/v1/pattern/detect"
        ),
        description="n8n webhook URL for MoSAEIC pattern detection.",
    )
    agent_run_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_AGENT_RUN_URL", "http://n8n:5678/webhook/memory/v1/ingest/agent-run"
        ),
        description="n8n webhook URL for persisting full agent trajectories.",
    )
    memevolve_evolve_webhook_url: str = Field(
        default_factory=lambda: os.getenv(
            "N8N_MEMEVOLVE_EVOLVE_URL", "http://n8n:5678/webhook/memevolve/v1/evolve"
        ),
        description="n8n webhook URL for triggering meta-evolution retrieval optimization.",
    )
    webhook_token: str = Field(
        default_factory=lambda: os.getenv("MEMORY_WEBHOOK_TOKEN", ""),
        description="HMAC secret for webhook authentication",
    )
    max_retries: int = Field(default=5, ge=1, le=10)
    initial_backoff_seconds: float = Field(default=1.0, ge=0.1)
    max_backoff_seconds: float = Field(default=300.0, ge=1.0)  # 5 minutes
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    queue_batch_size: int = Field(default=10, ge=1, le=100)
    request_timeout_seconds: float = Field(default=120.0, ge=5.0)


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

    Sync operations go through n8n webhooks.

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
        self._paused = False
        self._last_sync: Optional[datetime] = None
        self._last_error: Optional[str] = None

    # =========================================================================
    # Sync Control
    # =========================================================================

    def pause_sync(self) -> None:
        """Pause sync operations (items will be queued instead of sent)."""
        self._paused = True
        logger.warning("Sync operations PAUSED")

    def resume_sync(self) -> None:
        """Resume sync operations."""
        self._paused = False
        logger.info("Sync operations RESUMED")

    def is_paused(self) -> bool:
        """Check if sync is currently paused."""
        return self._paused

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
    # Cypher Execution (Webhook-only)
    # =========================================================================

    async def run_cypher(
        self,
        statement: str,
        parameters: Optional[dict[str, Any]] = None,
        *,
        mode: str = "read",
    ) -> dict[str, Any]:
        """
        Execute Cypher through n8n (never direct to Neo4j).

        The n8n workflow should enforce safety/allowlists as needed.
        """
        payload: dict[str, Any] = {
            "operation": "cypher",
            "mode": mode,
            "statement": statement,
            "parameters": parameters or {},
        }
        return await self._send_to_webhook(payload, webhook_url=self.config.cypher_webhook_url)

    # =========================================================================
    # Graph Traversal (read-only)
    # =========================================================================

    async def traverse(
        self,
        *,
        query_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run a predefined traversal query via n8n.

        query_type is mapped to a vetted Cypher query in the n8n workflow.
        """
        payload = {
            "operation": "traverse",
            "query_type": query_type,
            "params": params,
        }
        return await self._send_to_webhook(payload, webhook_url=self.config.traverse_webhook_url)

    # =========================================================================
    # Skills (procedural memory) - webhook-only write operations
    # =========================================================================

    async def skill_upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Upsert a Skill node (procedural memory) via n8n.
        """
        body = {"operation": "skill_upsert", **payload}
        return await self._send_to_webhook(body, webhook_url=self.config.skill_upsert_webhook_url)

    async def skill_practice(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Apply a practice event to a Skill node (increment practice_count, update proficiency, etc.) via n8n.
        """
        body = {"operation": "skill_practice", **payload}
        return await self._send_to_webhook(body, webhook_url=self.config.skill_practice_webhook_url)

    # =========================================================================
    # MoSAEIC Protocol (Feature 009 - Neo4j-Only Architecture)
    # =========================================================================

    async def create_capture(
        self,
        session_id: str,
        senses: Optional[dict[str, Any]] = None,
        actions: Optional[dict[str, Any]] = None,
        emotions: Optional[dict[str, Any]] = None,
        impulses: Optional[dict[str, Any]] = None,
        cognitions: Optional[dict[str, Any]] = None,
        emotional_intensity: float = 5.0,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a MoSAEIC Capture node via n8n webhook.

        Captures the 5 experiential windows:
        - senses: Interoceptive/exteroceptive sensations, body state
        - actions: Executed behaviors, motor output
        - emotions: Feelings, affective tone, valence
        - impulses: Urges, action tendencies, behavioral drives
        - cognitions: Thoughts, interpretations, predictions, core beliefs

        Auto-detects turning points (emotional_intensity >= 8.5).
        Matches cognitions.coreBelief against existing ThreatPredictions.

        Args:
            session_id: Session UUID this capture belongs to
            senses: Sensory window data
            actions: Action window data
            emotions: Emotion window data
            impulses: Impulse window data
            cognitions: Cognition window data (includes coreBelief for threat matching)
            emotional_intensity: 0-10 scale intensity rating
            context: Additional context metadata

        Returns:
            Response with capture_id, turning_point flag, and matched_threats
        """
        payload = {
            "session_id": session_id,
            "senses": senses,
            "actions": actions,
            "emotions": emotions,
            "impulses": impulses,
            "cognitions": cognitions,
            "emotional_intensity": emotional_intensity,
            "context": context or {},
        }
        return await self._send_to_webhook(
            payload, webhook_url=self.config.mosaeic_capture_webhook_url
        )

    async def initialize_profile(
        self,
        user_id: str,
        neurotype_classification: str,
        biological_model: str = "orchid",
        sensory_processing_style: str = "high_sensitivity",
        aspects: Optional[list[dict[str, Any]]] = None,
        threat_predictions: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Initialize user narrative profile from Step 1 work via n8n webhook.

        Creates:
        - User node (if not exists)
        - SelfConcept node (Orchid classification with Graphiti temporal versioning)
        - Aspect nodes (Boardroom members: Protector, Inner CEO, Inner Child, etc.)
        - ThreatPrediction nodes (If/Then statements from threat mapping)

        Args:
            user_id: User UUID
            neurotype_classification: e.g., 'analytical_empath', 'creative_sensitive'
            biological_model: 'orchid', 'dandelion', or 'tulip'
            sensory_processing_style: 'high_sensitivity', 'moderate_sensitivity', 'standard'
            aspects: List of aspect definitions:
                [{"name": "Protector", "status": "In Control", "role": "..."}]
            threat_predictions: List of threat prediction definitions:
                [{"prediction": "If I show vulnerability...",
                  "domain": "relationships",
                  "protector_directive": "Never let them see...",
                  "silenced_aspect": "Inner Child"}]

        Returns:
            Response with profile_version and created node counts
        """
        payload = {
            "user_id": user_id,
            "neurotype_classification": neurotype_classification,
            "biological_model": biological_model,
            "sensory_processing_style": sensory_processing_style,
            "aspects": aspects or [],
            "threat_predictions": threat_predictions or [],
        }
        return await self._send_to_webhook(
            payload, webhook_url=self.config.mosaeic_profile_webhook_url
        )

    async def detect_pattern(
        self,
        user_id: str,
        capture_id: str,
        belief_content: str,
        domain: str = "self",
        initial_severity: float = 0.1,
    ) -> dict[str, Any]:
        """
        Detect maladaptive patterns via n8n webhook.

        Searches for existing patterns with similar belief content.
        If found: increments recurrence_count, updates severity_score.
        If not found: creates new Pattern node.

        When recurrence_count >= 3 AND severity_score >= 0.7, sets
        intervention_status = 'queued' for therapeutic intervention.

        Args:
            user_id: User UUID for pattern search scope
            capture_id: Capture UUID to link pattern to
            belief_content: The maladaptive belief content (e.g., "I am incompetent")
            domain: Domain of the pattern ('self', 'relationships', 'work', 'world', 'health')
            initial_severity: Initial severity score for new patterns (0.0-1.0)

        Returns:
            Response with pattern_id, recurrence_count, severity_score,
            intervention_status, and needs_intervention flag
        """
        payload = {
            "user_id": user_id,
            "capture_id": capture_id,
            "belief_content": belief_content,
            "domain": domain,
            "initial_severity": initial_severity,
        }
        return await self._send_to_webhook(
            payload, webhook_url=self.config.mosaeic_pattern_webhook_url
        )

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

    # =========================================================================
    # Session Tagging & Query (T033-T036 - 002-remote-persistence-safety Phase 4)
    # =========================================================================

    async def tag_with_session(
        self,
        memory_data: dict[str, Any],
        session_id: str,
    ) -> dict[str, Any]:
        """
        Tag memory data with session_id for tracking.

        Args:
            memory_data: Memory data dictionary
            session_id: Session UUID string

        Returns:
            Memory data with session_id added
        """
        tagged = memory_data.copy()
        tagged["session_id"] = session_id
        return tagged

    async def query_by_session(
        self,
        session_id: str,
        query: Optional[str] = None,
        include_session_metadata: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Query memories by session_id.

        Args:
            session_id: Session UUID to filter by
            query: Optional keyword search within session
            include_session_metadata: Include session start/end times

        Returns:
            List of memories from the session
        """
        payload = {
            "operation": "query",
            "filters": {
                "session_id": session_id,
            },
        }

        if query:
            payload["query"] = query

        if include_session_metadata:
            payload["include_session_metadata"] = True

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("memories", [])
                else:
                    logger.error(f"Session query failed: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Session query error: {e}")
            return []

    async def query_by_date_range(
        self,
        from_date: datetime,
        to_date: datetime,
        session_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query memories by date range.

        Args:
            from_date: Start of date range
            to_date: End of date range
            session_id: Optional session filter

        Returns:
            List of memories within date range
        """
        payload = {
            "operation": "query",
            "filters": {
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat(),
            },
        }

        if session_id:
            payload["filters"]["session_id"] = session_id

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("memories", [])
                else:
                    logger.error(f"Date range query failed: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Date range query error: {e}")
            return []

    async def search_memories(
        self,
        query: str,
        include_session_attribution: bool = False,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search memories with optional session attribution.

        Args:
            query: Search query string
            include_session_attribution: Include session_id in results
            limit: Maximum results to return

        Returns:
            List of matching memories
        """
        payload = {
            "operation": "search",
            "query": query,
            "limit": limit,
            "include_session_attribution": include_session_attribution,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("memories", [])
                else:
                    logger.error(f"Memory search failed: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return []

    async def sync_memory(self, memory_data: dict[str, Any]) -> dict[str, Any]:
        """
        Sync a single memory to remote Neo4j.

        Args:
            memory_data: Memory data including id, content, type, etc.

        Returns:
            Sync result with success status
        """
        return await self.sync_memory_on_create(memory_data)

    async def get_memory_from_neo4j(self, memory_id: str) -> Optional[dict[str, Any]]:
        """
        Get a specific memory from Neo4j by ID.

        Args:
            memory_id: Memory UUID string

        Returns:
            Memory data or None if not found
        """
        payload = {
            "operation": "get",
            "memory_id": memory_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("memory")
                else:
                    return None

        except Exception as e:
            logger.error(f"Get memory error: {e}")
            return None

    # =========================================================================
    # Project Tagging & Query (T038-T041 - 002-remote-persistence-safety Phase 5)
    # =========================================================================

    async def tag_with_project(
        self,
        memory_data: dict[str, Any],
        project_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Tag memory data with project_id from current working directory.

        Args:
            memory_data: Memory data dictionary
            project_path: Optional project path (defaults to cwd)

        Returns:
            Memory data with project_id and project_name added
        """
        import os
        import hashlib

        if project_path is None:
            project_path = os.getcwd()

        project_name = os.path.basename(project_path)
        # Generate deterministic project_id from path
        project_id = hashlib.sha256(project_path.encode()).hexdigest()[:32]

        tagged = memory_data.copy()
        tagged["project_id"] = project_id
        tagged["project_name"] = project_name
        tagged["project_path"] = project_path

        return tagged

    async def query_by_project(
        self,
        project_id: str,
        query: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Query memories by project_id.

        Args:
            project_id: Project UUID to filter by
            query: Optional keyword search within project
            limit: Maximum results

        Returns:
            List of memories from the project
        """
        payload = {
            "operation": "query",
            "filters": {
                "project_id": project_id,
            },
            "limit": limit,
        }

        if query:
            payload["query"] = query

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("memories", [])
                else:
                    logger.error(f"Project query failed: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Project query error: {e}")
            return []

    async def query_all_projects(self) -> dict[str, list[dict[str, Any]]]:
        """
        Query memories from all known projects.

        Returns:
            Dictionary mapping project_name to list of memories
        """
        payload = {
            "operation": "query_all_projects",
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("projects", {})
                else:
                    logger.error(f"All projects query failed: {response.status_code}")
                    return {}

        except Exception as e:
            logger.error(f"All projects query error: {e}")
            return {}

    async def get_project_from_neo4j(self, project_id: str) -> Optional[dict[str, Any]]:
        """
        Get a Project node from Neo4j by ID.

        Args:
            project_id: Project ID

        Returns:
            Project data or None
        """
        payload = {
            "operation": "get_project",
            "project_id": project_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("project")
                else:
                    return None

        except Exception as e:
            logger.error(f"Get project error: {e}")
            return None

    async def get_project_by_name(self, project_name: str) -> Optional[dict[str, Any]]:
        """
        Get a Project node from Neo4j by name.

        Args:
            project_name: Project name

        Returns:
            Project data or None
        """
        payload = {
            "operation": "get_project_by_name",
            "project_name": project_name,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("project")
                else:
                    return None

        except Exception as e:
            logger.error(f"Get project by name error: {e}")
            return None

    async def ensure_known_projects(self, project_names: list[str]) -> None:
        """
        Ensure known projects are registered in Neo4j.

        Args:
            project_names: List of project names to register
        """
        payload = {
            "operation": "ensure_projects",
            "projects": project_names,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    logger.info(f"Registered {len(project_names)} known projects")
                else:
                    logger.error(f"Failed to register projects: {response.status_code}")

        except Exception as e:
            logger.error(f"Ensure projects error: {e}")

    # =========================================================================
    # Session Summary (T047-T048 - 002-remote-persistence-safety Phase 6)
    # =========================================================================

    async def store_session_summary(
        self,
        session_id: str,
        summary: str,
        started_at: datetime,
        ended_at: datetime,
        memory_count: int,
        project_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Store session summary in Neo4j Session node.

        Args:
            session_id: Session UUID
            summary: Generated summary text
            started_at: Session start time
            ended_at: Session end time
            memory_count: Number of memories in session
            project_id: Optional project association

        Returns:
            Result with success status
        """
        payload = {
            "session_id": session_id,
            "summary": summary,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "memory_count": memory_count,
        }

        if project_id:
            payload["project_id"] = project_id

        try:
            # Use session summary webhook endpoint
            summary_webhook_url = self.config.webhook_url.replace(
                "/memory/v1/ingest/message", "/session/summary"
            )

            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    summary_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json() if response.text else {"success": True}
                    logger.info(f"Stored session summary for {session_id}")
                    return result
                else:
                    logger.error(f"Failed to store session summary: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Webhook returned {response.status_code}",
                    }

        except Exception as e:
            logger.error(f"Store session summary error: {e}")
            return {"success": False, "error": str(e)}

    async def get_session_summary(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Get session summary from Neo4j.

        Args:
            session_id: Session UUID

        Returns:
            Session data including summary, or None if not found
        """
        payload = {
            "operation": "get_session",
            "session_id": session_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                signature = self._generate_signature(json.dumps(payload).encode())
                response = await client.post(
                    self.config.recall_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("session")
                else:
                    return None

        except Exception as e:
            logger.error(f"Get session summary error: {e}")
            return None

    async def trigger_session_summary(
        self,
        session_id: str,
        memories: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Trigger n8n workflow to generate session summary via Ollama.

        This calls the session/summary n8n workflow which:
        1. Takes session memories
        2. Generates summary via Ollama
        3. Stores summary in Neo4j Session node

        Args:
            session_id: Session UUID
            memories: List of memory objects from the session

        Returns:
            Result with generated summary
        """
        payload = {
            "session_id": session_id,
            "memories": memories,
        }

        try:
            # Use session summary webhook endpoint
            summary_webhook_url = self.config.webhook_url.replace(
                "/memory/v1/ingest/message", "/session/summary"
            )

            async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for LLM
                signature = self._generate_signature(json.dumps(payload, default=str).encode())
                response = await client.post(
                    summary_webhook_url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json() if response.text else {"success": True}
                    logger.info(f"Triggered session summary for {session_id}")
                    return result
                else:
                    logger.error(f"Failed to trigger session summary: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Webhook returned {response.status_code}: {response.text}",
                    }

        except Exception as e:
            logger.error(f"Trigger session summary error: {e}")
            return {"success": False, "error": str(e)}
