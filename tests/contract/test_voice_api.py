"""
Contract tests for Voice API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

class _FakeElevenLabsService:
    def stream_speech(self, text, voice_id=None):
        yield b"fake audio data"

@pytest.fixture
def app():
    import api.routers.voice as voice_router

    test_app = FastAPI()
    test_app.include_router(voice_router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_speak_contract(client):
    """POST /voice/speak returns audio stream."""
    import api.routers.voice as voice_router
    
    client.app.dependency_overrides[voice_router.get_elevenlabs_service] = lambda: _FakeElevenLabsService()
    try:
        response = client.post("/voice/speak", json={"text": "Hello world"})
    finally:
        client.app.dependency_overrides.clear()
        
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"fake audio data"
