import pytest
import time
import asyncio
from api.services.coordination_service import get_coordination_service, TaskStatus, AgentStatus, MAX_RETRIES

@pytest.fixture(autouse=True)
def reset_service():
    svc = get_coordination_service()
    svc.shutdown_pool()
    yield
    svc.shutdown_pool()

@pytest.mark.asyncio
async def test_exponential_backoff_timing():
    """Verify that tasks respect exponential backoff delays."""
    svc = get_coordination_service()
    # 1 agent only so it gets busy
    svc.spawn_agent()
    agent_id = list(svc.agents.keys())[0]
    
    # Submit task
    t_id = svc.submit_task({"cmd": "test-backoff"})
    
    # Fail once -> 2^1 = 2s delay
    svc.handle_agent_failure(agent_id)
    task = svc.tasks[t_id]
    assert task.status == TaskStatus.PENDING
    assert task.attempt_count == 1
    assert task.next_retry_at is not None
    
    # Check that _process_delayed_tasks doesn't move it early
    svc._process_delayed_tasks()
    assert t_id not in svc.queue
    
    # Mock time jump
    real_time = time.time
    with pytest.MonkeyPatch().context() as m:
        m.setattr(time, "time", lambda: real_time() + 3)
        svc._process_delayed_tasks()
        assert t_id in svc.queue

@pytest.mark.asyncio
async def test_dead_letter_queue_transition():
    """Verify that tasks move to DLQ after exceeding MAX_RETRIES."""
    svc = get_coordination_service()
    # Ensure some agents exist but we'll manually fail them
    for _ in range(2):
        svc.spawn_agent()
    
    t_id = svc.submit_task({"data": "poison-pill"})
    
    # Exhaust retries
    real_time = time.time
    # First MAX_RETRIES-1 failures allow re-assignment
    for i in range(MAX_RETRIES - 1):
        agent_id = svc.tasks[t_id].assigned_agent_id
        if not agent_id:
            svc._process_delayed_tasks()
            if t_id in svc.queue:
                svc._assign_task(svc.tasks[t_id])
            agent_id = svc.tasks[t_id].assigned_agent_id
            
        assert agent_id is not None, f"Task {t_id} not assigned at iteration {i}"
        svc.handle_agent_failure(agent_id)
        svc.agents[agent_id].status = AgentStatus.IDLE
        
        # Advance time for backoff
        real_time_val = time.time
        with pytest.MonkeyPatch().context() as m:
            m.setattr(time, "time", lambda: real_time_val() + 10)
            svc._process_delayed_tasks()

    # Clear fail history for final assignment so we can exhaust MAX_RETRIES
    svc.tasks[t_id].failed_agent_ids = []
    for a in svc.agents.values():
        a.status = AgentStatus.IDLE

    # Final failure (the 3rd one) triggers DLQ transition
    final_agent_id = svc.tasks[t_id].assigned_agent_id
    if not final_agent_id:
        svc._assign_task(svc.tasks[t_id])
        final_agent_id = svc.tasks[t_id].assigned_agent_id
        
    assert final_agent_id is not None
    svc.handle_agent_failure(final_agent_id)
    assert t_id in svc.dead_letter_queue

@pytest.mark.asyncio
async def test_pool_health_score_dynamics():
    """Verify that health score reacts to failures and isolation breaches."""
    svc = get_coordination_service()
    svc.spawn_agent() # a1
    svc.spawn_agent() # a2
    
    initial_health = svc.get_pool_stats()["pool_health_score"]
    assert initial_health == 1.0
    
    # 1. Force isolation breach
    a1_id, a2_id = list(svc.agents.keys())
    svc.agents[a2_id].context_window_id = svc.agents[a1_id].context_window_id
    
    health_breach = svc.get_pool_stats()["pool_health_score"]
    assert health_breach < initial_health # Deduction for security breach
    
    # 2. Add failures
    t1 = svc.submit_task({"job": "fail"})
    svc.complete_task(t1, success=False, failure_reason="simulation")
    
    health_final = svc.get_pool_stats()["pool_health_score"]
    assert health_final < health_breach # Further deduction for failure rate

@pytest.mark.asyncio
async def test_high_throughput_load_stability():
    """Verify stability under rapid task submission."""
    svc = get_coordination_service()
    svc.initialize_pool(4)
    
    task_ids = []
    for i in range(20):
        t_id = svc.submit_task({"index": i})
        task_ids.append(t_id)
    
    # Check that 4 are in progress, 16 pending
    stats = svc.metrics()
    assert stats["tasks_in_progress"] == 4
    assert stats["queue_length"] == 16
    
    # Complete some tasks and verify queue drains
    for t_id in task_ids[:4]:
        svc.complete_task(t_id)
        
    stats_after = svc.metrics()
    assert stats_after["tasks_completed"] == 4
    assert stats_after["tasks_in_progress"] == 4
    assert stats_after["queue_length"] == 12
