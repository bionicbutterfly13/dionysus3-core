import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

SAMPLE_CODE = """
class LegacyBrain:
    def __init__(self):
        self.awareness = True
    
    def infer_action(self):
        # uses attention and reasoning
        return "decide"

    def recall_memory(self):
        # episodic memory patterns
        return "recalled"
"""

@pytest.fixture
def temp_codebase():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "legacy_module.py"
        test_file.write_text(SAMPLE_CODE)
        yield tmpdir

def test_run_discovery_contract(temp_codebase):
    """T012: Contract test for POST /api/discovery/run"""
    request_data = {
        "codebase_path": temp_codebase,
        "top_n": 5
    }
    
    response = client.post("/api/discovery/run", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    
    if data["count"] > 0:
        res = data["results"][0]
        required_fields = [
            "component_id", "name", "file_path", "composite_score", 
            "migration_recommended", "consciousness", "strategic",
            "enhancement_opportunities", "risk_factors"
        ]
        for field in required_fields:
            assert field in res
        
        # Check nested structures
        assert "awareness_score" in res["consciousness"]
        assert "patterns" in res["consciousness"]
        assert "uniqueness" in res["strategic"]

def test_run_discovery_invalid_path():
    """Verify 400 error for non-existent path"""
    request_data = {
        "codebase_path": "/non/existent/path/at/all",
        "top_n": 5
    }
    response = client.post("/api/discovery/run", json=request_data)
    assert response.status_code == 400
    assert "detail" in response.json()
