import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.mosaeic_service import MOSAEICService
from api.models.mosaeic import MOSAEICCapture

@pytest.mark.asyncio
async def test_extract_capture_success():
    service = MOSAEICService()
    
    mock_json = {
        "senses": {"content": "tension in neck", "intensity": 0.7, "tags": ["physical"]},
        "actions": {"content": "working late", "intensity": 0.5, "tags": []},
        "emotions": {"content": "anxiety", "intensity": 0.8, "tags": ["stress"]},
        "impulses": {"content": "to quit", "intensity": 0.4, "tags": []},
        "cognitions": {"content": "I am behind", "intensity": 0.9, "tags": ["belief"]},
        "summary": "High work stress"
    }
    
    with patch("api.services.mosaeic_service.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = f"```json\n{import_json(mock_json)}\n```"
        
        capture = await service.extract_capture("I feel very stressed at work today.", source_id="test_unit")
        
        assert isinstance(capture, MOSAEICCapture)
        assert capture.summary == "High work stress"
        assert capture.senses.content == "tension in neck"
        assert capture.senses.intensity == 0.7
        assert capture.source_id == "test_unit"

def import_json(data):
    import json
    return json.dumps(data)

@pytest.mark.asyncio
async def test_persist_capture():
    service = MOSAEICService()
    
    mock_capture = MagicMock(spec=MOSAEICCapture)
    mock_capture.summary = "Stressful day"
    mock_capture.source_id = "test_user"
    mock_capture.timestamp = None
    
    # Mock windows
    mock_capture.senses = MagicMock(content="tension", intensity=0.8)
    mock_capture.actions = MagicMock(content="typing", intensity=0.2)
    mock_capture.emotions = MagicMock(content="fear", intensity=0.1) # low intensity
    mock_capture.impulses = MagicMock(content="run", intensity=0.5)
    mock_capture.cognitions = MagicMock(content="danger", intensity=0.9)
    
    with patch("api.services.mosaeic_service.get_graphiti_service", new_callable=AsyncMock) as mock_get_graphiti:
        mock_graphiti = AsyncMock()
        mock_get_graphiti.return_value = mock_graphiti
        
        await service.persist_capture(mock_capture)
        
        # Should ingest summary
        # And windows with intensity > 0.1: Senses (0.8), Actions (0.2), Impulses (0.5), Cognitions (0.9)
        # Emotions (0.1) should be skipped
        
        assert mock_graphiti.ingest_message.call_count == 5 
