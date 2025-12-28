"""
Monitoring and Metrics Aggregator Service
Feature: 023-migration-observability

Aggregates metrics from Discovery, Coordination, and Rollback services.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from api.services.discovery_service import get_discovery_service
from api.services.coordination_service import get_coordination_service
from api.services.rollback_service import get_rollback_service


class MonitoringService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.utcnow()
        self._current_trace_id: Optional[str] = None

    @property
    def trace_id(self) -> str:
        return self._current_trace_id or "no-trace"

    @trace_id.setter
    def trace_id(self, value: str):
        self._current_trace_id = value

    def _log(self, level: int, event: str, **kwargs):
        extra = kwargs
        extra["trace_id"] = self.trace_id
        self.logger.log(level, event, extra=extra)

    async def get_system_metrics(self) -> Dict:
        coordination = get_coordination_service()
        rollback = get_rollback_service()
        discovery = get_discovery_service()
        
        self._log(logging.INFO, "fetching_system_metrics")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "coordination": coordination.metrics(),
            "discovery": discovery.metrics(),
            "rollback": rollback.metrics(),
            "agents": coordination.agent_health_report()
        }

    async def get_performance_metrics(self) -> Dict:
        coordination = get_coordination_service()
        rollback = get_rollback_service()
        
        all_agents = coordination.list_agents()
        avg_task_time = 0.0
        if all_agents:
            avg_task_time = sum(a.performance.get("average_task_time", 0.0) for a in all_agents) / len(all_agents)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "throughput": {
                "tasks_completed": sum(a.performance.get("tasks_completed", 0) for a in all_agents),
                "tasks_failed": sum(a.performance.get("tasks_failed", 0) for a in all_agents),
            },
            "latency": {
                "average_task_duration_seconds": avg_task_time,
            },
            "utilization": {
                "agent_busy_percentage": self._calculate_agent_utilization(all_agents),
            }
        }

    def _calculate_agent_utilization(self, agents: List) -> float:
        if not agents: return 0.0
        busy = len([a for a in agents if a.status != "idle"])
        return (busy / len(agents)) * 100.0

    async def get_alerts(self) -> List[Dict]:
        alerts = []
        coordination = get_coordination_service()
        rollback = get_rollback_service()
        
        # 1. High queue alert
        if len(coordination.queue) > 10:
            alerts.append({
                "id": "queue_backlog",
                "severity": "warning",
                "message": f"Task queue is backing up ({len(coordination.queue)} items)",
                "timestamp": datetime.utcnow().isoformat()
            })

        # 2. Agent degradation alert
        degraded = [a.agent_id for a in coordination.list_agents() if a.status == "degraded"]
        if degraded:
            alerts.append({
                "id": "agents_degraded",
                "severity": "critical",
                "message": f"{len(degraded)} agents are in DEGRADED state",
                "affected": degraded,
                "timestamp": datetime.utcnow().isoformat()
            })

        # 3. Rollback failure alert
        failed_rollbacks = [r for r in rollback.history[-5:] if not r.success]
        if failed_rollbacks:
            alerts.append({
                "id": "rollback_failures",
                "severity": "critical",
                "message": f"Detected {len(failed_rollbacks)} recent rollback failures",
                "timestamp": datetime.utcnow().isoformat()
            })

        return alerts


_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
