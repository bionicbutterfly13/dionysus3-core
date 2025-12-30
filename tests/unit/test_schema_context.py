import pytest
import json
from unittest.mock import AsyncMock, patch
from pydantic import BaseModel, Field
from api.utils.schema_context import SchemaContext

class MockModel(BaseModel):
    name: str
    score: int = Field(..., ge=0, le=100)

@pytest.mark.asyncio
async def test_schema_context_success():
    """Verify SchemaContext returns parsed object on first success."""
    context = SchemaContext(MockModel)
    
    # Mock LLM response
    valid_json = json.dumps({"name": "Dionysus", "score": 95})
    
    with patch("api.utils.schema_context.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = valid_json
        
        result = await context.query("Test prompt")
        
        assert result["name"] == "Dionysus"
        assert result["score"] == 95
        assert mock_chat.call_count == 1

@pytest.mark.asyncio
async def test_schema_context_retry_and_recover():
    """Verify SchemaContext retries on invalid JSON and succeeds."""
    context = SchemaContext(MockModel, max_retries=2)
    
    invalid_json = "This is not JSON"
    valid_json = json.dumps({"name": "Recovered", "score": 80})
    
    with patch("api.utils.schema_context.chat_completion", new_callable=AsyncMock) as mock_chat:
        # First call fails, second succeeds
        mock_chat.side_effect = [invalid_json, valid_json]
        
        result = await context.query("Test prompt")
        
        assert result["name"] == "Recovered"
        assert mock_chat.call_count == 2
        
        # Verify second prompt contains error info
        second_call_args = mock_chat.call_args_list[1]
        assert "Your previous response was invalid" in second_call_args[1]["messages"][0]["content"]

@pytest.mark.asyncio
async def test_schema_context_validation_error_retry():
    """Verify SchemaContext retries on Pydantic validation error."""
    context = SchemaContext(MockModel, max_retries=2)
    
    # score out of range
    wrong_json = json.dumps({"name": "Wrong", "score": 150})
    valid_json = json.dumps({"name": "Corrected", "score": 50})
    
    with patch("api.utils.schema_context.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = [wrong_json, valid_json]
        
        result = await context.query("Test prompt")
        
        assert result["score"] == 50
        assert mock_chat.call_count == 2

@pytest.mark.asyncio
async def test_schema_context_exhaust_retries():
    """Verify SchemaContext returns empty/error dict after exhausting retries."""
    context = SchemaContext(MockModel, max_retries=2)
    
    invalid_json = "STILL NOT JSON"
    
    with patch("api.utils.schema_context.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = invalid_json
        
        result = await context.query("Test prompt")
        
        # Depending on implementation, it might raise or return partial
        # We expect a fallback or error marker
        assert "error" in result
        assert mock_chat.call_count == 3 # Initial + 2 retries
