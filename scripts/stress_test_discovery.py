
import asyncio
import time
import random
import uuid
from typing import List, Dict
from datetime import datetime

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.coordination_service import get_coordination_service, TaskType, TaskStatus, AgentStatus

# Configuration
TEST_AGENTS = 8
ROOT_TASKS = 5
MAX_RECURSION_DEPTH = 3
TASKS_PER_NODE = 2
TOTAL_TARGET = 50

async def worker_loop(agent_id: str):
    """
    Simulates a Coordination Pool worker polling the CoordinationService.
    """
    svc = get_coordination_service()
    processed_count = 0
    
    print(f"👷 Agent {agent_id[:8]} started.")
    
    while True:
        # Find the task assigned to this agent
        agent = svc.agents.get(agent_id)
        if not agent:
            break
            
        task_id = agent.current_task_id
        if task_id:
            task = svc.tasks[task_id]
            depth = task.payload.get("depth", 0)
            
            # Simulate "Discovery" work
            # print(f"  [{agent_id[:8]}] Working on {task_id[:8]} (depth {depth})...")
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Decide if we recurse
            if depth < MAX_RECURSION_DEPTH:
                for _ in range(TASKS_PER_NODE):
                    svc.submit_task({
                        "id": str(uuid.uuid4()),
                        "depth": depth + 1,
                        "source": task_id
                    }, task_type=TaskType.DISCOVERY)
            
            # Complete task
            svc.complete_task(task_id, success=True)
            processed_count += 1
        else:
            # Nothing assigned, wait a bit
            await asyncio.sleep(0.1)
            
        # Stop condition for this simulation
        if len(svc.tasks) >= TOTAL_TARGET and not any(a.current_task_id for a in svc.agents.values()):
            break

    print(f"🏁 Agent {agent_id[:8]} finished. Processed: {processed_count}")

async def run_stress_test():
    svc = get_coordination_service()
    
    print("🚀 Initializing Coordination Pool Stress Test...")
    svc.shutdown_pool()
    agent_ids = svc.initialize_pool(size=TEST_AGENTS)
    
    start_time = time.time()
    
    # Submit root tasks
    print(f"📤 Submitting {ROOT_TASKS} root tasks...")
    for i in range(ROOT_TASKS):
        svc.submit_task({"id": f"root-{i}", "depth": 0}, task_type=TaskType.DISCOVERY)
    
    # Run worker loops
    workers = [worker_loop(aid) for aid in agent_ids]
    
    # Metrics monitoring task
    async def monitor():
        while True:
            stats = svc.get_pool_stats()
            print(f"📊 Stats: Queue={stats['queue_length']} | InProgress={stats['tasks_in_progress']} | Completed={stats['tasks_completed']} | Health={stats['pool_health_score']:.2f} | Latency={stats['avg_assignment_latency_ms']:.1f}ms")
            
            if stats['tasks_completed'] >= TOTAL_TARGET or (stats['tasks_pending'] == 0 and stats['tasks_in_progress'] == 0 and stats['tasks_completed'] > 0):
                break
            await asyncio.sleep(1.0)

    monitor_task = asyncio.create_task(monitor())
    
    await asyncio.gather(*workers)
    await monitor_task
    
    end_time = time.time()
    duration = end_time - start_time
    
    final_stats = svc.get_pool_stats()
    print("\n" + "="*50)
    print("      COORDINATION POOL STRESS TEST COMPLETED")
    print("="*50)
    print(f"Duration:         {duration:.2f}s")
    print(f"Total Tasks:      {final_stats['tasks_total']}")
    print(f"Completed:        {final_stats['tasks_completed']}")
    print(f"Utilization:      {final_stats['utilization']*100:.1f}%")
    print(f"Avg Latency:      {final_stats['avg_assignment_latency_ms']:.2f}ms")
    print(f"Health Score:     {final_stats['pool_health_score']:.2f}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_stress_test())
