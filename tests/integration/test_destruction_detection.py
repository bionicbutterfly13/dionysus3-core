"""
Integration Tests: LLM Destruction Detection
Feature: 002-remote-persistence-safety
Phase 7, User Story 5: LLM Destruction Detections test for LLM destruction detection

TDD Test - Write FIRST, verify FAILS before implementation.

Tests that rapid deletion patterns (>10 deletes in 60s) trigger alerts.
"""

import asyncio
import time
import uuid
from datetime import datetime

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def destruction_detector():
    """Get DestructionDetector instance."""
    from api.services.destruction_detector import DestructionDetector
    return DestructionDetector()


@pytest.fixture
def sync_service():
    """Get RemoteSyncService instance."""
    from api.services.remote_sync import RemoteSyncService
    return RemoteSyncService()


# =============================================================================
# T049: Destruction Detection Tests
# =============================================================================

class TestDestructionDetectionThreshold:
    """Test destruction detection threshold logic."""

    async def test_rapid_deletes_trigger_alert(self, destruction_detector):
        """Test that >10 deletes in 60s triggers alert."""
        # Record 11 deletes in rapid succession
        for i in range(11):
            destruction_detector.record_delete(f"memory_{i}")

        # Should be above threshold
        assert destruction_detector.is_destruction_detected()

        # Alert should be active
        alert = destruction_detector.get_active_alert()
        assert alert is not None
        assert alert["delete_count"] >= 10
        assert alert["window_seconds"] == 60

    async def test_slow_deletes_no_alert(self, destruction_detector):
        """Test that slow deletes don't trigger alert."""
        # Record 5 deletes (below threshold)
        for i in range(5):
            destruction_detector.record_delete(f"memory_{i}")

        # Should NOT trigger alert
        assert not destruction_detector.is_destruction_detected()
        assert destruction_detector.get_active_alert() is None

    async def test_threshold_resets_after_window(self, destruction_detector):
        """Test that threshold resets after time window."""
        # Record deletes
        for i in range(8):
            destruction_detector.record_delete(f"memory_{i}")

        # Not yet at threshold
        assert not destruction_detector.is_destruction_detected()

        # Simulate time passing (clear old events)
        destruction_detector.clear_old_events(seconds_ago=61)

        # Add more deletes after window reset
        for i in range(3):
            destruction_detector.record_delete(f"new_memory_{i}")

        # Still should not trigger (only 3 in new window)
        assert not destruction_detector.is_destruction_detected()

    async def test_configurable_threshold(self):
        """Test that threshold is configurable."""
        from api.services.destruction_detector import DestructionDetector

        # Create detector with lower threshold
        detector = DestructionDetector(
            delete_threshold=5,
            window_seconds=30
        )

        # Record 6 deletes (above custom threshold)
        for i in range(6):
            detector.record_delete(f"memory_{i}")

        # Should trigger with custom threshold
        assert detector.is_destruction_detected()


class TestDestructionAlertLogging:
    """Test alert logging and notifications."""

    async def test_alert_logged_on_detection(self, destruction_detector, caplog):
        """Test that alert is logged when destruction detected."""
        import logging
        caplog.set_level(logging.WARNING)

        # Trigger destruction
        for i in range(12):
            destruction_detector.record_delete(f"memory_{i}")

        # Check alert was detected
        destruction_detector.check_and_alert()

        # Verify warning was logged
        assert any("destruction" in record.message.lower() for record in caplog.records)

    async def test_alert_contains_details(self, destruction_detector):
        """Test that alert contains useful details."""
        # Record deletes with IDs
        memory_ids = [f"mem_{i}" for i in range(11)]
        for mem_id in memory_ids:
            destruction_detector.record_delete(mem_id)

        destruction_detector.check_and_alert()
        alert = destruction_detector.get_active_alert()

        assert alert is not None
        assert "timestamp" in alert
        assert "delete_count" in alert
        assert "recent_ids" in alert
        assert len(alert["recent_ids"]) > 0


class TestDestructionWebhook:
    """Test webhook notification for destruction alerts."""

    async def test_webhook_triggered_on_alert(self, destruction_detector):
        """Test that n8n webhook is triggered on destruction alert."""
        # Configure webhook
        destruction_detector.set_webhook_url("http://localhost:5678/webhook/destruction-alert")

        # Trigger destruction
        for i in range(11):
            destruction_detector.record_delete(f"memory_{i}")

        # Check and alert (should trigger webhook)
        result = await destruction_detector.check_and_alert_async()

        # Webhook should have been called (or queued if unavailable)
        assert result.get("webhook_triggered") or result.get("webhook_queued")

    async def test_webhook_payload_structure(self, destruction_detector):
        """Test webhook payload has correct structure."""
        destruction_detector.set_webhook_url("http://localhost:5678/webhook/destruction-alert")

        # Record deletes
        for i in range(11):
            destruction_detector.record_delete(f"memory_{i}")

        # Get payload that would be sent
        payload = destruction_detector.get_alert_payload()

        assert "event_type" in payload
        assert payload["event_type"] == "destruction_detected"
        assert "timestamp" in payload
        assert "delete_count" in payload
        assert "window_seconds" in payload
        assert "recent_memory_ids" in payload


class TestIntegrationWithSync:
    """Test destruction detection integrated with sync service."""

    async def test_sync_delete_triggers_detection(self, sync_service, destruction_detector):
        """Test that sync_memory_on_delete records with detector."""
        # Create memories first
        memory_ids = []
        for i in range(12):
            memory_id = str(uuid.uuid4())
            memory_ids.append(memory_id)

        # Rapidly delete memories
        for memory_id in memory_ids:
            await sync_service.sync_memory_on_delete(
                memory_id=memory_id,
                queue_if_unavailable=True
            )
            # Record with detector
            destruction_detector.record_delete(memory_id)

        # Should trigger alert
        assert destruction_detector.is_destruction_detected()

    async def test_detection_survives_restart(self, destruction_detector):
        """Test that detection state persists across restarts."""
        # Record some deletes
        for i in range(5):
            destruction_detector.record_delete(f"memory_{i}")

        # Persist state
        state = destruction_detector.export_state()

        # Create new detector and restore state
        from api.services.destruction_detector import DestructionDetector
        new_detector = DestructionDetector()
        new_detector.import_state(state)

        # Continue recording
        for i in range(6):
            new_detector.record_delete(f"new_memory_{i}")

        # Should trigger (5 + 6 = 11 total)
        assert new_detector.is_destruction_detected()


class TestRecoveryFromDestruction:
    """Test recovery options when destruction is detected."""

    async def test_can_list_deleted_memories(self, destruction_detector):
        """Test that deleted memory IDs are available for recovery."""
        memory_ids = [f"memory_{i}" for i in range(15)]

        for mem_id in memory_ids:
            destruction_detector.record_delete(mem_id)

        # Get deleted IDs
        deleted = destruction_detector.get_recently_deleted_ids()

        # All should be recorded
        assert len(deleted) >= 15
        for mem_id in memory_ids:
            assert mem_id in deleted

    async def test_can_pause_sync_on_detection(self, destruction_detector, sync_service):
        """Test that sync can be paused when destruction detected."""
        # Trigger destruction
        for i in range(11):
            destruction_detector.record_delete(f"memory_{i}")

        # Pause sync
        destruction_detector.check_and_alert()
        sync_service.pause_sync()

        # Verify sync is paused
        assert sync_service.is_paused()

        # Verify new sync attempts are queued, not sent
        result = await sync_service.sync_memory_on_delete("another_memory")
        assert result["queued"] or result["synced"] is False
