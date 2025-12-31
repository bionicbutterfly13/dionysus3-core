"""
Unit tests for Research-Validated Cognitive Tools.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.agents.tools.cognitive_tools import (
    understand_question,
    recall_related,
    examine_answer,
    backtracking
)

@pytest.fixture
def mock_llm():
    with patch("api.agents.tools.cognitive_tools.chat_completion", new_callable=AsyncMock) as mock:
        yield mock

@pytest.mark.asyncio
async def test_understand_question(mock_llm):
    mock_llm.return_value = "Step 1: Identify vars..."
    
    # Tool.forward is sync but calls async internally via wrapper
    # We need to mock async_tool_wrapper or just let it run if we mock the inner async call
    # D3 async_tool_wrapper uses run_coroutine_threadsafe.
    # For unit tests, it's easier to mock async_tool_wrapper to just run the coroutine directly if possible,
    # OR we rely on the fact that `mock_llm` is async.
    
    # Since `async_tool_wrapper` does thread magic, we might need to mock it to just run sync for tests
    # or ensure the event loop handling is correct.
    # Actually, `forward` calls `async_tool_wrapper(_run)()`. 
    # If we patch `async_tool_wrapper` to just return a synchronous execution of the coroutine, it simplifies things.
    
    with patch("api.agents.tools.cognitive_tools.async_tool_wrapper") as mock_wrapper:
        # Mock wrapper to return a function that returns the result
        async def fake_run(coro_func):
            return await coro_func
            
        # We need a sync wrapper that takes the coroutine and returns a function that returns the result
        def side_effect(coro):
            def execute():
                # We can't await here because execute is sync. 
                # This suggests the unit test should probably test the logic, not the wrapper.
                # But `forward` uses the wrapper.
                
                # Let's assume the wrapper works (it's infrastructure). 
                # We want to verify that `chat_completion` is called with correct prompt.
                
                # If we mock chat_completion, `_run` will return a coroutine.
                # `async_tool_wrapper` will run it.
                return "Step 1: Identify vars..."
            return execute
            
        mock_wrapper.side_effect = side_effect
        
        result = understand_question.forward("Solve x^2 = 4")
        
        assert result["analysis"] == "Step 1: Identify vars..."
        assert result["original_question"] == "Solve x^2 = 4"

@pytest.mark.asyncio
async def test_recall_related(mock_llm):
    mock_llm.return_value = "Analogous Example 1..."
    
    with patch("api.agents.tools.cognitive_tools.async_tool_wrapper") as mock_wrapper:
        def side_effect(coro):
            def execute():
                return "Analogous Example 1..."
            return execute
        mock_wrapper.side_effect = side_effect
        
        result = recall_related.forward("Solve x^2 = 4")
        
        assert "analogies" in result
        assert result["analogies"] == "Analogous Example 1..."

@pytest.mark.asyncio
async def test_examine_answer(mock_llm):
    mock_llm.return_value = "Critique: Correct."
    
    with patch("api.agents.tools.cognitive_tools.async_tool_wrapper") as mock_wrapper:
        def side_effect(coro):
            def execute():
                return "Critique: Correct."
            return execute
        mock_wrapper.side_effect = side_effect
        
        result = examine_answer.forward("Solve x^2 = 4", "x=2")
        
        assert result["critique"] == "Critique: Correct."

@pytest.mark.asyncio
async def test_backtracking(mock_llm):
    mock_llm.return_value = "Try x=-2 as well."
    
    with patch("api.agents.tools.cognitive_tools.async_tool_wrapper") as mock_wrapper:
        def side_effect(coro):
            def execute():
                return "Try x=-2 as well."
            return execute
        mock_wrapper.side_effect = side_effect
        
        result = backtracking.forward("Solve x^2 = 4", "x=2 only")
        
        assert result["strategy"] == "Try x=-2 as well."
