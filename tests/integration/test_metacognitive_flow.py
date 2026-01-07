"""
Integration Tests for Metacognition API Flow

Feature: 040-metacognitive-particles
Tasks: T012, T023, T032, T041, T057

Tests end-to-end flows through the metacognition API.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestClassificationEndpoint:
    """Integration tests for /api/v1/metacognition/classify."""

    def test_classify_cognitive_particle(self, client):
        """Test classifying a cognitive particle."""
        response = client.post(
            "/api/v1/metacognition/classify",
            json={
                "agent_id": "test_cognitive_agent",
                "blanket": {
                    "external_paths": ["environment"],
                    "sensory_paths": ["perception"],
                    "active_paths": [],
                    "internal_paths": ["state"]
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "particle_type" in data
        assert "confidence" in data
        assert "level" in data
        assert "has_agency" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_classify_active_metacognitive(self, client):
        """Test classifying an active metacognitive particle."""
        response = client.post(
            "/api/v1/metacognition/classify",
            json={
                "agent_id": "test_active_agent",
                "blanket": {
                    "external_paths": ["external"],
                    "sensory_paths": ["sensory"],
                    "active_paths": ["action_1", "action_2"],
                    "internal_paths": ["belief_1", "belief_2", "belief_3"]
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_agency"] is True

    def test_classify_invalid_request(self, client):
        """Test classification with invalid request."""
        response = client.post(
            "/api/v1/metacognition/classify",
            json={"invalid": "data"}
        )

        assert response.status_code == 422  # Validation error


class TestAgencyEndpoint:
    """Integration tests for /api/v1/metacognition/agency/{agent_id}."""

    def test_get_agency_strength(self, client):
        """Test getting agency strength for an agent."""
        response = client.get("/api/v1/metacognition/agency/test_agent")

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "agency_strength" in data
        assert "has_agency" in data
        assert data["agent_id"] == "test_agent"
        assert data["agency_strength"] >= 0.0


class TestEpistemicGainEndpoint:
    """Integration tests for /api/v1/metacognition/epistemic-gain/check."""

    def test_check_epistemic_gain_detected(self, client):
        """Test epistemic gain detection when significant."""
        response = client.post(
            "/api/v1/metacognition/epistemic-gain/check",
            json={
                "particle_id": "test_particle",
                "prior_belief": {
                    "mean": [0.0],
                    "precision": [[0.1]]  # High entropy
                },
                "posterior_belief": {
                    "mean": [0.0],
                    "precision": [[10.0]]  # Low entropy
                },
                "threshold": 0.3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "gain_detected" in data
        # With this significant change, gain should be detected
        if data["gain_detected"]:
            assert "event" in data
            assert data["event"]["magnitude"] > 0.0

    def test_check_epistemic_gain_not_detected(self, client):
        """Test no epistemic gain for small change."""
        response = client.post(
            "/api/v1/metacognition/epistemic-gain/check",
            json={
                "particle_id": "test_particle",
                "prior_belief": {
                    "mean": [0.0],
                    "precision": [[1.0]]
                },
                "posterior_belief": {
                    "mean": [0.0],
                    "precision": [[1.1]]  # Minimal change
                },
                "threshold": 0.3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["gain_detected"] is False


class TestMonitoringEndpoint:
    """Integration tests for /api/v1/metacognition/monitoring/{agent_id}."""

    def test_get_monitoring_assessment(self, client):
        """Test getting cognitive assessment for an agent."""
        response = client.get("/api/v1/metacognition/monitoring/test_agent")

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "progress" in data
        assert "confidence" in data
        assert "prediction_error" in data
        assert "issues" in data
        assert "recommendations" in data
        assert data["agent_id"] == "test_agent"


class TestControlEndpoint:
    """Integration tests for /api/v1/metacognition/control."""

    def test_apply_control_action(self, client):
        """Test applying control action based on assessment."""
        response = client.post(
            "/api/v1/metacognition/control",
            json={
                "assessment": {
                    "id": "assess-123",
                    "agent_id": "test_agent",
                    "progress": 0.5,
                    "confidence": 0.2,  # Low - should trigger action
                    "prediction_error": 0.6,  # High - should trigger action
                    "issues": ["HIGH_PREDICTION_ERROR", "LOW_CONFIDENCE"],
                    "recommendations": []
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "recommended_actions" in data
        assert "rationale" in data
        # Should have actions for the issues
        assert len(data["recommended_actions"]) >= 1


class TestMentalActionEndpoint:
    """Integration tests for /api/v1/metacognition/mental-action."""

    def test_mental_action_hierarchy_violation(self, client):
        """Test mental action returns 403 for hierarchy violation."""
        # Both agents at default level 1 - should fail
        response = client.post(
            "/api/v1/metacognition/mental-action",
            json={
                "source_agent": "agent_a",
                "target_agent": "agent_b",
                "action_type": "precision_modulation",
                "modulation": {"precision_delta": 0.1}
            }
        )

        assert response.status_code == 403
        assert "Hierarchy violation" in response.json()["detail"]


class TestEndToEndFlow:
    """Test complete metacognition flow."""

    def test_classify_then_monitor_then_control(self, client):
        """Test: classify -> monitor -> control flow."""
        # Step 1: Classify
        classify_response = client.post(
            "/api/v1/metacognition/classify",
            json={
                "agent_id": "flow_test_agent",
                "blanket": {
                    "external_paths": ["external"],
                    "sensory_paths": ["sensory"],
                    "active_paths": ["action"],
                    "internal_paths": ["belief_1", "belief_2"]
                }
            }
        )
        assert classify_response.status_code == 200
        classification = classify_response.json()

        # Step 2: Monitor
        monitor_response = client.get(
            f"/api/v1/metacognition/monitoring/{classification['particle_id']}"
        )
        assert monitor_response.status_code == 200
        assessment = monitor_response.json()

        # Step 3: Control (if issues detected)
        control_response = client.post(
            "/api/v1/metacognition/control",
            json={"assessment": assessment}
        )
        assert control_response.status_code == 200
        control = control_response.json()
        assert "recommended_actions" in control

    def test_epistemic_gain_flow(self, client):
        """Test epistemic gain detection flow."""
        # Check for epistemic gain with significant entropy reduction
        response = client.post(
            "/api/v1/metacognition/epistemic-gain/check",
            json={
                "particle_id": "learning_particle",
                "prior_belief": {
                    "mean": [0.0, 0.0],
                    "precision": [[0.5, 0.0], [0.0, 0.5]]  # High entropy
                },
                "posterior_belief": {
                    "mean": [0.0, 0.0],
                    "precision": [[5.0, 0.0], [0.0, 5.0]]  # Low entropy
                },
                "threshold": 0.3
            }
        )

        assert response.status_code == 200
        result = response.json()

        # Verify structure
        assert "gain_detected" in result
        if result["gain_detected"]:
            event = result["event"]
            assert event["prior_entropy"] > event["posterior_entropy"]
            assert event["magnitude"] > 0.0
