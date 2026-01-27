"""
Agent Fleet Models (formerly Coordination Pool)

Feature: 095-coordination-pool-rename
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    DEGRADED = "degraded"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, enum.Enum):
    """
    Standardized Task Types aligned with OODA phases.
    """
    GENERAL = "general"
    RESEARCH = "research"  # Observe/Orient
    DESIGN = "design"      # Orient/Decide
    EXECUTE = "execute"    # Act
    AUDIT = "audit"        # Metacognition
    DISCOVERY = "discovery" # KG Learning


@dataclass
class FleetAgent:
    """Represents an autonomous agent in the fleet."""
    agent_id: str
    context_window_id: str
    tool_session_id: str
    memory_handle_id: str
    status: AgentStatus = AgentStatus.IDLE
    assigned_task_id: Optional[str] = None
    last_active: float = field(default_factory=time.time)
    errors: int = 0


@dataclass
class FleetTask:
    """Represents a discrete unit of work for the fleet."""
    task_id: str
    payload: Dict[str, Any]
    task_type: TaskType = TaskType.GENERAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    attempt_count: int = 0
    assignment_latency_ms: Optional[float] = None


class FleetStatus(BaseModel):
    """Summary of fleet health and activity."""
    agents_total: int
    agents_idle: int
    tasks_pending: int
    tasks_in_progress: int
    tasks_completed_today: int
    tasks_failed_today: int
    utilization: float
    health_score: float # 0.0 - 1.0
