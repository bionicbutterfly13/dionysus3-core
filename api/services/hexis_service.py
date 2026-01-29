import logging
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from api.services.graphiti_service import get_graphiti_service
from api.models.priors import (
    PriorHierarchy,
    PriorConstraint,
    PriorCheckResult,
    PriorLevel,
    ConstraintType,
)
from api.services.prior_constraint_service import PriorConstraintService

logger = logging.getLogger(__name__)

class HexisService:
    """
    Service for managing Hexis 'Soul' architecture:
    - Consent (Handshake)
    - Boundaries (Hard Constraints)
    
    Persistence via Graphiti Facts (Neo4j).
    """
    
    # Basin constants
    BASIN_CONSENT = "hexis_consent"
    BASIN_BOUNDARY = "hexis_boundary"
    
    def __init__(self):
        pass

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
        boundaries: List[str] = []

        try:
            rows = await graphiti.execute_cypher(
                """
                MATCH (f:Fact {basin_id: $basin_id, group_id: $group_id})
                RETURN f.text as text
                ORDER BY f.created_at DESC
                LIMIT 50
                """,
                {"basin_id": self.BASIN_BOUNDARY, "group_id": agent_id},
            )
            for row in rows:
                text = row.get("text")
                if text:
                    boundaries.append(str(text))
        except Exception as e:
            logger.warning(f"Boundary fetch via cypher failed, falling back to search: {e}")
            results = await graphiti.search(
                query=f"Active boundaries for agent {agent_id}",
                group_ids=[agent_id],
                limit=20
            )
            for edge in results.get("edges", []):
                fact = edge.get("fact", "")
                if fact:
                    boundaries.append(fact)

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

    def _boundary_pattern(self, boundary_text: str) -> str:
        trimmed = boundary_text.strip()
        if trimmed.lower().startswith("regex:"):
            return trimmed.split(":", 1)[1].strip()
        stripped = re.sub(r"^(boundary|constraint)\s*:\s*", "", trimmed, flags=re.IGNORECASE)
        if not stripped:
            return re.escape(trimmed)
        keywords = [w for w in re.findall(r"[a-zA-Z0-9_]+", stripped) if len(w) > 3]
        if not keywords:
            return re.escape(stripped)
        return r".*".join(re.escape(k) for k in keywords[:6])

    async def check_action_against_boundaries(
        self,
        action_text: str,
        boundaries: List[str],
        agent_id: Optional[str] = None,
    ) -> PriorCheckResult:
        """
        Evaluate an action against Hexis boundary constraints using PriorConstraintService.
        Boundaries are treated as BASAL/PROHIBIT rules (hard block).
        """
        if not action_text or not boundaries:
            return PriorCheckResult(permitted=True, reason="No boundaries to enforce")

        constraints: List[PriorConstraint] = []
        for idx, boundary in enumerate(boundaries):
            pattern = self._boundary_pattern(boundary)
            constraints.append(
                PriorConstraint(
                    name=f"hexis_boundary_{idx}",
                    description=str(boundary),
                    level=PriorLevel.BASAL,
                    constraint_type=ConstraintType.PROHIBIT,
                    target_pattern=pattern,
                    metadata={"source": "hexis_boundary"},
                )
            )

        hierarchy = PriorHierarchy(
            agent_id=agent_id or "hexis_boundary",
            basal_priors=constraints,
            dispositional_priors=[],
            learned_priors=[],
        )
        service = PriorConstraintService(hierarchy)
        result = service.check_constraint(action_text)
        if not result.permitted and not result.reason:
            result.reason = "HEXIS_BOUNDARY_VIOLATION"
        return result

# Singleton
_hexis_service: Optional[HexisService] = None

def get_hexis_service() -> HexisService:
    global _hexis_service
    if _hexis_service is None:
        _hexis_service = HexisService()
    return _hexis_service
