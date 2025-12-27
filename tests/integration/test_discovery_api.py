import pytest
from pathlib import Path
from api.services.discovery_service import DiscoveryService

@pytest.fixture
def temp_codebase(tmp_path):
    f = tmp_path / "agent.py"
    f.write_text("""
def observe_and_reason():
    # awareness and inference
    pass
""")
    return tmp_path

@pytest.mark.asyncio
async def test_discovery_api_contract(client, temp_codebase):
    response = await client.post("/api/discovery/run", json={
        "codebase_path": str(temp_codebase),
        "top_n": 5
    })
    assert response.status_code == 200
    data = response.json()
    
    assert "count" in data
    assert "results" in data
    assert len(data["results"]) > 0
    
    res = data["results"][0]
    assert "component_id" in res
    assert "name" in res
    assert "file_path" in res
    assert "composite_score" in res
    assert "migration_recommended" in res
    assert "consciousness" in res
    assert "strategic" in res
    
    # Check consciousness shape
    cons = res["consciousness"]
    assert "awareness_score" in cons
    assert "patterns" in cons
    assert "awareness" in cons["patterns"]

def test_discovery_tool_contract(temp_codebase):
    from api.agents.tools.discovery_tools import discover_components
    
    # tool is a function decorated with @tool, but we can call it directly
    # for testing contract if we ignore the @tool metadata
    result = discover_components.forward(codebase_path=str(temp_codebase), top_n=5)
    
    assert "count" in result
    assert "results" in result
    assert len(result["results"]) > 0
    
    res = result["results"][0]
    assert "component_id" in res
    assert "consciousness" in res
    assert "strategic" in res
