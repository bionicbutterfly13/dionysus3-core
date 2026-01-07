"""
Unit tests for Meta-Cognitive Learning (Feature 043).
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from api.models.meta_cognition import CognitiveEpisode
from api.services.meta_cognitive_service import MetaCognitiveLearner

@pytest.fixture
def sample_episode():
    return CognitiveEpisode(
        task_query="How to port D2 tools?",
        tools_used=["understand_question", "recall_related"],
        success=True,
        lessons_learned="Always break down the problem first."
    )

def test_episode_serialization(sample_episode):
    data = sample_episode.model_dump()
    assert data["task_query"] == "How to port D2 tools?"
    assert "understand_question" in data["tools_used"]
    assert data["success"] is True

@pytest.mark.asyncio
async def test_synthesize_lessons():
    learner = MetaCognitiveLearner()
    episodes = [
        CognitiveEpisode(
            task_query="Task A",
            tools_used=["tool1"],
            success=True,
            lessons_learned="Lesson A"
        ),
        CognitiveEpisode(
            task_query="Task B",
            tools_used=["tool2"],
            success=False,
            lessons_learned="Lesson B"
        )
    ]
    
    with patch("api.services.meta_cognitive_service.chat_completion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Advice: Use tool1, avoid tool2."
        
        result = await learner.synthesize_lessons(episodes)
        
        assert "Advice" in result
        mock_llm.assert_called_once()

@pytest.mark.asyncio
async def test_record_episode():
    learner = MetaCognitiveLearner()
    episode = CognitiveEpisode(task_query="Test recording")
    
    mock_session = AsyncMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    with patch("api.services.meta_cognitive_service.get_neo4j_driver", return_value=mock_driver):
        await learner.record_episode(episode)
        
        mock_session.run.assert_called_once()
        # Verify params
        args, kwargs = mock_session.run.call_args
        assert args[1]["task_query"] == "Test recording"

@pytest.mark.asyncio
async def test_retrieve_relevant_episodes_fallback():
    learner = MetaCognitiveLearner()
    
    mock_session = AsyncMock()
    # Mock result data
    mock_session.run.return_value.data.return_value = [
        {
            "node": {
                "id": "ep1",
                "timestamp": datetime.utcnow().isoformat(),
                "task_query": "Past Task",
                "success": True,
                "surprise_score": 0.1
            }
        }
    ]
    
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    with patch("api.services.meta_cognitive_service.get_neo4j_driver", return_value=mock_driver):
        results = await learner.retrieve_relevant_episodes("Current Task")
        
        assert len(results) == 1
        assert results[0].task_query == "Past Task"
        assert results[0].id == "ep1"
