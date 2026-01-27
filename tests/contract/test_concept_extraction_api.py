"""
Contract tests for Concept Extraction API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from api.models.concept_extraction import (
    ConceptExtractionLevel,
    FiveLevelExtractionResult,
    LevelExtractionResult,
    ExtractedConcept
)

class _FakeConceptService:
    async def extract_all(self, content, context, document_id):
        return FiveLevelExtractionResult(
            document_id=document_id,
            all_concepts=[ExtractedConcept(id="c1", name="Test", level=ConceptExtractionLevel.ATOMIC, description="test")],
            level_results={},
            cross_level_relationships=[],
            concept_hierarchy={}
        )

    def get_extractor(self, level):
        mock_extractor = AsyncMock()
        mock_extractor.extract = AsyncMock(return_value=LevelExtractionResult(
            level=level,
            concepts=[ExtractedConcept(id="c1", name="Test", level=level, description="test")],
            local_relationships=[]
        ))
        return mock_extractor

@pytest.fixture
def app():
    import api.routers.concept_extraction as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_extract_concepts_contract(client):
    """POST /api/concepts/extract returns full extraction result."""
    import api.routers.concept_extraction as router
    
    with patch("api.routers.concept_extraction.get_concept_extraction_service", return_value=_FakeConceptService()):
        response = client.post(
            "/api/concepts/extract",
            json={"content": "Test content", "document_id": "doc-1"}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc-1"
    assert len(data["all_concepts"]) > 0

def test_list_levels_contract(client):
    """GET /api/concepts/levels returns levels list."""
    response = client.get("/api/concepts/levels")
    assert response.status_code == 200
    data = response.json()
    assert "levels" in data
    assert len(data["levels"]) == 5
