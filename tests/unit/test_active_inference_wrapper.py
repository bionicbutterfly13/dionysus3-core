import pytest
from unittest.mock import AsyncMock, patch

from api.core.engine.active_inference import ActiveInferenceWrapper
from api.core.engine.models import ThoughtNode


@pytest.mark.asyncio
async def test_score_thought_generates_embedding_and_uses_goal_fallback():
    wrapper = ActiveInferenceWrapper()
    thought = ThoughtNode(content="hello world")

    mock_service = AsyncMock()
    mock_service.generate_embedding = AsyncMock(return_value=[1.0, 0.0])

    with patch("api.core.engine.active_inference.get_embedding_service", return_value=mock_service):
        score = await wrapper.score_thought(thought, goal_vector=[])

    mock_service.generate_embedding.assert_awaited_once_with(thought.content)
    assert score.expected_free_energy == pytest.approx(1.0, rel=1e-3)
    assert score.prediction_error == pytest.approx(0.0, abs=1e-6)


@pytest.mark.asyncio
async def test_score_thought_pads_mismatched_vectors():
    wrapper = ActiveInferenceWrapper()
    thought = ThoughtNode(content="padding test")

    mock_service = AsyncMock()
    mock_service.generate_embedding = AsyncMock(return_value=[1.0, 0.0])

    with patch("api.core.engine.active_inference.get_embedding_service", return_value=mock_service):
        score = await wrapper.score_thought(thought, goal_vector=[1.0, 0.0, 0.0])

    assert score.expected_free_energy == pytest.approx(1.0, rel=1e-3)
    assert score.prediction_error == pytest.approx(0.0, abs=1e-6)
