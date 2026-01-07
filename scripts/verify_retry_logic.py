import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from api.services.coordination_service import get_coordination_service, AgentStatus, TaskStatus

def run_tests():
    print("=== Verifying Daedalus Phase 3: Retry Logic & DLQ ===")
    
    svc = get_coordination_service()
    svc.shutdown_pool() # Clean start
    
    agent_id = svc.spawn_agent()
    print(f"Spawned agent: {agent_id}")
    
    # 1. Test Exponential Backoff
    print("\n[Test 1] Testing Exponential Backoff...")
    task_id = svc.submit_task({"data": "fail_me"})
    task = svc.tasks[task_id]
    
    print(f"Task submitted: {task_id}. Assigned to: {task.assigned_agent_id}")
    
    # Simulate Failure #1
    svc.handle_agent_failure(task.assigned_agent_id)
    
    # Check if task is in delayed_retries
    is_delayed = any(t[1] == task_id for t in svc.delayed_retries)
    if is_delayed and task_id not in svc.queue:
        print("PASS: Task moved to delayed_retries and NOT in main queue.")
    else:
        print(f"FAIL: Task state incorrect. Delayed: {is_delayed}, In Queue: {task_id in svc.queue}")
        return

    # Check Backoff Time (should be ~2s)
    delay = task.next_retry_at - time.time()
    print(f"Backoff delay: {delay:.2f}s (Expected ~2s)")
    if 1.0 < delay < 3.0:
        print("PASS: Backoff duration correct.")
    else:
        print("FAIL: Backoff duration incorrect.")
        return

    # 2. Test Retry Promotion
    print("\n[Test 2] Testing Retry Promotion...")
    print("Waiting for backoff to expire...")
    time.sleep(2.5)
    
    # Trigger processing (simulate activity)
    svc._process_delayed_tasks()
    
    if task_id in svc.queue:
        print("PASS: Task moved back to main queue.")
    else:
        print("FAIL: Task did not move to main queue.")
        return

    # 3. Test Dead Letter Queue
    print("\n[Test 3] Testing Dead Letter Queue...")
    # Manually exhaust retries
    from api.services.coordination_service import MAX_RETRIES
    task.attempt_count = MAX_RETRIES
    
    # Assign and fail again
    svc._assign_task(task)
    svc.handle_agent_failure(task.assigned_agent_id)
    
    if task_id in svc.dead_letter_queue:
        print("PASS: Task moved to DLQ.")
    else:
        print("FAIL: Task NOT in DLQ.")
        return
        
    if task.status == TaskStatus.FAILED:
         print("PASS: Task status is FAILED.")
    else:
         print(f"FAIL: Task status is {task.status}")

    # 4. Test DLQ Replay
    print("\n[Test 4] Testing DLQ Replay...")
    svc.replay_dead_letter_task(task_id)
    
    if task_id not in svc.dead_letter_queue and (task_id in svc.queue or task.status == TaskStatus.IN_PROGRESS):
        print("PASS: Task rescued from DLQ.")
    else:
        print("FAIL: Task not rescued correctly.")
        return

    print("\n=== ALL RETRY TESTS PASSED ===")

if __name__ == "__main__":
    run_tests()
