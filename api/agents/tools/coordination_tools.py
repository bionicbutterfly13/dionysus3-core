"""
Class-based tools for coordination pool interactions.
Feature: 020-daedalus-coordination-pool
Tasks: T4.1, T4.2
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.coordination_service import get_coordination_service

class CoordinationPoolOutput(BaseModel):
    status: str = Field(..., description="The current status of the operation")
    spawned_agents: Optional[int] = Field(None, description="Number of agents successfully spawned")
    agent_ids: Optional[List[str]] = Field(None, description="List of spawned agent identifiers")

class InitializeCoordinationPoolTool(Tool):
    name = "initialize_coordination_pool"
    description = "Initialize the coordination pool with a specific number of agents."
    
    inputs = {
        "size": {
            "type": "integer",
            "description": "Number of agents to initialize in the pool.",
            "default": 4,
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, size: int = 4) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = get_coordination_service()
            spawned_ids = service.initialize_pool(size)
            output = CoordinationPoolOutput(
                status="initialized",
                spawned_agents=len(spawned_ids),
                agent_ids=spawned_ids
            )
            return output.model_dump()
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Pool initialization failed: {e}")}

class ShutdownCoordinationPoolTool(Tool):
    name = "shutdown_coordination_pool"
    description = "Gracefully shut down the coordination pool."
    
    inputs = {}
    output_type = "any"

    def forward(self) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = get_coordination_service()
            service.shutdown_pool()
            return {"status": "shutdown_completed"}
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Pool shutdown failed: {e}")}

class SpawnCoordinationAgentOutput(BaseModel):
    agent_id: str = Field(..., description="The unique identifier for the spawned agent")
    context_window_id: str = Field(..., description="The context window identifier for the agent")
    status: str = Field(..., description="The current status of the spawned agent")

class SpawnCoordinationAgentTool(Tool):
    name = "spawn_coordination_agent"
    description = "Spawn a single coordination pool agent and return its identifiers."
    
    inputs = {}
    output_type = "any"

    def forward(self) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = get_coordination_service()
            agent_id = service.spawn_agent()
            agent = service.agents[agent_id]
            output = SpawnCoordinationAgentOutput(
                agent_id=agent.agent_id,
                context_window_id=agent.context_window_id,
                status=agent.status.value
            )
            return output.model_dump()
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Agent spawn failed: {e}")}

class SubmitCoordinationTaskOutput(BaseModel):
    task_id: str = Field(..., description="The unique identifier for the submitted task")
    status: str = Field(..., description="The current status of the task")
    assigned_agent_id: Optional[str] = Field(None, description="The identifier of the agent assigned to the task")

class SubmitCoordinationTaskTool(Tool):
    name = "submit_coordination_task"
    description = "Submit a task to the coordination pool with an optional type."
    
    inputs = {
        "payload": {
            "type": "object",
            "description": "The task payload containing instructions and context."
        },
        "preferred_agent_id": {
            "type": "string",
            "description": "Optional identifier for a specific agent to handle the task.",
            "nullable": True
        },
        "task_type": {
            "type": "string",
            "description": "The category of the task (e.g., general, research, content).",
            "default": "general",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, payload: dict, preferred_agent_id: str | None = None, task_type: str = "general") -> dict:
        from api.agents.resilience import wrap_with_resilience
        from api.services.coordination_service import TaskType
        try:
            service = get_coordination_service()
            try:
                tt = TaskType(task_type)
            except ValueError:
                tt = TaskType.GENERAL
                
            task_id = service.submit_task(payload, preferred_agent_id, tt)
            task = service.tasks[task_id]
            output = SubmitCoordinationTaskOutput(
                task_id=task_id,
                status=task.status.value,
                assigned_agent_id=task.assigned_agent_id
            )
            return output.model_dump()
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Task submission failed: {e}")}

class FailCoordinationAgentTool(Tool):
    name = "fail_coordination_agent"
    description = "Trigger failure handling for a specific agent."
    
    inputs = {
        "agent_id": {
            "type": "string",
            "description": "The identifier of the agent that failed."
        }
    }
    output_type = "any"

    def forward(self, agent_id: str) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = get_coordination_service()
            service.handle_agent_failure(agent_id)
            agent = service.agents.get(agent_id)
            return {"agent_id": agent_id, "status": agent.status.value if agent else "unknown"}
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Agent failure handling failed: {e}")}

class CompleteCoordinationTaskTool(Tool):
    name = "complete_coordination_task"
    description = "Complete a task and trigger queue drain."
    
    inputs = {
        "task_id": {
            "type": "string",
            "description": "The identifier of the task being completed."
        },
        "success": {
            "type": "boolean",
            "description": "Whether the task was completed successfully.",
            "default": True,
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, task_id: str, success: bool = True) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = get_coordination_service()
            service.complete_task(task_id, success=success)
            task = service.tasks.get(task_id)
            return {"task_id": task_id, "status": task.status.value if task else "unknown"}
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Task completion failed: {e}")}

class CoordinationIsolationReportTool(Tool):
    name = "coordination_isolation_report"
    description = "Generate a report on agent isolation status."
    
    inputs = {}
    output_type = "any"

    def forward(self) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = get_coordination_service()
            return service.generate_isolation_report()
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Isolation report failed: {e}")}

class CoordinationMetricsTool(Tool):
    name = "coordination_metrics"
    description = "Return real-time coordination pool metrics."
    
    inputs = {}
    output_type = "any"

    def forward(self) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = get_coordination_service()
            return service.metrics()
        except Exception as e:
            return {"status": "error", "error": wrap_with_resilience(f"Metrics fetch failed: {e}")}

# Export tool instances
initialize_coordination_pool = InitializeCoordinationPoolTool()
shutdown_coordination_pool = ShutdownCoordinationPoolTool()
spawn_coordination_agent = SpawnCoordinationAgentTool()
submit_coordination_task = SubmitCoordinationTaskTool()
fail_coordination_agent = FailCoordinationAgentTool()
complete_coordination_task = CompleteCoordinationTaskTool()
coordination_isolation_report = CoordinationIsolationReportTool()
coordination_metrics = CoordinationMetricsTool()