"""
Integration Tests for Belief Journey Router

Feature: 036-belief-avatar-system
Tests: T008, T009, T010, T021, T022, T036
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


# =============================================================================
# T008: Journey Creation Tests
# =============================================================================


class TestJourneyCreation:
    """Integration tests for journey creation and retrieval."""

    async def test_create_journey(self, client: AsyncClient):
        """Test creating a new belief journey."""
        response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_pilot_001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["participant_id"] == "test_pilot_001"
        assert data["data"]["current_phase"] == "revelation"
        assert data["data"]["current_lesson"] == "lesson_1_breakthrough_mapping"

    async def test_create_journey_without_participant_id(self, client: AsyncClient):
        """Test creating journey without participant_id (optional field)."""
        response = await client.post(
            "/belief-journey/journey/create",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["participant_id"] is None

    async def test_get_journey(self, client: AsyncClient):
        """Test retrieving a journey by ID."""
        # Create journey first
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_pilot_002"}
        )
        journey_id = create_response.json()["data"]["id"]

        # Retrieve it
        response = await client.get(f"/belief-journey/journey/{journey_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == journey_id
        assert data["data"]["limiting_beliefs_count"] == 0
        assert data["data"]["empowering_beliefs_count"] == 0

    async def test_get_journey_not_found(self, client: AsyncClient):
        """Test 404 for non-existent journey."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/belief-journey/journey/{fake_uuid}")
        assert response.status_code == 404

    async def test_advance_lesson(self, client: AsyncClient):
        """Test advancing journey to next lesson."""
        # Create journey
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_pilot_003"}
        )
        journey_id = create_response.json()["data"]["id"]

        # First complete lesson 1
        await client.post(
            f"/belief-journey/journey/{journey_id}/advance",
            json={"lesson": "lesson_1_breakthrough_mapping"}
        )

        # Then advance to lesson 2
        response = await client.post(
            f"/belief-journey/journey/{journey_id}/advance",
            json={"lesson": "lesson_2_mosaeic_method"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["current_lesson"] == "lesson_2_mosaeic_method"
        assert "lesson_1_breakthrough_mapping" in data["data"]["lessons_completed"]
        assert "lesson_2_mosaeic_method" in data["data"]["lessons_completed"]


# =============================================================================
# T009: Limiting Belief Lifecycle Tests
# =============================================================================


class TestLimitingBeliefLifecycle:
    """Integration tests for limiting belief CRUD operations."""

    async def test_identify_limiting_belief(self, client: AsyncClient):
        """Test identifying a new limiting belief."""
        # Create journey first
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_belief_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        # Identify limiting belief
        response = await client.post(
            "/belief-journey/beliefs/limiting/identify",
            json={
                "journey_id": journey_id,
                "content": "I must always be exceptional",
                "pattern_name": "perfectionism_trap",
                "self_talk": ["I should have done better"],
                "mental_blocks": ["Fear of delegation"],
                "protects_from": "Fear of being mediocre"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["content"] == "I must always be exceptional"
        assert data["data"]["status"] == "identified"

    async def test_map_limiting_belief(self, client: AsyncClient):
        """Test mapping belief to behaviors."""
        # Create journey and belief
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_belief_002"}
        )
        journey_id = create_response.json()["data"]["id"]

        belief_response = await client.post(
            "/belief-journey/beliefs/limiting/identify",
            json={
                "journey_id": journey_id,
                "content": "I am not good enough"
            }
        )
        belief_id = belief_response.json()["data"]["id"]

        # Map belief
        response = await client.post(
            f"/belief-journey/beliefs/limiting/{belief_id}/map",
            json={
                "journey_id": journey_id,
                "self_talk": ["I can't do this", "I'll fail"],
                "mental_blocks": ["Imposter syndrome"],
                "self_sabotage_behaviors": ["Procrastination", "Overworking"],
                "protects_from": "Vulnerability"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "mapped"
        assert len(data["data"]["self_talk"]) == 2

    async def test_add_evidence_against_belief(self, client: AsyncClient):
        """Test adding counter-evidence to a limiting belief."""
        # Create journey and belief
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_evidence_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        belief_response = await client.post(
            "/belief-journey/beliefs/limiting/identify",
            json={
                "journey_id": journey_id,
                "content": "Nobody values my work"
            }
        )
        belief_id = belief_response.json()["data"]["id"]

        # Add evidence against
        response = await client.post(
            f"/belief-journey/beliefs/limiting/{belief_id}/evidence",
            json={
                "journey_id": journey_id,
                "evidence": "My manager praised my last project",
                "evidence_type": "against"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["evidence_against"]) == 1
        assert "praised my last project" in data["data"]["evidence_against"][0]

    async def test_dissolve_limiting_belief(self, client: AsyncClient):
        """Test dissolving a limiting belief."""
        # Create journey and belief
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_dissolve_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        belief_response = await client.post(
            "/belief-journey/beliefs/limiting/identify",
            json={
                "journey_id": journey_id,
                "content": "I am unlovable"
            }
        )
        belief_id = belief_response.json()["data"]["id"]

        # Dissolve belief
        response = await client.post(
            f"/belief-journey/beliefs/limiting/{belief_id}/dissolve",
            json={"journey_id": journey_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "dissolved"
        assert data["data"]["dissolved_at"] is not None


# =============================================================================
# T010: Empowering Belief Lifecycle Tests
# =============================================================================


class TestEmpoweringBeliefLifecycle:
    """Integration tests for empowering belief operations."""

    async def test_propose_empowering_belief(self, client: AsyncClient):
        """Test proposing a new empowering belief."""
        # Create journey
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_empower_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        # Propose empowering belief
        response = await client.post(
            "/belief-journey/beliefs/empowering/propose",
            json={
                "journey_id": journey_id,
                "content": "My worth is inherent, not earned",
                "bridge_version": "I am learning that my worth is inherent"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["content"] == "My worth is inherent, not earned"
        assert data["data"]["bridge_version"] == "I am learning that my worth is inherent"
        assert data["data"]["status"] == "proposed"

    async def test_strengthen_empowering_belief(self, client: AsyncClient):
        """Test strengthening an empowering belief with evidence."""
        # Create journey and empowering belief
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_strengthen_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        belief_response = await client.post(
            "/belief-journey/beliefs/empowering/propose",
            json={
                "journey_id": journey_id,
                "content": "I am capable of growth"
            }
        )
        belief_id = belief_response.json()["data"]["id"]

        # Strengthen with evidence
        response = await client.post(
            f"/belief-journey/beliefs/empowering/{belief_id}/strengthen",
            json={
                "journey_id": journey_id,
                "evidence": "I learned a new skill this month",
                "embodiment_increase": 0.15
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["embodiment_level"] >= 0.15
        assert "I learned a new skill" in data["data"]["evidence_collected"][0]

    async def test_anchor_empowering_belief(self, client: AsyncClient):
        """Test anchoring an empowering belief to a habit."""
        # Create journey and belief
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_anchor_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        belief_response = await client.post(
            "/belief-journey/beliefs/empowering/propose",
            json={
                "journey_id": journey_id,
                "content": "I deserve rest"
            }
        )
        belief_id = belief_response.json()["data"]["id"]

        # Anchor to habit
        response = await client.post(
            f"/belief-journey/beliefs/empowering/{belief_id}/anchor",
            json={
                "journey_id": journey_id,
                "habit_stack": "After my morning coffee",
                "checklist_items": ["Take 5 deep breaths", "Set a rest intention"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["habit_stack"] == "After my morning coffee"
        assert len(data["data"]["daily_checklist_items"]) == 2


# =============================================================================
# T021/T022: Metrics Tests
# =============================================================================


class TestJourneyMetrics:
    """Integration tests for journey metrics endpoint."""

    async def test_metrics_with_populated_journey(self, client: AsyncClient):
        """Test metrics calculation with beliefs and experiments."""
        # Create journey
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_metrics_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        # Add some beliefs
        await client.post(
            "/belief-journey/beliefs/limiting/identify",
            json={"journey_id": journey_id, "content": "Belief 1"}
        )
        await client.post(
            "/belief-journey/beliefs/empowering/propose",
            json={"journey_id": journey_id, "content": "Empowering 1"}
        )

        # Get metrics
        response = await client.get(f"/belief-journey/journey/{journey_id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["limiting_beliefs"]["total"] == 1
        assert data["data"]["empowering_beliefs"]["total"] == 1

    async def test_metrics_with_empty_journey(self, client: AsyncClient):
        """Test metrics for a fresh journey with no data."""
        # Create journey
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_metrics_002"}
        )
        journey_id = create_response.json()["data"]["id"]

        # Get metrics
        response = await client.get(f"/belief-journey/journey/{journey_id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["limiting_beliefs"]["total"] == 0
        assert data["data"]["limiting_beliefs"]["dissolution_rate"] == 0.0
        assert data["data"]["experiments"]["total"] == 0
        assert data["data"]["replay_loops"]["total"] == 0


# =============================================================================
# T036: Replay Loop Lifecycle Tests
# =============================================================================


class TestReplayLoopLifecycle:
    """Integration tests for replay loop operations."""

    async def test_identify_replay_loop(self, client: AsyncClient):
        """Test identifying a new replay loop."""
        # Create journey
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_loop_001"}
        )
        journey_id = create_response.json()["data"]["id"]

        # Identify loop
        response = await client.post(
            "/belief-journey/loops/identify",
            json={
                "journey_id": journey_id,
                "trigger_situation": "After giving feedback",
                "story_text": "They must think I'm too critical",
                "emotion": "anxiety",
                "fear_underneath": "Fear of rejection"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["trigger_situation"] == "After giving feedback"
        assert data["data"]["status"] == "active"

    async def test_interrupt_and_resolve_loop(self, client: AsyncClient):
        """Test full loop lifecycle: identify → interrupt → resolve."""
        # Create journey and loop
        create_response = await client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "test_loop_002"}
        )
        journey_id = create_response.json()["data"]["id"]

        loop_response = await client.post(
            "/belief-journey/loops/identify",
            json={
                "journey_id": journey_id,
                "trigger_situation": "Making a mistake",
                "story_text": "I'm incompetent",
                "emotion": "shame",
                "fear_underneath": "Fear of inadequacy"
            }
        )
        loop_id = loop_response.json()["data"]["id"]

        # Interrupt with compassion
        interrupt_response = await client.post(
            f"/belief-journey/loops/{loop_id}/interrupt",
            json={
                "journey_id": journey_id,
                "compassionate_reflection": "Everyone makes mistakes. This doesn't define me."
            }
        )
        assert interrupt_response.status_code == 200
        assert interrupt_response.json()["data"]["status"] == "interrupted"

        # Resolve with lesson
        resolve_response = await client.post(
            f"/belief-journey/loops/{loop_id}/resolve",
            json={
                "journey_id": journey_id,
                "lesson_found": "Mistakes are learning opportunities",
                "comfort_offered": "I am growing, and that takes courage",
                "time_to_resolution_minutes": 12.5
            }
        )
        assert resolve_response.status_code == 200
        data = resolve_response.json()["data"]
        assert data["status"] == "resolved"
        assert data["time_to_resolution_minutes"] == 12.5


# =============================================================================
# Health Endpoint Test
# =============================================================================


class TestHealthEndpoint:
    """Test the router health endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Test belief journey health endpoint."""
        response = await client.get("/belief-journey/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "belief-journey"
        assert "journeys_in_memory" in data

    async def test_health_includes_ingestion_stats(self, client: AsyncClient):
        """Test that health endpoint includes ingestion statistics."""
        response = await client.get("/belief-journey/health")
        assert response.status_code == 200
        data = response.json()
        
        # Verify ingestion stats are present
        assert "ingestion" in data
        ingestion = data["ingestion"]
        assert "total_attempts" in ingestion
        assert "successful" in ingestion
        assert "failed" in ingestion
        assert "success_rate" in ingestion
        assert "healthy" in ingestion
        assert "recent_failures" in ingestion
