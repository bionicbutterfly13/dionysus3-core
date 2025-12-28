import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.services.monitoring_service import get_monitoring_service
from api.services.coordination_service import get_coordination_service
from api.services.rollback_service import get_rollback_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_services():
    # Reset coordination
    coord = get_coordination_service()
    coord.agents.clear()
    coord.tasks.clear()
    coord.queue.clear()
    
    # Reset rollback
    rollback = get_rollback_service()
    rollback.checkpoints.clear()
    rollback.history.clear()
    yield

def test_metrics_aggregation_contract():
    """T010: Contract test for GET /metrics aggregation"""
    response = client.get("/api/monitoring/metrics")
    assert response.status_code == 200
    data = response.json()
    
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert "coordination" in data
    assert "discovery" in data
    assert "rollback" in data
    assert "agents" in data

def test_performance_metrics_contract():
    """T010: Contract test for GET /performance stats"""
    # Spawn an agent and complete a task to have some data
    coord = get_coordination_service()
    agent_id = coord.spawn_agent()
    task_id = coord.submit_task({"cmd": "test"})
    coord.complete_task(task_id)
    
    response = client.get("/api/monitoring/performance")
    assert response.status_code == 200
    data = response.json()
    
    assert "throughput" in data
    assert "latency" in data
    assert "utilization" in data
    assert data["throughput"]["tasks_completed"] >= 1

def test_alerts_induced_queue_backlog():
    """T011: Induced alert test for queue backlog"""
    coord = get_coordination_service()
    # Fill the queue (backlog alert triggers if > 10)
    for i in range(15):
        # We don't spawn agents, so they will all be queued
        coord.submit_task({"i": i})
    
    response = client.get("/api/monitoring/alerts")
    assert response.status_code == 200
    alerts = response.json()
    
    assert any(a["id"] == "queue_backlog" for a in alerts)
    backlog_alert = next(a for a in alerts if a["id"] == "queue_backlog")
    assert backlog_alert["severity"] == "warning"

def test_alerts_induced_agent_degradation():
    """T011: Induced alert test for agent degradation"""
    coord = get_coordination_service()
    agent_id = coord.spawn_agent()
    coord.submit_task({"cmd": "fail"})
    coord.handle_agent_failure(agent_id) # This sets status to DEGRADED
    
    response = client.get("/api/monitoring/alerts")
    assert response.status_code == 200
    alerts = response.json()
    
    assert any(a["id"] == "agents_degraded" for a in alerts)
    degraded_alert = next(a for a in alerts if a["id"] == "agents_degraded")
    assert degraded_alert["severity"] == "critical"
    assert agent_id in degraded_alert["affected"]

def test_tracing_correlation_contract():
    """T009: Verify trace_id correlation in monitoring responses"""
    trace_id = "test-trace-123"
    response = client.get("/api/monitoring/metrics", headers={"x-trace-id": trace_id})
    assert response.status_code == 200
    
    # Check if cognitive endpoint returns it (I added it there explicitly)
    response = client.get("/api/monitoring/cognitive", headers={"x-trace-id": trace_id})
    assert response.status_code == 200
    assert response.json()["trace_id"] == trace_id
