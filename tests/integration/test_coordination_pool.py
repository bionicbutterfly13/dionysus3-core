import pytest
import time
from api.services.coordination_service import get_coordination_service

@pytest.fixture(autouse=True)
def reset_service():
    svc = get_coordination_service()
    svc.shutdown_pool()
    yield

def test_full_task_lifecycle_integration():
    """T021: Integration test for full task lifecycle (submit → queue → assign → complete)"""
    svc = get_coordination_service()
    svc.initialize_pool(2)
    
    # Submit 3 tasks
    t1 = svc.submit_task({"id": 1})
    t2 = svc.submit_task({"id": 2})
    t3 = svc.submit_task({"id": 3})
    
    assert svc.tasks[t1].status == "in_progress"
    assert svc.tasks[t2].status == "in_progress"
    assert svc.tasks[t3].status == "pending"
    
    svc.complete_task(t1)
    assert svc.tasks[t1].status == "completed"
    assert svc.tasks[t3].status == "in_progress"
