"""
Integration Tests: MoSAEIC Neo4j-Only Architecture
Feature: 009-mosaeic-protocol
Task: T010.7

MoSAEIC = Mindful Observation of Senses, Actions, Emotions, Impulses, and Cognitions

Tests the Neo4j-only MoSAEIC flow via n8n webhooks:
1. Profile initialization from Step 1 narrative work
2. Capture creation with correct 5 windows
3. Pattern detection with recurrence tracking
4. RemoteSyncService webhook integration

Uses mocked webhook responses since n8n workflows are deployed separately.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from api.services.remote_sync import RemoteSyncService, SyncConfig


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def sync_config():
    """Create test sync config with mock URLs."""
    return SyncConfig(
        webhook_token="test-secret-token",
        mosaeic_capture_webhook_url="http://localhost:5678/webhook/mosaeic/v1/capture/create",
        mosaeic_profile_webhook_url="http://localhost:5678/webhook/mosaeic/v1/profile/initialize",
        mosaeic_pattern_webhook_url="http://localhost:5678/webhook/mosaeic/v1/pattern/detect",
    )


@pytest.fixture
def sync_service(sync_config):
    """Create RemoteSyncService with test config."""
    return RemoteSyncService(config=sync_config)


@pytest.fixture
def sample_profile_data():
    """Sample profile data from Step 1 narrative work."""
    return {
        "user_id": str(uuid.uuid4()),
        "neurotype_classification": "analytical_empath",
        "biological_model": "orchid",
        "sensory_processing_style": "high_sensitivity",
        "aspects": [
            {"name": "Protector", "status": "In Control", "role": "Head of Security, Threat Detector"},
            {"name": "Inner CEO", "status": "Silenced", "role": "Executive Function, Decision Maker"},
            {"name": "Inner Child", "status": "Muted", "role": "Emotional Needs, Vulnerability"},
            {"name": "Inner Critic", "status": "Active", "role": "Performance Standards"},
            {"name": "Visionary", "status": "Emerging", "role": "Creative Self, Dreams"},
        ],
        "threat_predictions": [
            {
                "prediction": "If I show vulnerability, I will be rejected",
                "domain": "relationships",
                "protector_directive": "Never let them see the real you",
                "emotional_cost": "Hollow success, deep isolation",
                "silenced_aspect": "Inner Child",
            },
            {
                "prediction": "If I fail at work, I will be worthless",
                "domain": "work",
                "protector_directive": "Be perfect or don't try",
                "emotional_cost": "Constant anxiety, burnout",
                "silenced_aspect": "Visionary",
            },
        ],
    }


@pytest.fixture
def sample_capture_data():
    """Sample capture data with correct 5 MoSAEIC windows."""
    return {
        "session_id": str(uuid.uuid4()),
        "senses": {
            "interoceptive": "Tight chest, shallow breathing",
            "exteroceptive": "Bright office lights, keyboard sounds",
            "bodyState": "Tension in shoulders",
        },
        "actions": {
            "executed": "Typing email response",
            "motorOutput": "Rigid posture, clenched jaw",
        },
        "emotions": {
            "primary": "Anxiety",
            "valence": -0.6,
            "arousal": 0.8,
        },
        "impulses": {
            "urges": "To leave the meeting early",
            "avoidance": "Avoid eye contact",
            "approach": None,
        },
        "cognitions": {
            "automaticThoughts": "They're judging me",
            "interpretations": "This is going badly",
            "predictions": "I'll be criticized later",
            "coreBelief": "I am not good enough",
        },
        "emotional_intensity": 7.5,
        "context": {"location": "work", "trigger": "team meeting"},
    }


# =========================================================================
# Profile Initialization Tests
# =========================================================================


class TestProfileInitialization:
    """Test MoSAEIC profile initialization from Step 1 narrative work."""

    @pytest.mark.asyncio
    async def test_initialize_profile_success(self, sync_service, sample_profile_data):
        """Test successful profile initialization via webhook."""
        mock_response = {
            "success": True,
            "user_id": sample_profile_data["user_id"],
            "profile_version": 1,
            "self_concept_id": str(uuid.uuid4()),
            "aspects_created": 5,
            "threats_created": 2,
        }

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            mock_webhook.return_value = mock_response

            result = await sync_service.initialize_profile(
                user_id=sample_profile_data["user_id"],
                neurotype_classification=sample_profile_data["neurotype_classification"],
                biological_model=sample_profile_data["biological_model"],
                sensory_processing_style=sample_profile_data["sensory_processing_style"],
                aspects=sample_profile_data["aspects"],
                threat_predictions=sample_profile_data["threat_predictions"],
            )

            assert result["success"] is True
            assert result["profile_version"] == 1
            assert result["aspects_created"] == 5
            assert result["threats_created"] == 2

            # Verify webhook was called with correct payload
            mock_webhook.assert_called_once()
            call_args = mock_webhook.call_args
            payload = call_args[0][0]

            assert payload["user_id"] == sample_profile_data["user_id"]
            assert payload["neurotype_classification"] == "analytical_empath"
            assert payload["biological_model"] == "orchid"
            assert len(payload["aspects"]) == 5
            assert len(payload["threat_predictions"]) == 2

    @pytest.mark.asyncio
    async def test_initialize_profile_with_defaults(self, sync_service):
        """Test profile initialization with default values."""
        user_id = str(uuid.uuid4())
        mock_response = {
            "success": True,
            "user_id": user_id,
            "profile_version": 1,
            "self_concept_id": str(uuid.uuid4()),
            "aspects_created": 0,
            "threats_created": 0,
        }

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            mock_webhook.return_value = mock_response

            result = await sync_service.initialize_profile(
                user_id=user_id,
                neurotype_classification="creative_sensitive",
            )

            assert result["success"] is True

            payload = mock_webhook.call_args[0][0]
            assert payload["biological_model"] == "orchid"  # default
            assert payload["sensory_processing_style"] == "high_sensitivity"  # default
            assert payload["aspects"] == []  # default empty
            assert payload["threat_predictions"] == []  # default empty


# =========================================================================
# Capture Creation Tests
# =========================================================================


class TestCaptureCreation:
    """Test MoSAEIC capture creation with correct 5 windows."""

    @pytest.mark.asyncio
    async def test_create_capture_success(self, sync_service, sample_capture_data):
        """Test successful capture creation via webhook."""
        capture_id = str(uuid.uuid4())
        mock_response = {
            "success": True,
            "capture_id": capture_id,
            "session_id": sample_capture_data["session_id"],
            "turning_point": False,
            "matched_threats": [],
            "threats_triggered": 0,
        }

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            mock_webhook.return_value = mock_response

            result = await sync_service.create_capture(
                session_id=sample_capture_data["session_id"],
                senses=sample_capture_data["senses"],
                actions=sample_capture_data["actions"],
                emotions=sample_capture_data["emotions"],
                impulses=sample_capture_data["impulses"],
                cognitions=sample_capture_data["cognitions"],
                emotional_intensity=sample_capture_data["emotional_intensity"],
                context=sample_capture_data["context"],
            )

            assert result["success"] is True
            assert result["capture_id"] == capture_id
            assert result["turning_point"] is False

            # Verify all 5 windows sent correctly
            payload = mock_webhook.call_args[0][0]
            assert payload["senses"]["interoceptive"] == "Tight chest, shallow breathing"
            assert payload["actions"]["executed"] == "Typing email response"
            assert payload["emotions"]["primary"] == "Anxiety"
            assert payload["impulses"]["avoidance"] == "Avoid eye contact"
            assert payload["cognitions"]["coreBelief"] == "I am not good enough"

    @pytest.mark.asyncio
    async def test_create_capture_high_intensity_turning_point(self, sync_service):
        """Test that high emotional intensity triggers turning point detection."""
        session_id = str(uuid.uuid4())
        capture_id = str(uuid.uuid4())
        mock_response = {
            "success": True,
            "capture_id": capture_id,
            "session_id": session_id,
            "turning_point": True,  # Auto-detected due to high intensity
            "matched_threats": [],
            "threats_triggered": 0,
        }

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            mock_webhook.return_value = mock_response

            result = await sync_service.create_capture(
                session_id=session_id,
                emotions={"primary": "Terror", "valence": -0.9, "arousal": 1.0},
                emotional_intensity=9.5,  # >= 8.5 triggers turning point
            )

            assert result["success"] is True
            assert result["turning_point"] is True

    @pytest.mark.asyncio
    async def test_create_capture_with_threat_match(self, sync_service):
        """Test that cognitions.coreBelief matches existing ThreatPredictions."""
        session_id = str(uuid.uuid4())
        capture_id = str(uuid.uuid4())
        threat_id = str(uuid.uuid4())

        mock_response = {
            "success": True,
            "capture_id": capture_id,
            "session_id": session_id,
            "turning_point": False,
            "matched_threats": [
                {
                    "threat_id": threat_id,
                    "prediction": "If I show vulnerability, I will be rejected",
                }
            ],
            "threats_triggered": 1,
        }

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            mock_webhook.return_value = mock_response

            result = await sync_service.create_capture(
                session_id=session_id,
                cognitions={
                    "coreBelief": "If I open up, they will leave me",  # Matches threat
                },
                emotional_intensity=6.0,
            )

            assert result["success"] is True
            assert result["threats_triggered"] == 1
            assert len(result["matched_threats"]) == 1
            assert result["matched_threats"][0]["threat_id"] == threat_id


# =========================================================================
# Pattern Detection Tests
# =========================================================================


class TestPatternDetection:
    """Test maladaptive pattern detection with recurrence tracking."""

    @pytest.mark.asyncio
    async def test_detect_pattern_new(self, sync_service):
        """Test detection of new pattern (first occurrence)."""
        user_id = str(uuid.uuid4())
        capture_id = str(uuid.uuid4())
        pattern_id = str(uuid.uuid4())

        mock_response = {
            "success": True,
            "action": "create",
            "capture_id": capture_id,
            "pattern_id": pattern_id,
            "belief_content": "I am incompetent",
            "recurrence_count": 1,
            "severity_score": 0.1,
            "intervention_status": "detected",
            "needs_intervention": False,
        }

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            mock_webhook.return_value = mock_response

            result = await sync_service.detect_pattern(
                user_id=user_id,
                capture_id=capture_id,
                belief_content="I am incompetent",
                domain="self",
                initial_severity=0.1,
            )

            assert result["success"] is True
            assert result["action"] == "create"
            assert result["recurrence_count"] == 1
            assert result["severity_score"] == 0.1
            assert result["needs_intervention"] is False

    @pytest.mark.asyncio
    async def test_detect_pattern_recurrence(self, sync_service):
        """Test pattern recurrence updates severity and may trigger intervention."""
        user_id = str(uuid.uuid4())
        capture_id = str(uuid.uuid4())
        pattern_id = str(uuid.uuid4())

        mock_response = {
            "success": True,
            "action": "update",
            "capture_id": capture_id,
            "pattern_id": pattern_id,
            "belief_content": "I am incompetent",
            "recurrence_count": 5,
            "severity_score": 0.9,  # High after many recurrences
            "intervention_status": "queued",
            "needs_intervention": True,
        }

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            mock_webhook.return_value = mock_response

            result = await sync_service.detect_pattern(
                user_id=user_id,
                capture_id=capture_id,
                belief_content="I am incompetent",  # Same belief as before
                domain="self",
            )

            assert result["success"] is True
            assert result["action"] == "update"
            assert result["recurrence_count"] == 5
            assert result["severity_score"] >= 0.7
            assert result["needs_intervention"] is True
            assert result["intervention_status"] == "queued"

    @pytest.mark.asyncio
    async def test_detect_pattern_different_domains(self, sync_service):
        """Test that patterns are tracked separately per domain."""
        user_id = str(uuid.uuid4())
        capture_id = str(uuid.uuid4())

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            # First call: self domain
            mock_webhook.return_value = {
                "success": True,
                "action": "create",
                "pattern_id": str(uuid.uuid4()),
                "domain": "self",
                "recurrence_count": 1,
            }

            result1 = await sync_service.detect_pattern(
                user_id=user_id,
                capture_id=capture_id,
                belief_content="I always fail",
                domain="self",
            )

            payload1 = mock_webhook.call_args[0][0]
            assert payload1["domain"] == "self"

            # Second call: work domain (different pattern)
            mock_webhook.return_value = {
                "success": True,
                "action": "create",
                "pattern_id": str(uuid.uuid4()),
                "domain": "work",
                "recurrence_count": 1,
            }

            result2 = await sync_service.detect_pattern(
                user_id=user_id,
                capture_id=capture_id,
                belief_content="I always fail",
                domain="work",
            )

            payload2 = mock_webhook.call_args[0][0]
            assert payload2["domain"] == "work"

            # Both should be new patterns (different domains)
            assert result1["action"] == "create"
            assert result2["action"] == "create"


# =========================================================================
# Integration Flow Tests
# =========================================================================


class TestIntegratedMoSAEICFlow:
    """Test complete integrated MoSAEIC flow: Profile -> Capture -> Pattern."""

    @pytest.mark.asyncio
    async def test_full_flow_profile_to_pattern(
        self, sync_service, sample_profile_data, sample_capture_data
    ):
        """Test the full flow from profile initialization through pattern detection."""
        user_id = sample_profile_data["user_id"]
        session_id = sample_capture_data["session_id"]
        capture_id = str(uuid.uuid4())
        pattern_id = str(uuid.uuid4())
        threat_id = str(uuid.uuid4())

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            # Step 1: Initialize profile from Step 1 work
            mock_webhook.return_value = {
                "success": True,
                "user_id": user_id,
                "profile_version": 1,
                "self_concept_id": str(uuid.uuid4()),
                "aspects_created": 5,
                "threats_created": 2,
            }

            profile_result = await sync_service.initialize_profile(
                user_id=user_id,
                neurotype_classification=sample_profile_data["neurotype_classification"],
                aspects=sample_profile_data["aspects"],
                threat_predictions=sample_profile_data["threat_predictions"],
            )

            assert profile_result["success"] is True
            assert profile_result["aspects_created"] == 5

            # Step 2: Create capture with matching threat
            mock_webhook.return_value = {
                "success": True,
                "capture_id": capture_id,
                "session_id": session_id,
                "turning_point": False,
                "matched_threats": [
                    {
                        "threat_id": threat_id,
                        "prediction": "If I show vulnerability, I will be rejected",
                    }
                ],
                "threats_triggered": 1,
            }

            capture_result = await sync_service.create_capture(
                session_id=session_id,
                senses=sample_capture_data["senses"],
                actions=sample_capture_data["actions"],
                emotions=sample_capture_data["emotions"],
                impulses=sample_capture_data["impulses"],
                cognitions=sample_capture_data["cognitions"],
                emotional_intensity=sample_capture_data["emotional_intensity"],
            )

            assert capture_result["success"] is True
            assert capture_result["threats_triggered"] == 1

            # Step 3: Detect pattern from capture's core belief
            mock_webhook.return_value = {
                "success": True,
                "action": "create",
                "capture_id": capture_id,
                "pattern_id": pattern_id,
                "belief_content": sample_capture_data["cognitions"]["coreBelief"],
                "recurrence_count": 1,
                "severity_score": 0.2,
                "intervention_status": "detected",
                "needs_intervention": False,
            }

            pattern_result = await sync_service.detect_pattern(
                user_id=user_id,
                capture_id=capture_id,
                belief_content=sample_capture_data["cognitions"]["coreBelief"],
                domain="self",
            )

            assert pattern_result["success"] is True
            assert pattern_result["pattern_id"] == pattern_id
            assert pattern_result["recurrence_count"] == 1

    @pytest.mark.asyncio
    async def test_recurring_pattern_triggers_intervention(self, sync_service):
        """Test that recurring patterns eventually trigger intervention."""
        user_id = str(uuid.uuid4())
        pattern_id = str(uuid.uuid4())
        belief = "I am fundamentally broken"

        with patch.object(
            sync_service, "_send_to_webhook", new_callable=AsyncMock
        ) as mock_webhook:
            # Simulate 5 captures with same belief
            recurrence_responses = [
                {"action": "create", "recurrence_count": 1, "severity_score": 0.1, "needs_intervention": False},
                {"action": "update", "recurrence_count": 2, "severity_score": 0.3, "needs_intervention": False},
                {"action": "update", "recurrence_count": 3, "severity_score": 0.5, "needs_intervention": False},
                {"action": "update", "recurrence_count": 4, "severity_score": 0.7, "needs_intervention": True},
                {"action": "update", "recurrence_count": 5, "severity_score": 0.9, "needs_intervention": True},
            ]

            for i, expected in enumerate(recurrence_responses):
                capture_id = str(uuid.uuid4())
                mock_webhook.return_value = {
                    "success": True,
                    "pattern_id": pattern_id,
                    "capture_id": capture_id,
                    "belief_content": belief,
                    "intervention_status": "queued" if expected["needs_intervention"] else "detected",
                    **expected,
                }

                result = await sync_service.detect_pattern(
                    user_id=user_id,
                    capture_id=capture_id,
                    belief_content=belief,
                    domain="self",
                )

                assert result["recurrence_count"] == expected["recurrence_count"]
                assert result["needs_intervention"] == expected["needs_intervention"]

                # After 4th recurrence, intervention should be needed
                if expected["recurrence_count"] >= 4:
                    assert result["needs_intervention"] is True
                    assert result["severity_score"] >= 0.7


# =========================================================================
# Webhook Configuration Tests
# =========================================================================


class TestWebhookConfiguration:
    """Test that webhook URLs are correctly configured."""

    def test_sync_config_mosaeic_urls(self, sync_config):
        """Test that MoSAEIC webhook URLs are properly set."""
        assert "mosaeic/v1/capture/create" in sync_config.mosaeic_capture_webhook_url
        assert "mosaeic/v1/profile/initialize" in sync_config.mosaeic_profile_webhook_url
        assert "mosaeic/v1/pattern/detect" in sync_config.mosaeic_pattern_webhook_url

    def test_sync_service_uses_correct_urls(self, sync_service, sync_config):
        """Test that service methods use correct webhook URLs."""
        assert sync_service.config.mosaeic_capture_webhook_url == sync_config.mosaeic_capture_webhook_url
        assert sync_service.config.mosaeic_profile_webhook_url == sync_config.mosaeic_profile_webhook_url
        assert sync_service.config.mosaeic_pattern_webhook_url == sync_config.mosaeic_pattern_webhook_url
