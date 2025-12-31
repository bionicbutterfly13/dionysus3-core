import logging
from datetime import datetime
from typing import Any, Dict, Optional

from smolagents.memory import AgentMemory
from api.services.remote_sync import RemoteSyncService

logger = logging.getLogger(__name__)

class AgentMemoryService:
    """
    Service for persisting agent trajectories and memories to Neo4j.
    Ensures long-term learning and auditability of agent reasoning.
    """
    def __init__(self, sync_service: Optional[RemoteSyncService] = None):
        self.sync_service = sync_service or RemoteSyncService()

    async def persist_run(
        self,
        agent_name: str,
        task: str,
        memory: AgentMemory,
        result: Any,
        trace_id: str = "no-trace",
        timing: Optional[Dict[str, float]] = None,
        token_usage: Optional[Dict[str, int]] = None,
    ) -> bool:
        """
        Formats and sends the full agent trajectory to the n8n ingestion webhook.
        """
        try:
            # 1. Extract succinct steps from smolagents memory
            steps_data = memory.get_succinct_steps()
            
            # 2. Prepare payload for Neo4j (Procedural/Autobiographical subgraph)
            payload = {
                "agent_name": agent_name,
                "task": task[:1000],
                "trace_id": trace_id,
                "steps": steps_data,
                "final_result": str(result)[:2000],
                "timing": timing or {},
                "token_usage": token_usage or {},
                "timestamp": datetime.utcnow().isoformat(),
                "operation": "persist_agent_run"
            }
            
            # 3. Send to n8n webhook
            # Note: _send_to_webhook handles signature generation
            response = await self.sync_service._send_to_webhook(
                payload, 
                webhook_url=self.sync_service.config.agent_run_webhook_url
            )
            
            if response.get("success", True):
                logger.info(f"Successfully persisted trajectory for agent {agent_name}")
                return True
            else:
                logger.error(f"Failed to persist trajectory: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error persisting agent run: {e}")
            return False

_agent_memory_service: Optional[AgentMemoryService] = None

def get_agent_memory_service() -> AgentMemoryService:
    global _agent_memory_service
    if _agent_memory_service is None:
        _agent_memory_service = AgentMemoryService()
    return _agent_memory_service
