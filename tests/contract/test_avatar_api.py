"""
Contract tests for Avatar API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

class _FakeAvatarResearcher:
    async def analyze_content(self, content, source):
        return {"insights_count": 5, "source": source}
    
    async def research_question(self, question):
        return {"answer": "The avatar desires freedom.", "confidence": 0.9}

@pytest.fixture
def app():
    import api.routers.avatar as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_analyze_content_contract(client):
    """POST /avatar/analyze/content returns analysis result."""
    with patch("api.routers.avatar.create_avatar_researcher", return_value=_FakeAvatarResearcher()):
        response = client.post(
            "/avatar/analyze/content",
            json={"content": "I am exhausted by hollow success", "source": "test"}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["insights_count"] == 5

def test_research_question_contract(client):
    """POST /avatar/research returns answer."""
    with patch("api.routers.avatar.create_avatar_researcher", return_value=_FakeAvatarResearcher()):
        response = client.post(
            "/avatar/research",
            json={"question": "What does the avatar desire?"}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "answer" in data["data"]
