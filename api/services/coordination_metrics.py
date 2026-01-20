from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger("dionysus.coordination.metrics")

class CoordinationMetrics:
    """
    Observability layer for the Daedalus Coordination Pool.
    Tracks agent lifecycle events, failures, and performance timing.
    """
    
    def __init__(self):
        # Counters
        self.tasks_submitted: int = 0
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.tasks_retried: int = 0
        
        # Histograms (Simulated lists for now)
        self.execution_times: list[float] = []
        self.routing_latency: list[float] = []
        
        # Agent Health
        self.agent_failures: Dict[str, int] = {}
        
    def record_submission(self, task_id: str, agent_id: str):
        """Log a new task submission."""
        self.tasks_submitted += 1
        logger.info(f"[METRIC] Task Submitted: {task_id} -> {agent_id}")
        
    def record_completion(self, task_id: str, duration_sec: float):
        """Log a successful completion."""
        self.tasks_completed += 1
        self.execution_times.append(duration_sec)
        logger.info(f"[METRIC] Task Completed: {task_id} in {duration_sec:.4f}s")
        
    def record_failure(self, task_id: str, agent_id: str, error: str):
        """Log a task failure."""
        self.tasks_failed += 1
        self.agent_failures[agent_id] = self.agent_failures.get(agent_id, 0) + 1
        logger.error(f"[METRIC] Task Failed: {task_id} ({agent_id}) - {error}")
        
    def record_retry(self, task_id: str, attempt: int):
        """Log a retry attempt."""
        self.tasks_retried += 1
        logger.warning(f"[METRIC] Task Retry: {task_id} (Attempt {attempt})")
        
    def get_snapshot(self) -> Dict[str, Any]:
        """Return current metrics state."""
        avg_exec = sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0.0
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "throughput": {
                "submitted": self.tasks_submitted,
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "retried": self.tasks_retried
            },
            "performance": {
                "avg_execution_sec": avg_exec,
                "samples": len(self.execution_times)
            },
            "health": {
                "agent_failure_counts": self.agent_failures
            }
        }

_metrics_instance: Optional[CoordinationMetrics] = None

def get_coordination_metrics() -> CoordinationMetrics:
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = CoordinationMetrics()
    return _metrics_instance
