"""
Sync Logging Configuration
Feature: 002-remote-persistence-safety
Phase 8, Task T058: Structured logging for all sync operations

Provides structured logging for:
- Memory sync operations (create, update, delete)
- Queue processing events
- Destruction detection alerts
- Recovery operations
- n8n webhook interactions

Uses JSON structured logging for easy parsing and monitoring.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Optional


# =============================================================================
# Custom JSON Formatter
# =============================================================================

class SyncJSONFormatter(logging.Formatter):
    """JSON formatter for structured sync logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from record
        if hasattr(record, "sync_operation"):
            log_data["sync_operation"] = record.sync_operation
        if hasattr(record, "memory_id"):
            log_data["memory_id"] = record.memory_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "project_id"):
            log_data["project_id"] = record.project_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "queue_size"):
            log_data["queue_size"] = record.queue_size
        if hasattr(record, "error"):
            log_data["error"] = record.error
        if hasattr(record, "webhook_url"):
            log_data["webhook_url"] = record.webhook_url
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# =============================================================================
# Logger Configuration
# =============================================================================

def configure_sync_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for sync operations.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON formatting for structured logs
        log_file: Optional file path for log output

    Returns:
        Configured logger
    """
    logger = logging.getLogger("dionysus.sync")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    if json_format:
        formatter = SyncJSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# =============================================================================
# Structured Logging Helpers
# =============================================================================

class SyncLogger:
    """Helper class for structured sync logging."""

    def __init__(self, logger_name: str = "dionysus.sync"):
        self.logger = logging.getLogger(logger_name)

    def log_sync_start(
        self,
        operation: str,
        memory_id: str,
        **kwargs,
    ) -> None:
        """Log start of sync operation."""
        self.logger.info(
            f"sync.{operation}.start",
            extra={
                "sync_operation": operation,
                "memory_id": memory_id,
                **kwargs,
            },
        )

    def log_sync_success(
        self,
        operation: str,
        memory_id: str,
        duration_ms: float,
        **kwargs,
    ) -> None:
        """Log successful sync operation."""
        self.logger.info(
            f"sync.{operation}.success",
            extra={
                "sync_operation": operation,
                "memory_id": memory_id,
                "duration_ms": duration_ms,
                **kwargs,
            },
        )

    def log_sync_failure(
        self,
        operation: str,
        memory_id: str,
        error: str,
        duration_ms: Optional[float] = None,
        **kwargs,
    ) -> None:
        """Log failed sync operation."""
        self.logger.error(
            f"sync.{operation}.failure",
            extra={
                "sync_operation": operation,
                "memory_id": memory_id,
                "error": error,
                "duration_ms": duration_ms,
                **kwargs,
            },
        )

    def log_queue_event(
        self,
        event: str,
        queue_size: int,
        **kwargs,
    ) -> None:
        """Log queue-related event."""
        self.logger.info(
            f"sync.queue.{event}",
            extra={
                "sync_operation": f"queue.{event}",
                "queue_size": queue_size,
                **kwargs,
            },
        )

    def log_webhook_call(
        self,
        webhook_url: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Log webhook call."""
        level = logging.INFO if status_code == 200 else logging.WARNING

        self.logger.log(
            level,
            f"sync.webhook.{'success' if status_code == 200 else 'failure'}",
            extra={
                "sync_operation": "webhook",
                "webhook_url": webhook_url,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "error": error,
                **kwargs,
            },
        )

    def log_destruction_detected(
        self,
        delete_count: int,
        window_seconds: int,
        recent_ids: list[str],
        **kwargs,
    ) -> None:
        """Log destruction detection alert."""
        self.logger.critical(
            "sync.destruction.detected",
            extra={
                "sync_operation": "destruction_detection",
                "delete_count": delete_count,
                "window_seconds": window_seconds,
                "recent_memory_ids": recent_ids[:10],
                **kwargs,
            },
        )

    def log_recovery_event(
        self,
        event: str,
        recovered_count: int = 0,
        duration_ms: Optional[float] = None,
        **kwargs,
    ) -> None:
        """Log recovery operation."""
        self.logger.info(
            f"sync.recovery.{event}",
            extra={
                "sync_operation": f"recovery.{event}",
                "recovered_count": recovered_count,
                "duration_ms": duration_ms,
                **kwargs,
            },
        )


# =============================================================================
# Global Sync Logger Instance
# =============================================================================

_sync_logger: Optional[SyncLogger] = None


def get_sync_logger() -> SyncLogger:
    """Get or create global sync logger."""
    global _sync_logger
    if _sync_logger is None:
        configure_sync_logging()
        _sync_logger = SyncLogger()
    return _sync_logger
