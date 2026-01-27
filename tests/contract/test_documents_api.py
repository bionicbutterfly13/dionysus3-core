"""
Contract tests for Documents API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from api.services.document_lifecycle import Document, DocumentStatus

class _FakeDocumentService:
    def __init__(self):
        self.results_dir = MagicMock()

    async def get_document(self, doc_id):
        return Document(
            doc_id=doc_id,
            original_filename="test.pdf",
            status=DocumentStatus.COMPLETED,
            metadata={}
        )

    async def list_documents(self, status=None, limit=100, offset=0):
        return []

    async def get_stats(self):
        return {"total": 0}

@pytest.fixture
def app():
    import api.routers.documents as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_list_documents_contract(client):
    """GET /api/documents returns documents list."""
    import api.routers.documents as router
    
    with patch("api.routers.documents.get_document_service", return_value=_FakeDocumentService()):
        response = client.get("/api/documents")
        
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data

def test_get_stats_contract(client):
    """GET /api/documents/stats returns statistics."""
    import api.routers.documents as router
    
    with patch("api.routers.documents.get_document_service", return_value=_FakeDocumentService()):
        response = client.get("/api/documents/stats")
        
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
