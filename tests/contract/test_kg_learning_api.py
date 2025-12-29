import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from api.main import app
from api.models.kg_learning import RelationshipProposal

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_review_queue_contract():
    """T013: Contract test for GET /api/kg/review-queue"""
    
    mock_proposal = {
        "source": "ConceptX",
        "target": "ConceptY",
        "type": "RELATES_TO",
        "confidence": 0.4,
        "evidence": "Mentioned in passing",
        "run_id": "run-123",
        "status": "pending_review"
    }
    
    with patch("api.routers.kg_learning.get_kg_learning_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_get_svc.return_value = mock_svc
        mock_svc._driver = AsyncMock()
        
        # Mock the driver response for the cypher query
        mock_svc._driver.execute_query.return_value = [{"r": mock_proposal}]
        
        response = client.get("/api/kg/review-queue")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["source"] == "ConceptX"
        assert data[0]["status"] == "pending_review"

from unittest.mock import MagicMock
