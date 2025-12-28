import pytest
import uuid
from api.services.coordination_service import get_coordination_service, PoolFullError, MAX_POOL_SIZE

@pytest.fixture(autouse=True)
def reset_service():
    svc = get_coordination_service()
    svc.agents.clear()
    svc.tasks.clear()
    svc.queue.clear()
    svc.last_context_snapshot.clear()
    yield

def test_spawn_agent_pool_limit():
    """T009: Unit test for spawn_agent with pool size limit enforcement"""
    svc = get_coordination_service()
    
    # Fill the pool
    for _ in range(MAX_POOL_SIZE):
        svc.spawn_agent()
    
    assert len(svc.agents) == MAX_POOL_SIZE
    
    # Next spawn should raise PoolFullError
    # Note: T012 is not yet implemented, so this will likely FAIL if we run it now.
    with pytest.raises(PoolFullError):
        svc.spawn_agent()

def test_isolation_check_concurrent_agents():
    """T010: Unit test for isolation check between concurrent agents"""
    svc = get_coordination_service()
    
    a1_id = svc.spawn_agent()
    a2_id = svc.spawn_agent()
    
    a1 = svc.agents[a1_id]
    a2 = svc.agents[a2_id]
    
    # Verify they have unique IDs
    assert a1.context_window_id != a2.context_window_id
    assert a1.tool_session_id != a2.tool_session_id
    assert a1.memory_handle_id != a2.memory_handle_id
    
    # Force a collision
    a2.context_window_id = a1.context_window_id
    svc._check_isolation(a2)
    
    assert a2.isolation["shared_state_detected"] is True
    assert any("context_window_id" in note for note in a2.isolation["notes"])

def test_task_queueing_and_routing():
    """T019: Unit test for task queueing and auto-routing on agent free"""
    svc = get_coordination_service()
    svc.spawn_agent() # Only 1 agent
    
    t1 = svc.submit_task({"t": 1})
    t2 = svc.submit_task({"t": 2})
    
    assert svc.tasks[t1].status == "in_progress"
    assert svc.tasks[t2].status == "pending"
    assert len(svc.queue) == 1
    
    svc.complete_task(t1)
    assert svc.tasks[t1].status == "completed"
    assert svc.tasks[t2].status == "in_progress"
    assert len(svc.queue) == 0

def test_retry_logic_and_failover():
    """T020: Unit test for retry logic (3 attempts, failover to different agent)"""
    svc = get_coordination_service()
    a1_id = svc.spawn_agent()
    a2_id = svc.spawn_agent()
    
    # Submit task, should go to a1 (first IDLE)
    t_id = svc.submit_task({"cmd": "fail-me"})
    assert svc.tasks[t_id].assigned_agent_id == a1_id
    
    # Fail agent 1
    svc.handle_agent_failure(a1_id)
    
    # Should have retried on a2
    assert svc.tasks[t_id].assigned_agent_id == a2_id
    assert svc.tasks[t_id].attempt_count == 1
    assert a1_id in svc.tasks[t_id].failed_agent_ids
    assert svc.agents[a1_id].status == "degraded"
    
    # Fail agent 2
    svc.handle_agent_failure(a2_id)
    
    # No IDLE agents left (both degraded), should be at front of queue
    assert svc.tasks[t_id].status == "pending"
    assert svc.tasks[t_id].attempt_count == 2
    assert svc.queue[0] == t_id

def test_metrics_calculation():
    """T035: Unit test for metrics calculation (utilization, latency avg)"""
    svc = get_coordination_service()
    svc.shutdown_pool()
    svc.spawn_agent() # 1 agent
    
    t1 = svc.submit_task({"id": 1})
    m = svc.metrics()
    assert m["utilization"] == 1.0 # 1 busy / 1 total
    assert m["tasks_in_progress"] == 1
    assert m["tasks_pending"] == 0
    
    svc.complete_task(t1)
    m = svc.metrics()
    assert m["utilization"] == 0.0
    assert m["tasks_completed"] == 1
    assert m["avg_assignment_latency_ms"] >= 0

def test_graceful_degradation_discovery_unavailable(monkeypatch):
    """T044: Unit test for graceful degradation (discovery tasks queue, others process)"""
    from api.services.coordination_service import TaskType
    svc = get_coordination_service()
    svc.shutdown_pool()
    svc.spawn_agent()
    
    # Mock discovery service unavailability
    monkeypatch.setattr(svc, "_is_discovery_service_available", lambda: False)
    
    # DISCOVERY task should NOT be assigned, stays pending
    t1 = svc.submit_task({"id": "d1"}, task_type=TaskType.DISCOVERY)
    assert svc.tasks[t1].status == "pending"
    assert len(svc.queue) == 1
    
    # HEARTBEAT task should be assigned
    t2 = svc.submit_task({"id": "h1"}, task_type=TaskType.HEARTBEAT)
    assert svc.tasks[t2].status == "in_progress"
    assert svc.tasks[t2].assigned_agent_id is not None
