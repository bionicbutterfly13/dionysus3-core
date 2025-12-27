"""
Monitoring and Metrics Aggregator Service
Feature: 023-migration-observability

Aggregates metrics from Discovery, Coordination, and Rollback services.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from api.services.discovery_service import get_discovery_service
from api.services.coordination_service import get_coordination_service
from api.services.rollback_service import get_rollback_service


class MonitoringService:
    def __init__(self):
        self.start_time = datetime.utcnow()

    async def get_system_metrics(self) -> Dict:
        coordination = get_coordination_service()
        rollback = get_rollback_service()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "coordination": coordination.metrics(),
            "rollback": {
                "total_checkpoints": len(rollback.checkpoints),
                "history_count": len(rollback.history),
                "last_rollback_success": rollback.history[0].success if rollback.history else None
            },
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
