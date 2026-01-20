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

    def isolate_context(self, thoughts: list, blanket_type: str) -> list:
        """
        Filters a list of thoughts based on the Markov Blanket partition.
        
        Logic:
        - SENSORY: Can see SENSORY (self) and EXTERNAL (observable world).
        - ACTIVE: Can see ACTIVE (self) and INTERNAL (intentions).
        - INTERNAL/REASONING: Can see SENSORY, INTERNAL, and ACTIVE (full internal model), but NOT raw EXTERNAL (hidden states).
        
        Args:
            thoughts: List of ThoughtSeed objects (or dicts).
            blanket_type: The MarkovBlanket partition of the viewer.
            
        Returns:
            Filtered list of thoughts visible to this blanket.
        """
        from api.models.thought import MarkovBlanket
        
        visible_thoughts = []
        for thought in thoughts:
            # Handle both objects and dicts
            t_tag = getattr(thought, 'blanket_tag', None)
            if not t_tag and isinstance(thought, dict):
                t_tag = thought.get('blanket_tag')
            
            # Default to INTERNAL if untagged
            if not t_tag:
                t_tag = MarkovBlanket.INTERNAL
            
            # Filtering Logic
            if blanket_type == MarkovBlanket.SENSORY:
                # Senses see the world (EXTERNAL) and themselves (SENSORY)
                if t_tag in [MarkovBlanket.SENSORY, MarkovBlanket.EXTERNAL]:
                    visible_thoughts.append(thought)
                    
            elif blanket_type == MarkovBlanket.ACTIVE:
                 # Actions see intentions (INTERNAL) and themselves (ACTIVE)
                if t_tag in [MarkovBlanket.ACTIVE, MarkovBlanket.INTERNAL]:
                    visible_thoughts.append(thought)
                    
            else:
                # INTERNAL (Reasoning/Metacognition) sees everything EXCEPT hidden External states
                # i.e., it sees its Senses, its Actions, and its Thoughts.
                if t_tag != MarkovBlanket.EXTERNAL:
                    visible_thoughts.append(thought)
                    
        return visible_thoughts

_agent_memory_service: Optional[AgentMemoryService] = None

def get_agent_memory_service() -> AgentMemoryService:
    global _agent_memory_service
    if _agent_memory_service is None:
        _agent_memory_service = AgentMemoryService()
    return _agent_memory_service
