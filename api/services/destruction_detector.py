"""
Destruction Detector Service
Feature: 002-remote-persistence-safety
Phase 7, User Story 5: LLM Destruction Detection & Archon Integration

T051: Detect rapid delete patterns that may indicate LLM memory wipeout.
T052: Alert logging and optional n8n webhook notification.

Monitors delete operations and triggers alerts when threshold exceeded:
- Default: >10 deletes in 60 seconds
- Configurable threshold and window

IMPORTANT: This is a safety mechanism to detect when an LLM may be
attempting to wipe memory. It provides early warning and can pause sync.
"""

import hashlib
import hmac
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_DELETE_THRESHOLD = 10
DEFAULT_WINDOW_SECONDS = 60


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class DeleteEvent:
    """Record of a single delete operation."""
    memory_id: str
    timestamp: float
    source: Optional[str] = None  # e.g., "api", "mcp", "hook"


@dataclass
class DestructionAlert:
    """Alert generated when destruction is detected."""
    timestamp: datetime
    delete_count: int
    window_seconds: int
    recent_ids: list[str]
    acknowledged: bool = False
    webhook_sent: bool = False


# =============================================================================
# Destruction Detector Service
# =============================================================================

class DestructionDetector:
    """
    Detects rapid deletion patterns that may indicate LLM memory wipeout.

    Features:
    - Sliding window tracking of delete operations
    - Configurable threshold and window size
    - Alert logging and optional webhook notification
    - State export/import for persistence

    Usage:
        detector = DestructionDetector()
        detector.record_delete(memory_id)
        if detector.is_destruction_detected():
            alert = detector.get_active_alert()
            # Take action: pause sync, notify user, etc.
    """

    def __init__(
        self,
        delete_threshold: int = DEFAULT_DELETE_THRESHOLD,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        webhook_url: Optional[str] = None,
        webhook_token: Optional[str] = None,
    ):
        """
        Initialize destruction detector.

        Args:
            delete_threshold: Number of deletes to trigger alert
            window_seconds: Time window in seconds
            webhook_url: Optional n8n webhook URL for alerts
            webhook_token: HMAC secret for webhook authentication
        """
        self.delete_threshold = delete_threshold
        self.window_seconds = window_seconds
        self._webhook_url = webhook_url
        self._webhook_token = webhook_token or ""

        # Sliding window of delete events
        self._delete_events: deque[DeleteEvent] = deque()

        # Active alert (if any)
        self._active_alert: Optional[DestructionAlert] = None

        # All deleted memory IDs (for recovery)
        self._deleted_ids: list[str] = []

        logger.info(
            f"DestructionDetector initialized: "
            f"threshold={delete_threshold}, window={window_seconds}s"
        )

    # =========================================================================
    # Event Recording
    # =========================================================================

    def record_delete(
        self,
        memory_id: str,
        source: Optional[str] = None
    ) -> None:
        """
        Record a delete operation.

        Args:
            memory_id: ID of deleted memory
            source: Source of delete (api, mcp, hook)
        """
        event = DeleteEvent(
            memory_id=memory_id,
            timestamp=time.time(),
            source=source
        )
        self._delete_events.append(event)
        self._deleted_ids.append(memory_id)

        # Prune old events outside window
        self._prune_old_events()

        logger.debug(f"Recorded delete: {memory_id} (source={source})")

    def _prune_old_events(self) -> None:
        """Remove events outside the sliding window."""
        cutoff = time.time() - self.window_seconds
        while self._delete_events and self._delete_events[0].timestamp < cutoff:
            self._delete_events.popleft()

    def clear_old_events(self, seconds_ago: int) -> None:
        """
        Clear events older than specified time.

        Args:
            seconds_ago: Clear events older than this many seconds
        """
        cutoff = time.time() - seconds_ago
        while self._delete_events and self._delete_events[0].timestamp < cutoff:
            self._delete_events.popleft()

    # =========================================================================
    # Detection Logic
    # =========================================================================

    def is_destruction_detected(self) -> bool:
        """
        Check if deletion rate exceeds threshold.

        Returns:
            True if destruction pattern detected
        """
        self._prune_old_events()
        return len(self._delete_events) >= self.delete_threshold

    def get_delete_count_in_window(self) -> int:
        """Get current delete count within window."""
        self._prune_old_events()
        return len(self._delete_events)

    # =========================================================================
    # Alert Management
    # =========================================================================

    def check_and_alert(self) -> Optional[DestructionAlert]:
        """
        Check for destruction and create alert if detected.

        Returns:
            Alert if destruction detected, None otherwise
        """
        if not self.is_destruction_detected():
            return None

        # Create alert if not already active
        if self._active_alert is None:
            recent_ids = [e.memory_id for e in self._delete_events]
            self._active_alert = DestructionAlert(
                timestamp=datetime.utcnow(),
                delete_count=len(self._delete_events),
                window_seconds=self.window_seconds,
                recent_ids=recent_ids[-20:],  # Keep last 20 IDs
            )

            # Log warning
            logger.warning(
                f"⚠️ DESTRUCTION DETECTED: {len(self._delete_events)} deletes "
                f"in {self.window_seconds}s window. "
                f"IDs: {recent_ids[:5]}..."
            )

        return self._active_alert

    async def check_and_alert_async(self) -> dict[str, Any]:
        """
        Async version that also triggers webhook.

        Returns:
            Result with alert status and webhook trigger status
        """
        result = {
            "destruction_detected": False,
            "alert": None,
            "webhook_triggered": False,
            "webhook_queued": False,
        }

        alert = self.check_and_alert()
        if alert:
            result["destruction_detected"] = True
            result["alert"] = {
                "timestamp": alert.timestamp.isoformat(),
                "delete_count": alert.delete_count,
                "window_seconds": alert.window_seconds,
                "recent_ids": alert.recent_ids,
            }

            # Trigger webhook if configured
            if self._webhook_url and not alert.webhook_sent:
                webhook_result = await self._send_webhook_alert()
                result["webhook_triggered"] = webhook_result.get("success", False)
                result["webhook_queued"] = webhook_result.get("queued", False)
                if webhook_result.get("success"):
                    alert.webhook_sent = True

        return result

    def get_active_alert(self) -> Optional[dict[str, Any]]:
        """
        Get currently active alert as dictionary.

        Returns:
            Alert data or None
        """
        if self._active_alert is None:
            return None

        return {
            "timestamp": self._active_alert.timestamp.isoformat(),
            "delete_count": self._active_alert.delete_count,
            "window_seconds": self._active_alert.window_seconds,
            "recent_ids": self._active_alert.recent_ids,
            "acknowledged": self._active_alert.acknowledged,
            "webhook_sent": self._active_alert.webhook_sent,
        }

    def acknowledge_alert(self) -> bool:
        """
        Acknowledge the active alert.

        Returns:
            True if alert was acknowledged, False if no alert
        """
        if self._active_alert:
            self._active_alert.acknowledged = True
            logger.info("Destruction alert acknowledged")
            return True
        return False

    def clear_alert(self) -> None:
        """Clear the active alert."""
        self._active_alert = None
        logger.info("Destruction alert cleared")

    # =========================================================================
    # Webhook Notification (T052)
    # =========================================================================

    def set_webhook_url(self, url: str, token: Optional[str] = None) -> None:
        """Configure webhook URL for alerts."""
        self._webhook_url = url
        if token:
            self._webhook_token = token

    def get_alert_payload(self) -> dict[str, Any]:
        """
        Get webhook payload for current alert.

        Returns:
            Payload dictionary
        """
        recent_ids = [e.memory_id for e in self._delete_events]

        return {
            "event_type": "destruction_detected",
            "timestamp": datetime.utcnow().isoformat(),
            "delete_count": len(self._delete_events),
            "window_seconds": self.window_seconds,
            "threshold": self.delete_threshold,
            "recent_memory_ids": recent_ids[-20:],
            "severity": "critical" if len(self._delete_events) > self.delete_threshold * 2 else "warning",
        }

    async def _send_webhook_alert(self) -> dict[str, Any]:
        """
        Send alert to configured webhook.

        Returns:
            Result with success status
        """
        if not self._webhook_url:
            return {"success": False, "error": "No webhook URL configured"}

        payload = self.get_alert_payload()
        payload_bytes = json.dumps(payload).encode("utf-8")

        # Generate HMAC signature
        signature = "sha256=" + hmac.new(
            key=self._webhook_token.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self._webhook_url,
                    content=payload_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                    },
                )

                if response.status_code == 200:
                    logger.info(f"Destruction alert sent to webhook: {self._webhook_url}")
                    return {"success": True}
                else:
                    logger.error(f"Webhook failed: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Webhook returned {response.status_code}",
                    }

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"success": False, "queued": True, "error": str(e)}

    # =========================================================================
    # Recovery Support
    # =========================================================================

    def get_recently_deleted_ids(self) -> list[str]:
        """
        Get all recently deleted memory IDs for potential recovery.

        Returns:
            List of memory IDs
        """
        return list(self._deleted_ids)

    def clear_deleted_history(self) -> None:
        """Clear the deleted ID history."""
        self._deleted_ids.clear()

    # =========================================================================
    # State Persistence
    # =========================================================================

    def export_state(self) -> dict[str, Any]:
        """
        Export detector state for persistence.

        Returns:
            Serializable state dictionary
        """
        return {
            "delete_threshold": self.delete_threshold,
            "window_seconds": self.window_seconds,
            "events": [
                {
                    "memory_id": e.memory_id,
                    "timestamp": e.timestamp,
                    "source": e.source,
                }
                for e in self._delete_events
            ],
            "deleted_ids": self._deleted_ids[-100:],  # Keep last 100
            "active_alert": self.get_active_alert(),
            "exported_at": datetime.utcnow().isoformat(),
        }

    def import_state(self, state: dict[str, Any]) -> None:
        """
        Import detector state.

        Args:
            state: Previously exported state
        """
        if "delete_threshold" in state:
            self.delete_threshold = state["delete_threshold"]
        if "window_seconds" in state:
            self.window_seconds = state["window_seconds"]

        # Restore events (within window)
        now = time.time()
        for event_data in state.get("events", []):
            if now - event_data["timestamp"] < self.window_seconds:
                event = DeleteEvent(
                    memory_id=event_data["memory_id"],
                    timestamp=event_data["timestamp"],
                    source=event_data.get("source"),
                )
                self._delete_events.append(event)

        # Restore deleted IDs
        self._deleted_ids = state.get("deleted_ids", [])

        logger.info(f"Imported destruction detector state: {len(self._delete_events)} events")


# =============================================================================
# Global Instance (Optional)
# =============================================================================

_global_detector: Optional[DestructionDetector] = None


def get_destruction_detector() -> DestructionDetector:
    """Get or create global destruction detector instance."""
    global _global_detector
    if _global_detector is None:
        _global_detector = DestructionDetector()
    return _global_detector
