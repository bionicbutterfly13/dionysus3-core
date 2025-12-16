"""
Heartbeat Scheduler
Feature: 004-heartbeat-system
Task: T020

Asyncio-based scheduler for hourly heartbeat triggers.
Pauses automatically during user sessions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable

logger = logging.getLogger("dionysus.heartbeat_scheduler")


class SchedulerState(str, Enum):
    """State of the heartbeat scheduler."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    USER_SESSION = "user_session"


class HeartbeatScheduler:
    """
    Asyncio-based scheduler for triggering heartbeats.

    Features:
    - Configurable interval (default: 1 hour)
    - Automatic pause during user sessions
    - Manual pause/resume
    - Jitter to avoid predictable timing
    """

    def __init__(
        self,
        interval_hours: float = 1.0,
        jitter_minutes: float = 5.0,
        user_session_cooldown_minutes: float = 30.0,
    ):
        """
        Initialize the scheduler.

        Args:
            interval_hours: Hours between heartbeats
            jitter_minutes: Random jitter to add (0 to jitter_minutes)
            user_session_cooldown_minutes: Wait this long after user session ends
        """
        self._interval_hours = interval_hours
        self._jitter_minutes = jitter_minutes
        self._user_session_cooldown = user_session_cooldown_minutes
        self._state = SchedulerState.STOPPED
        self._task: asyncio.Task | None = None
        self._last_heartbeat_at: datetime | None = None
        self._next_heartbeat_at: datetime | None = None
        self._last_user_activity: datetime | None = None
        self._heartbeat_callback: Callable | None = None
        self._stop_event = asyncio.Event()

    @property
    def state(self) -> SchedulerState:
        """Get current scheduler state."""
        return self._state

    @property
    def next_heartbeat_at(self) -> datetime | None:
        """Get scheduled time for next heartbeat."""
        return self._next_heartbeat_at

    @property
    def last_heartbeat_at(self) -> datetime | None:
        """Get time of last heartbeat."""
        return self._last_heartbeat_at

    def set_heartbeat_callback(self, callback: Callable) -> None:
        """
        Set the callback to execute on heartbeat.

        Args:
            callback: Async function to call (typically HeartbeatService.heartbeat)
        """
        self._heartbeat_callback = callback

    async def start(self) -> None:
        """Start the scheduler."""
        if self._state == SchedulerState.RUNNING:
            logger.warning("Scheduler already running")
            return

        if not self._heartbeat_callback:
            raise ValueError("No heartbeat callback set. Call set_heartbeat_callback first.")

        self._state = SchedulerState.RUNNING
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Heartbeat scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        if self._state == SchedulerState.STOPPED:
            logger.warning("Scheduler already stopped")
            return

        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._state = SchedulerState.STOPPED
        self._next_heartbeat_at = None
        logger.info("Heartbeat scheduler stopped")

    async def pause(self, reason: str = "Manual pause") -> None:
        """
        Pause the scheduler.

        Args:
            reason: Reason for pausing
        """
        if self._state not in (SchedulerState.RUNNING, SchedulerState.USER_SESSION):
            logger.warning(f"Cannot pause from state: {self._state}")
            return

        self._state = SchedulerState.PAUSED
        logger.info(f"Scheduler paused: {reason}")

    async def resume(self) -> None:
        """Resume the scheduler."""
        if self._state != SchedulerState.PAUSED:
            logger.warning(f"Cannot resume from state: {self._state}")
            return

        self._state = SchedulerState.RUNNING
        logger.info("Scheduler resumed")

    def notify_user_activity(self) -> None:
        """
        Notify scheduler of user activity.

        This pauses heartbeats during active user sessions.
        """
        self._last_user_activity = datetime.utcnow()

        if self._state == SchedulerState.RUNNING:
            self._state = SchedulerState.USER_SESSION
            logger.info("User session detected, pausing heartbeats")

    def _calculate_next_heartbeat(self) -> datetime:
        """Calculate when next heartbeat should occur."""
        import random

        base_interval = timedelta(hours=self._interval_hours)
        jitter = timedelta(minutes=random.uniform(0, self._jitter_minutes))

        return datetime.utcnow() + base_interval + jitter

    def _should_skip_for_user_session(self) -> bool:
        """Check if we should skip due to recent user activity."""
        if self._last_user_activity is None:
            return False

        cooldown = timedelta(minutes=self._user_session_cooldown)
        return datetime.utcnow() - self._last_user_activity < cooldown

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        logger.info("Scheduler loop started")

        while not self._stop_event.is_set():
            try:
                # Calculate next heartbeat time
                self._next_heartbeat_at = self._calculate_next_heartbeat()
                logger.info(f"Next heartbeat scheduled for: {self._next_heartbeat_at}")

                # Wait until next heartbeat
                wait_seconds = (self._next_heartbeat_at - datetime.utcnow()).total_seconds()
                if wait_seconds > 0:
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(),
                            timeout=wait_seconds,
                        )
                        # If we get here, stop was requested
                        break
                    except asyncio.TimeoutError:
                        # Normal timeout, proceed to heartbeat
                        pass

                # Check if we should skip
                if self._state == SchedulerState.PAUSED:
                    logger.info("Heartbeat skipped: scheduler paused")
                    continue

                if self._state == SchedulerState.USER_SESSION:
                    if self._should_skip_for_user_session():
                        logger.info("Heartbeat skipped: user session active")
                        continue
                    else:
                        # User session ended, resume
                        self._state = SchedulerState.RUNNING
                        logger.info("User session ended, resuming heartbeats")

                # Execute heartbeat
                logger.info("Executing scheduled heartbeat")
                try:
                    await self._heartbeat_callback()
                    self._last_heartbeat_at = datetime.utcnow()
                except Exception as e:
                    logger.error(f"Heartbeat execution failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

        logger.info("Scheduler loop ended")

    async def trigger_now(self) -> None:
        """Trigger an immediate heartbeat (for testing/admin)."""
        if not self._heartbeat_callback:
            raise ValueError("No heartbeat callback set")

        logger.info("Manual heartbeat trigger")
        await self._heartbeat_callback()
        self._last_heartbeat_at = datetime.utcnow()

    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "state": self._state.value,
            "interval_hours": self._interval_hours,
            "last_heartbeat_at": self._last_heartbeat_at.isoformat() if self._last_heartbeat_at else None,
            "next_heartbeat_at": self._next_heartbeat_at.isoformat() if self._next_heartbeat_at else None,
            "last_user_activity": self._last_user_activity.isoformat() if self._last_user_activity else None,
            "user_session_cooldown_minutes": self._user_session_cooldown,
        }


# =============================================================================
# Service Factory
# =============================================================================

_scheduler_instance: HeartbeatScheduler | None = None


def get_heartbeat_scheduler() -> HeartbeatScheduler:
    """Get or create the HeartbeatScheduler singleton."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = HeartbeatScheduler()
    return _scheduler_instance


async def start_heartbeat_scheduler() -> HeartbeatScheduler:
    """
    Start the heartbeat scheduler with default configuration.

    Returns:
        Running HeartbeatScheduler instance
    """
    from api.services.heartbeat_service import get_heartbeat_service

    scheduler = get_heartbeat_scheduler()
    heartbeat_service = get_heartbeat_service()

    scheduler.set_heartbeat_callback(heartbeat_service.heartbeat)
    await scheduler.start()

    return scheduler
