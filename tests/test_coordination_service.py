from api.services.coordination_service import get_coordination_service, TaskStatus


def test_queue_and_assignment_flow():
    svc = get_coordination_service()
    svc.agents.clear()
    svc.tasks.clear()
    svc.queue.clear()

    # Spawn one agent
    agent_id = svc.spawn_agent()

    # Submit two tasks, second should queue
    first = svc.submit_task({"name": "t1"})
    second = svc.submit_task({"name": "t2"})

    assert svc.tasks[first].status == TaskStatus.IN_PROGRESS
    assert svc.tasks[second].status == TaskStatus.PENDING
    assert len(svc.queue) == 1

    # Complete first -> second should start
    svc.complete_task(first, success=True)
    assert svc.tasks[first].status == TaskStatus.COMPLETED
    assert svc.tasks[second].status == TaskStatus.IN_PROGRESS


def test_preferred_agent_assignment():
    svc = get_coordination_service()
    svc.agents.clear()
    svc.tasks.clear()
    svc.queue.clear()

    a1 = svc.spawn_agent()
    a2 = svc.spawn_agent()

    task_id = svc.submit_task({"name": "preferred"}, preferred_agent_id=a2)
    assert svc.tasks[task_id].assigned_agent_id == a2
