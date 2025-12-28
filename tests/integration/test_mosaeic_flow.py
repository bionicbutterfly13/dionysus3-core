import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.mosaeic_service import get_mosaeic_service
from api.agents.tools.mosaeic_tools import mosaeic_capture
from api.models.mosaeic import MOSAEICCapture

@pytest.mark.asyncio
async def test_full_mosaeic_capture_flow():
    """Verify flow from raw text to structured capture and persistence."""
    service = get_mosaeic_service()
    
    test_text = "I felt my heart racing as I walked into the presentation. I wanted to run away, but I just stood there and started speaking. I kept thinking I would fail."
    
    # 1. Test Extraction (Mocking LLM)
    mock_capture_data = {
        "senses": {"content": "heart racing", "intensity": 0.8, "tags": []},
        "actions": {"content": "stood and spoke", "intensity": 0.6, "tags": []},
        "emotions": {"content": "fear/anxiety", "intensity": 0.9, "tags": []},
        "impulses": {"content": "to run away", "intensity": 0.7, "tags": []},
        "cognitions": {"content": "I will fail", "intensity": 0.8, "tags": []},
        "summary": "Performance anxiety during presentation"
    }
    
    with patch("api.services.mosaeic_service.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "```json\n" + json.dumps(mock_capture_data) + "\n```"
        
        # 2. Test Persistence (Mocking Graphiti)
        with patch("api.services.mosaeic_service.get_graphiti_service", new_callable=AsyncMock) as mock_get_graphiti:
            mock_graphiti = AsyncMock()
            mock_get_graphiti.return_value = mock_graphiti
            mock_graphiti.ingest_message.return_value = {"episode_uuid": "ep-123"}
            
            # Execute capture via tool (which calls service)
            result = mosaeic_capture(test_text, source_id="test_integration")
            
            # 3. Verify results
            assert "MOSAEIC Capture Successful" in result
            assert "Performance anxiety" in result
            assert "heart racing" in result
            
            # Verify Graphiti was called for summary + 5 windows
            assert mock_graphiti.ingest_message.call_count == 6
