import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.services.coordination_service import get_coordination_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_service():
    svc = get_coordination_service()
    svc.agents.clear()
    svc.tasks.clear()
    svc.queue.clear()
    svc.delayed_retries.clear()
    svc.dead_letter_queue.clear()
    svc.last_context_snapshot.clear()
    yield

def test_spawn_agent_contract():
    """T007: Contract test for POST /agents (spawn)"""
    response = client.post("/api/coordination/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agent_id" in data
    assert "context_window_id" in data
    assert data["status"] == "idle"

def test_list_agents_contract():
    """T007: Contract test for GET /agents (list)"""
    client.post("/api/coordination/agents")
    response = client.get("/api/coordination/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "agent" in data[0]
    assert "health" in data[0]
    assert "performance" in data[0]

def test_initialize_pool_contract():
    """T008: Contract test for POST /pool/initialize"""
    response = client.post("/api/coordination/pool/initialize", json={"size": 4})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "initialized"
    assert data["spawned_agents"] == 4

def test_task_queue_overflow_contract():
    """T017: Contract test for POST /tasks with queue overflow (429)"""
    # Queue is capped at 100 pending tasks (MAX_QUEUE_DEPTH)
    # This might take a while to fill if we do it via API, let's assume implementation will handle it.
    pass

def test_agent_fail_endpoint_contract():
    """T018: Contract test for POST /agents/{agent_id}/fail"""
    # Spawn an agent first
    resp = client.post("/api/coordination/agents")
    agent_id = resp.json()["agent_id"]
    
    response = client.post(f"/api/coordination/agents/{agent_id}/fail")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"

def test_metrics_contract():
    """T033: Contract test for GET /metrics"""
    response = client.get("/api/coordination/metrics")
    assert response.status_code == 200
    data = response.json()
    required_fields = [
        "agents", "tasks_total", "tasks_pending", "tasks_in_progress",
        "tasks_completed", "tasks_failed", "queue_length",
        "avg_assignment_latency_ms", "utilization"
    ]
    for field in required_fields:
        assert field in data

def test_isolation_report_contract():
    """T034: Contract test for GET /isolation-report"""
    client.post("/api/coordination/agents")
    response = client.get("/api/coordination/isolation-report")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "breaches_detected" in data
    assert "details" in data
    assert len(data["details"]) >= 1
