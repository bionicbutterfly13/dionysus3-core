"""
Sync MCP Tools
Feature: 002-remote-persistence-safety
Phase 8: MCP Tools & Polish

T055: Create sync_now MCP tool
T056: Create get_sync_status MCP tool

MCP tools for memory synchronization and safety operations.
"""

import logging
from typing import Any, Optional

from api.services.remote_sync import RemoteSyncService
from api.services.destruction_detector import get_destruction_detector

logger = logging.getLogger(__name__)


# Global sync service instance
_sync_service: Optional[RemoteSyncService] = None


def get_sync_service() -> RemoteSyncService:
    """Get or create sync service instance."""
    global _sync_service
    if _sync_service is None:
        _sync_service = RemoteSyncService()
    return _sync_service


# =============================================================================
# Tool: sync_now (T055)
# =============================================================================

async def sync_now_tool(
    force: bool = False,
    batch_size: Optional[int] = None,
) -> dict[str, Any]:
    """
    Immediately process pending sync queue.

    Use this tool when you want to ensure all pending memory operations
    are synchronized to the remote Neo4j database via n8n webhook.

    Args:
        force: If True, process even if sync is paused (not recommended)
        batch_size: Maximum items to process (defaults to config)

    Returns:
        Sync result with counts of processed, succeeded, failed items
    """
    sync_service = get_sync_service()

    # Check if paused
    if sync_service.is_paused() and not force:
        return {
            "success": False,
            "error": "Sync is currently paused (possible destruction detection). Use force=True to override.",
            "paused": True,
            "queue_size": sync_service.get_queue_size(),
        }

    # Process queue
    result = await sync_service.process_queue(batch_size=batch_size)

    return {
        "success": result.get("failed", 0) == 0,
        "processed": result.get("processed", 0),
        "succeeded": result.get("succeeded", 0),
        "failed": result.get("failed", 0),
        "requeued": result.get("requeued", 0),
        "errors": result.get("errors", []),
        "queue_remaining": sync_service.get_queue_size(),
    }


# =============================================================================
# Tool: get_sync_status (T056)
# =============================================================================

async def get_sync_status_tool() -> dict[str, Any]:
    """
    Get current status of the memory sync system.

    Returns information about:
    - Queue size and pending items
    - Last sync timestamp
    - Pause status
    - Destruction detection status
    - Health of n8n connectivity

    Returns:
        Comprehensive sync status information
    """
    sync_service = get_sync_service()
    detector = get_destruction_detector()

    # Get basic sync status
    status = sync_service.get_sync_status()

    # Add destruction detection status
    status["destruction_detection"] = {
        "active": detector.is_destruction_detected(),
        "delete_count_in_window": detector.get_delete_count_in_window(),
        "threshold": detector.delete_threshold,
        "window_seconds": detector.window_seconds,
    }

    # Get active alert if any
    alert = detector.get_active_alert()
    if alert:
        status["destruction_detection"]["alert"] = alert

    # Add pause status
    status["paused"] = sync_service.is_paused()

    # Check health
    try:
        health = await sync_service.check_health()
        status["health"] = health
    except Exception as e:
        status["health"] = {"error": str(e)}

    return status


# =============================================================================
# Tool: pause_sync
# =============================================================================

async def pause_sync_tool(reason: Optional[str] = None) -> dict[str, Any]:
    """
    Pause sync operations.

    New sync operations will be queued instead of sent to remote.
    Use this when you detect issues or need to investigate.

    Args:
        reason: Optional reason for pausing sync

    Returns:
        Confirmation of pause status
    """
    sync_service = get_sync_service()
    sync_service.pause_sync()

    if reason:
        logger.warning(f"Sync paused: {reason}")

    return {
        "success": True,
        "paused": True,
        "reason": reason,
        "queue_size": sync_service.get_queue_size(),
    }


# =============================================================================
# Tool: resume_sync
# =============================================================================

async def resume_sync_tool(process_queue: bool = True) -> dict[str, Any]:
    """
    Resume sync operations after pause.

    Args:
        process_queue: If True, immediately process pending queue

    Returns:
        Result including optional queue processing results
    """
    sync_service = get_sync_service()
    sync_service.resume_sync()

    result = {
        "success": True,
        "paused": False,
        "queue_size": sync_service.get_queue_size(),
    }

    if process_queue and sync_service.get_queue_size() > 0:
        queue_result = await sync_service.process_queue()
        result["queue_processed"] = queue_result

    return result


# =============================================================================
# Tool: check_destruction
# =============================================================================

async def check_destruction_tool() -> dict[str, Any]:
    """
    Check for destruction patterns (rapid memory deletion).

    This tool detects if there's been unusual deletion activity
    that might indicate an LLM attempting to wipe memory.

    Returns:
        Destruction detection status and recent activity
    """
    detector = get_destruction_detector()

    is_detected = detector.is_destruction_detected()
    alert = detector.get_active_alert()

    result = {
        "destruction_detected": is_detected,
        "delete_count": detector.get_delete_count_in_window(),
        "threshold": detector.delete_threshold,
        "window_seconds": detector.window_seconds,
    }

    if alert:
        result["alert"] = alert
        result["recently_deleted_ids"] = detector.get_recently_deleted_ids()[-20:]

    return result


# =============================================================================
# Tool: acknowledge_destruction_alert
# =============================================================================

async def acknowledge_destruction_alert_tool() -> dict[str, Any]:
    """
    Acknowledge a destruction detection alert.

    Call this after investigating and confirming the deletions were intentional.

    Returns:
        Acknowledgment status
    """
    detector = get_destruction_detector()

    acknowledged = detector.acknowledge_alert()

    return {
        "success": acknowledged,
        "message": "Alert acknowledged" if acknowledged else "No active alert to acknowledge",
    }


# =============================================================================
# Tool: bootstrap_recovery
# =============================================================================

async def bootstrap_recovery_tool(
    project_id: Optional[str] = None,
    since: Optional[str] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Recover memories from remote Neo4j via n8n.

    Use this tool to restore local memory after database loss or
    when starting fresh on a new machine.

    Args:
        project_id: Filter recovery to specific project (optional)
        since: Only recover memories after this ISO datetime (optional)
        dry_run: If True, preview what would be recovered without writing

    Returns:
        Recovery results including count and duration
    """
    sync_service = get_sync_service()

    result = await sync_service.bootstrap_recovery_with_stats(
        project_id=project_id,
        since=since,
        dry_run=dry_run,
    )

    return {
        "success": True,
        "recovered_count": result.get("recovered_count", 0),
        "duration_ms": result.get("duration_ms", 0),
        "dry_run": dry_run,
        "project_id": project_id,
        "since": since,
        "memories": result.get("memories") if dry_run else None,
    }


# =============================================================================
# Tool Definitions for MCP Registration
# =============================================================================

SYNC_TOOLS = [
    {
        "name": "sync_now",
        "description": "Immediately process pending memory sync queue",
        "function": sync_now_tool,
        "parameters": {
            "type": "object",
            "properties": {
                "force": {
                    "type": "boolean",
                    "description": "Override pause status and force sync",
                    "default": False,
                },
                "batch_size": {
                    "type": "integer",
                    "description": "Maximum items to process",
                },
            },
        },
    },
    {
        "name": "get_sync_status",
        "description": "Get current status of memory sync system",
        "function": get_sync_status_tool,
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "pause_sync",
        "description": "Pause sync operations (items will be queued)",
        "function": pause_sync_tool,
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for pausing sync",
                },
            },
        },
    },
    {
        "name": "resume_sync",
        "description": "Resume sync operations after pause",
        "function": resume_sync_tool,
        "parameters": {
            "type": "object",
            "properties": {
                "process_queue": {
                    "type": "boolean",
                    "description": "Process pending queue immediately",
                    "default": True,
                },
            },
        },
    },
    {
        "name": "check_destruction",
        "description": "Check for rapid memory deletion patterns",
        "function": check_destruction_tool,
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "acknowledge_destruction_alert",
        "description": "Acknowledge a destruction detection alert",
        "function": acknowledge_destruction_alert_tool,
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "bootstrap_recovery",
        "description": "Recover memories from remote Neo4j",
        "function": bootstrap_recovery_tool,
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Filter to specific project",
                },
                "since": {
                    "type": "string",
                    "description": "Only recover after this ISO datetime",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview without writing",
                    "default": True,
                },
            },
        },
    },
]
