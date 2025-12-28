import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app
from api.services.rollback_service import get_rollback_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_service():
    svc = get_rollback_service()
    svc.checkpoints.clear()
    svc.history.clear()
    yield

def test_checkpoint_lifecycle_contract():
    """T005, T009: Contract test for rollback checkpoint lifecycle"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        tmp.write(b"original_content")
        tmp_path = tmp.name
    
    try:
        # 1. Create Checkpoint
        request_data = {
            "component_id": "test_component",
            "file_path": tmp_path,
            "related_files": [],
            "retention_days": 1
        }
        response = client.post("/api/rollback/checkpoints", json=request_data)
        assert response.status_code == 200
        checkpoint_id = response.json()["checkpoint_id"]
        assert checkpoint_id is not None
        
        # 2. List Checkpoints
        response = client.get("/api/rollback/checkpoints")
        assert response.status_code == 200
        checkpoints = response.json()
        assert any(c["checkpoint_id"] == checkpoint_id for c in checkpoints)
        
        # 3. Mutate file
        Path(tmp_path).write_text("mutated_content")
        
        # 4. Perform Rollback
        rollback_request = {
            "checkpoint_id": checkpoint_id,
            "backup_current": False
        }
        response = client.post("/api/rollback/run", json=rollback_request)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 5. Verify file restored
        assert Path(tmp_path).read_text() == "original_content"
        
        # 6. Check History
        response = client.get("/api/rollback/history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) >= 1
        assert history[0]["checkpoint_id"] == checkpoint_id
        assert history[0]["success"] is True

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_cleanup_expired_contract():
    """T005: Contract test for POST /api/rollback/cleanup"""
    response = client.post("/api/rollback/cleanup")
    assert response.status_code == 200
    assert "cleaned_count" in response.json()
