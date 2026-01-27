"""
Contract tests for Belief Journey API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime
from api.models.belief_journey import BeliefJourney, LimitingBelief, BeliefStatus, IASPhase, IASLesson

class _FakeBeliefService:
    def __init__(self):
        self._journeys = {}

    async def create_journey(self, participant_id):
        mock_journey = MagicMock(spec=BeliefJourney)
        mock_journey.id = uuid4()
        mock_journey.participant_id = participant_id
        mock_journey.current_phase = IASPhase.REVELATION
        mock_journey.current_lesson = IASLesson.BREAKTHROUGH_MAPPING
        mock_journey.lessons_completed = []
        mock_journey.limiting_beliefs = []
        mock_journey.empowering_beliefs = []
        mock_journey.experiments = []
        mock_journey.replay_loops = []
        mock_journey.started_at = datetime.utcnow()
        mock_journey.last_activity_at = datetime.utcnow()
        return mock_journey

    async def get_journey(self, journey_id):
        mock_journey = MagicMock(spec=BeliefJourney)
        mock_journey.id = journey_id
        mock_journey.participant_id = "test-user"
        mock_journey.current_phase = IASPhase.REVELATION
        mock_journey.current_lesson = IASLesson.BREAKTHROUGH_MAPPING
        mock_journey.lessons_completed = []
        mock_journey.limiting_beliefs = []
        mock_journey.empowering_beliefs = []
        mock_journey.experiments = []
        mock_journey.replay_loops = []
        mock_journey.started_at = datetime.utcnow()
        mock_journey.last_activity_at = datetime.utcnow()
        return mock_journey

    def get_ingestion_health(self):
        return {"healthy": True}

@pytest.fixture
def app():
    import api.routers.belief_journey as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_create_journey_contract(client):
    """POST /belief-journey/journey/create returns journey data."""
    import api.routers.belief_journey as router
    
    with patch("api.routers.belief_journey.get_belief_tracking_service", return_value=_FakeBeliefService()):
        response = client.post(
            "/belief-journey/journey/create",
            json={"participant_id": "user-123"}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["participant_id"] == "user-123"

def test_get_journey_contract(client):
    """GET /belief-journey/journey/{id} returns journey data."""
    import api.routers.belief_journey as router
    
    journey_id = uuid4()
    with patch("api.routers.belief_journey.get_belief_tracking_service", return_value=_FakeBeliefService()):
        response = client.get(f"/belief-journey/journey/{journey_id}")
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == str(journey_id)
