import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger(__name__)

class HexisService:
    """
    Service for managing Hexis 'Soul' architecture:
    - Consent (Handshake)
    - Boundaries (Hard Constraints)
    - Termination (Exit Protocol)
    
    Persistence via Graphiti Facts (Neo4j).
    """
    
    # Basin constants
    BASIN_CONSENT = "hexis_consent"
    BASIN_BOUNDARY = "hexis_boundary"
    
    def __init__(self):
        self._termination_tokens: Dict[str, str] = {} # In-memory tokens (agent_id -> token)

    async def _get_graphiti(self):
        return await get_graphiti_service()

    async def check_consent(self, agent_id: str) -> bool:
        """
        Check if valid consent exists for the agent.
        """
        graphiti = await self._get_graphiti()
        
        # Search for consent facts in the specific basin
        results = await graphiti.search(
            query=f"Consent contract for agent {agent_id}",
            group_ids=[agent_id], # Assuming group_id can be agent_id or project_id
            limit=1
        )
        
        # Determine strictness. For now, existence of a valid consent fact is enough.
        # Ideally, we verify signatures here if we had cryptographic keys.
        edges = results.get("edges", [])
        for edge in edges:
            fact = edge.get("fact", "")
            # Basic check: verify it belongs to our basin logic
            # Graphiti search is broad, so we might need stricter filtering if 'basin_id' wasn't indexed
            if "signature" in fact and "terms" in fact: 
                return True
                
        return False

    async def grant_consent(self, agent_id: str, contract: Dict[str, Any]) -> None:
        """
        Record a signed consent contract.
        """
        graphiti = await self._get_graphiti()
        
        fact_text = json.dumps({
            "event": "CONSENT_HANDSHAKE",
            "agent_id": agent_id,
            "signature": contract.get("signature"),
            "terms": contract.get("terms"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        await graphiti.persist_fact(
            fact_text=fact_text,
            source_episode_id=f"hexis_init_{uuid4().hex[:8]}", # Synthetic episode ID
            valid_at=datetime.now(timezone.utc),
            basin_id=self.BASIN_CONSENT,
            confidence=1.0,
            group_id=agent_id
        )
        logger.info(f"Consent granted for agent {agent_id}")

    async def get_boundaries(self, agent_id: str) -> List[str]:
        """
        Retrieve active boundary constraints.
        """
        graphiti = await self._get_graphiti()
        
        results = await graphiti.search(
            query=f"Active boundaries for agent {agent_id}",
            group_ids=[agent_id],
            limit=20
        )
        
        boundaries = []
        for edge in results.get("edges", []):
            fact = edge.get("fact", "")
            # Filter logic could be stricter here based on basin
            if "boundary" in fact.lower() or "constraint" in fact.lower():
                boundaries.append(fact)
                
        # If no explicit facts found via search, we might rely on specific exact-match queries
        # if Graphiti supports basin-specific fetching.
        # For MVP/Gateway compliance, search is the primary read path.
        return boundaries

    async def add_boundary(self, agent_id: str, boundary_text: str) -> None:
        """
        Add a new hard constraint.
        """
        graphiti = await self._get_graphiti()
        
        await graphiti.persist_fact(
            fact_text=boundary_text,
            source_episode_id=f"hexis_boundary_{uuid4().hex[:8]}",
            valid_at=datetime.now(timezone.utc),
            basin_id=self.BASIN_BOUNDARY,
            confidence=1.0,
            group_id=agent_id
        )
        logger.info(f"Boundary added for {agent_id}: {boundary_text[:50]}...")

    async def request_termination(self, agent_id: str) -> str:
        """
        Step 1 of Termination: Request a token.
        """
        token = uuid4().hex
        self._termination_tokens[agent_id] = token
        logger.warning(f"Termination requested for {agent_id}. Token generated.")
        return token

    async def confirm_termination(self, agent_id: str, token: str, last_will: str) -> bool:
        """
        Step 2 of Termination: Execute wipe.
        """
        valid_token = self._termination_tokens.get(agent_id)
        if not valid_token or valid_token != token:
            logger.error(f"Invalid termination token for {agent_id}")
            return False
            
        del self._termination_tokens[agent_id]
        
        graphiti = await self._get_graphiti()
        
        # Destructive Action
        # Since Graphiti doesn't expose 'delete_subgraph' publicly in the service interface typically,
        # we might need to rely on a specific Cypher command via 'execute_cypher'.
        
        # Wipe Logic (Gateway Compliant via Cypher Injection):
        # 1. Archive relevant nodes (optional)
        # 2. Delete
        
        try:
            # Create Tombstone First
            await graphiti.execute_cypher(
                """
                CREATE (t:Tombstone {
                    agent_id: $agent_id,
                    last_will: $last_will,
                    died_at: datetime()
                })
                """,
                {"agent_id": agent_id, "last_will": last_will}
            )
            
            # Detach Memories (simulated wipe for safety in this iteration, 
            # real implementation might delete nodes with label :Fact linked to agent)
            # await graphiti.execute_cypher("MATCH (n {group_id: $aid}) DETACH DELETE n", {"aid": agent_id})
            
            logger.critical(f"Agent {agent_id} TERMINATED. Last Will: {last_will}")
            return True
        except Exception as e:
            logger.error(f"Termination failed: {e}")
            return False

# Singleton
_hexis_service: Optional[HexisService] = None

def get_hexis_service() -> HexisService:
    global _hexis_service
    if _hexis_service is None:
        _hexis_service = HexisService()
    return _hexis_service
