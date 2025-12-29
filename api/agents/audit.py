import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from smolagents.memory import ActionStep, PlanningStep, CallbackRegistry

logger = logging.getLogger(__name__)

class AgentAuditCallback:
    """
    Callback handler for smolagents steps.
    Sends real-time telemetry to n8n for observability.
    """
    def __init__(self, webhook_url: Optional[str] = None, project_id: str = "dionysus"):
        self.webhook_url = webhook_url or os.getenv(
            "N8N_AUDIT_WEBHOOK_URL", 
            "http://72.61.78.89:5678/webhook/memory/v1/ingest/agent-step"
        )
        self.project_id = project_id
        self._client = httpx.AsyncClient(timeout=5.0)

    async def on_step(self, step: Any, agent_name: str, trace_id: str = "no-trace"):
        """
        Processes a single agent step and forwards to webhook.
        """
        payload = {
            "project_id": self.project_id,
            "agent_name": agent_name,
            "trace_id": trace_id,
            "step_number": getattr(step, "step_number", 0),
            "step_type": type(step).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if isinstance(step, ActionStep):
            # Capture tool calls or code actions
            payload["tool_calls"] = []
            if hasattr(step, "tool_calls") and step.tool_calls:
                payload["tool_calls"] = [
                    {"name": c.name, "arguments": c.arguments}
                    for c in step.tool_calls
                ]
            
            # Use getattr to be safe with different versions
            payload["observation"] = str(getattr(step, "observation", ""))[:1000]
            payload["error"] = str(step.error) if getattr(step, "error", None) else None
            
            if hasattr(step, "code_action"):
                payload["code_action"] = str(step.code_action)[:2000]

        elif isinstance(step, PlanningStep):
            payload["plan"] = str(getattr(step, "plan", ""))[:2000]

        # Non-blocking async call
        try:
            # We use a background task to not slow down the agent execution loop
            asyncio.create_task(self._send_payload(payload))
        except Exception as e:
            logger.warning(f"Failed to queue audit payload: {e}")

    async def _send_payload(self, payload: Dict[str, Any]):
        try:
            await self._client.post(self.webhook_url, json=payload)
        except Exception as e:
            # We don't want audit failures to crash the agent
            logger.error(f"Audit webhook failed: {e}")

    def get_registry(self, agent_name: str, trace_id: str = "no-trace") -> Dict:
        """
        Returns a dictionary of callbacks configured for this audit instance.
        """
        def handle_action(step, **kwargs):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.on_step(step, agent_name, trace_id), 
                        loop
                    )
                else:
                    asyncio.run(self.on_step(step, agent_name, trace_id))
            except Exception:
                pass # Audit failure should not break agent

        def handle_planning(step, **kwargs):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.on_step(step, agent_name, trace_id), 
                        loop
                    )
                else:
                    asyncio.run(self.on_step(step, agent_name, trace_id))
            except Exception:
                pass

        return {
            ActionStep: handle_action,
            PlanningStep: handle_planning
        }

_global_audit: Optional[AgentAuditCallback] = None

def get_audit_callback(project_id: str = "dionysus") -> AgentAuditCallback:
    global _global_audit
    if _global_audit is None:
        _global_audit = AgentAuditCallback(project_id=project_id)
    return _global_audit
