import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app
from api.models.mosaeic import MOSAEICCapture

client = TestClient(app)

@pytest.mark.asyncio
async def test_mosaeic_capture_endpoint():
    """T012: Contract test for POST /api/mosaeic/capture"""
    
    mock_json = {
        "senses": {"content": "vision blurry", "intensity": 0.3, "tags": []},
        "actions": {"content": "rubbing eyes", "intensity": 0.4, "tags": []},
        "emotions": {"content": "tiredness", "intensity": 0.6, "tags": []},
        "impulses": {"content": "to sleep", "intensity": 0.8, "tags": []},
        "cognitions": {"content": "it is late", "intensity": 0.9, "tags": []},
        "summary": "Fatigue"
    }
    
    # Mocking BOTH extraction and persistence
    with patch("api.services.mosaeic_service.MOSAEICService.extract_capture", new_callable=AsyncMock) as mock_extract:
        with patch("api.services.mosaeic_service.MOSAEICService.persist_capture", new_callable=AsyncMock) as mock_persist:
            
            mock_extract.return_value = MOSAEICCapture(**mock_json)
            mock_persist.return_value = "episode-123"
            
            response = client.post(
                "/api/mosaeic/capture",
                json={"text": "I am so tired.", "source_id": "test_contract"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["summary"] == "Fatigue"
            assert data["senses"]["content"] == "vision blurry"
            
            mock_extract.assert_called_once()
            mock_persist.assert_called_once()

def test_mosaeic_health():
    response = client.get("/api/mosaeic/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
