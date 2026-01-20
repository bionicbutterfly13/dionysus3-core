"""
Prior Persistence Service

Handles persistence of prior hierarchies to Graphiti/Neo4j.
Provides methods to seed default priors and hydrate from storage.

Track 038 Phase 2 - Evolutionary Priors
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from api.models.priors import (
    PriorHierarchy,
    PriorConstraint,
    PriorLevel,
    ConstraintType,
    get_default_basal_priors,
    get_default_dispositional_priors,
)

logger = logging.getLogger(__name__)


class PriorPersistenceService:
    """
    Service for persisting and hydrating prior hierarchies.

    Uses Graphiti's execute_cypher for Neo4j operations, following
    the pattern established in biological_agency_service.py.

    Schema:
        (:Agent {id: ...})-[:HAS_PRIORS]->(:PriorHierarchy {agent_id: ...})
        (:PriorHierarchy)-[:HAS_CONSTRAINT {level: ...}]->(:PriorConstraint {...})
    """

    def __init__(self):
        """Initialize the prior persistence service."""
        self._graphiti = None

    async def _get_graph_service(self):
        """Lazy async initialization of Graphiti Service."""
        if self._graphiti is None:
            from api.services.graphiti_service import GraphitiService
            self._graphiti = await GraphitiService.get_instance()
        return self._graphiti

    async def seed_basal_priors(self, agent_id: str) -> PriorHierarchy:
        """
        Seed default BASAL priors for an agent.

        Creates the prior hierarchy with default survival/integrity constraints.
        These are evolutionary constraints that should NEVER be violated.

        Args:
            agent_id: The agent ID to seed priors for

        Returns:
            PriorHierarchy with seeded BASAL priors
        """
        hierarchy = PriorHierarchy(
            agent_id=agent_id,
            basal_priors=get_default_basal_priors(),
            dispositional_priors=[],
            learned_priors=[],
        )

        await self.persist_hierarchy(hierarchy)
        logger.info(f"Seeded {len(hierarchy.basal_priors)} BASAL priors for agent {agent_id}")

        return hierarchy

    async def seed_dispositional_priors(
        self,
        agent_id: str,
        priors: Optional[List[PriorConstraint]] = None
    ) -> PriorHierarchy:
        """
        Seed DISPOSITIONAL priors for an agent.

        If no priors are provided, uses defaults.

        Args:
            agent_id: The agent ID
            priors: Optional list of dispositional priors

        Returns:
            Updated PriorHierarchy
        """
        # Try to load existing hierarchy
        hierarchy = await self.hydrate_hierarchy(agent_id)

        if hierarchy is None:
            # Create new with default basal
            hierarchy = await self.seed_basal_priors(agent_id)

        # Add dispositional priors
        dispositional = priors or get_default_dispositional_priors()
        hierarchy.dispositional_priors = dispositional
        hierarchy.updated_at = datetime.utcnow()

        await self.persist_hierarchy(hierarchy)
        logger.info(
            f"Seeded {len(dispositional)} DISPOSITIONAL priors for agent {agent_id}"
        )

        return hierarchy

    async def seed_full_hierarchy(self, agent_id: str) -> PriorHierarchy:
        """
        Seed a complete hierarchy with all default priors.

        Args:
            agent_id: The agent ID

        Returns:
            Complete PriorHierarchy with all defaults
        """
        hierarchy = PriorHierarchy(
            agent_id=agent_id,
            basal_priors=get_default_basal_priors(),
            dispositional_priors=get_default_dispositional_priors(),
            learned_priors=[],
        )

        await self.persist_hierarchy(hierarchy)
        logger.info(
            f"Seeded full hierarchy for agent {agent_id}: "
            f"{len(hierarchy.basal_priors)} BASAL, "
            f"{len(hierarchy.dispositional_priors)} DISPOSITIONAL"
        )

        return hierarchy

    async def persist_hierarchy(self, hierarchy: PriorHierarchy) -> None:
        """
        Persist a prior hierarchy to Neo4j via Graphiti.

        Creates/updates nodes:
        - (:Agent {id: ...})-[:HAS_PRIORS]->(:PriorHierarchy)
        - (:PriorHierarchy)-[:HAS_CONSTRAINT]->(:PriorConstraint)

        Args:
            hierarchy: The hierarchy to persist
        """
        graph = await self._get_graph_service()

        # Serialize hierarchy for storage
        hierarchy_props = {
            "agent_id": hierarchy.agent_id,
            "base_precision": hierarchy.base_precision,
            "created_at": hierarchy.created_at.isoformat(),
            "updated_at": hierarchy.updated_at.isoformat(),
            "basal_count": len(hierarchy.basal_priors),
            "dispositional_count": len(hierarchy.dispositional_priors),
            "learned_count": len(hierarchy.learned_priors),
        }

        # Create/update hierarchy node
        hierarchy_query = """
        MERGE (a:Agent {id: $agent_id})
        MERGE (a)-[:HAS_PRIORS]->(h:PriorHierarchy {agent_id: $agent_id})
        SET h += $props
        RETURN h
        """

        try:
            await graph.execute_cypher(
                hierarchy_query,
                {"agent_id": hierarchy.agent_id, "props": hierarchy_props}
            )

            # Persist individual constraints
            all_constraints = (
                [(c, "basal") for c in hierarchy.basal_priors] +
                [(c, "dispositional") for c in hierarchy.dispositional_priors] +
                [(c, "learned") for c in hierarchy.learned_priors]
            )

            for constraint, level in all_constraints:
                await self._persist_constraint(hierarchy.agent_id, constraint, level)

            logger.info(f"Persisted hierarchy for agent {hierarchy.agent_id}")

        except Exception as e:
            logger.error(f"Failed to persist hierarchy for {hierarchy.agent_id}: {e}")
            raise

    async def _persist_constraint(
        self,
        agent_id: str,
        constraint: PriorConstraint,
        level: str
    ) -> None:
        """Persist a single constraint."""
        graph = await self._get_graph_service()

        props = {
            "id": constraint.id,
            "name": constraint.name,
            "description": constraint.description,
            "level": constraint.level.value,
            "precision": constraint.precision,
            "constraint_type": constraint.constraint_type.value,
            "target_pattern": constraint.target_pattern,
            "active": constraint.active,
            "created_at": constraint.created_at.isoformat(),
            "metadata_json": json.dumps(constraint.metadata),
        }

        query = """
        MATCH (h:PriorHierarchy {agent_id: $agent_id})
        MERGE (c:PriorConstraint {id: $constraint_id})
        SET c += $props
        MERGE (h)-[r:HAS_CONSTRAINT]->(c)
        SET r.level = $level
        """

        await graph.execute_cypher(
            query,
            {
                "agent_id": agent_id,
                "constraint_id": constraint.id,
                "level": level,
                "props": props
            }
        )

    async def hydrate_hierarchy(self, agent_id: str) -> Optional[PriorHierarchy]:
        """
        Hydrate a prior hierarchy from Neo4j.

        Args:
            agent_id: The agent ID to hydrate for

        Returns:
            PriorHierarchy if found, None otherwise
        """
        graph = await self._get_graph_service()

        # Query hierarchy and constraints
        query = """
        MATCH (a:Agent {id: $agent_id})-[:HAS_PRIORS]->(h:PriorHierarchy)
        OPTIONAL MATCH (h)-[r:HAS_CONSTRAINT]->(c:PriorConstraint)
        RETURN h, collect({constraint: c, level: r.level}) as constraints
        """

        try:
            results = await graph.execute_cypher(query, {"agent_id": agent_id})

            if not results:
                logger.info(f"No hierarchy found for agent {agent_id}")
                return None

            row = results[0]
            h_data = row.get("h", {})
            constraints_data = row.get("constraints", [])

            # Reconstruct constraints by level
            basal_priors = []
            dispositional_priors = []
            learned_priors = []

            for item in constraints_data:
                c_data = item.get("constraint")
                level = item.get("level")

                if not c_data or not c_data.get("id"):
                    continue

                constraint = PriorConstraint(
                    id=c_data["id"],
                    name=c_data.get("name", "Unknown"),
                    description=c_data.get("description", ""),
                    level=PriorLevel(c_data.get("level", "learned")),
                    precision=float(c_data.get("precision", 1.0)),
                    constraint_type=ConstraintType(
                        c_data.get("constraint_type", "prohibit")
                    ),
                    target_pattern=c_data.get("target_pattern", ".*"),
                    active=c_data.get("active", True),
                    metadata=json.loads(c_data.get("metadata_json", "{}"))
                )

                if level == "basal":
                    basal_priors.append(constraint)
                elif level == "dispositional":
                    dispositional_priors.append(constraint)
                else:
                    learned_priors.append(constraint)

            hierarchy = PriorHierarchy(
                agent_id=agent_id,
                basal_priors=basal_priors,
                dispositional_priors=dispositional_priors,
                learned_priors=learned_priors,
                base_precision=float(h_data.get("base_precision", 1.0)),
            )

            logger.info(
                f"Hydrated hierarchy for {agent_id}: "
                f"{len(basal_priors)} BASAL, "
                f"{len(dispositional_priors)} DISPOSITIONAL, "
                f"{len(learned_priors)} LEARNED"
            )

            return hierarchy

        except Exception as e:
            logger.error(f"Failed to hydrate hierarchy for {agent_id}: {e}")
            return None

    async def add_learned_prior(
        self,
        agent_id: str,
        constraint: PriorConstraint
    ) -> bool:
        """
        Add a learned prior to an agent's hierarchy.

        Learned priors can be added dynamically based on experience.

        Args:
            agent_id: The agent ID
            constraint: The constraint to add

        Returns:
            True if successful
        """
        hierarchy = await self.hydrate_hierarchy(agent_id)

        if hierarchy is None:
            hierarchy = await self.seed_full_hierarchy(agent_id)

        # Ensure constraint is LEARNED level
        constraint.level = PriorLevel.LEARNED
        hierarchy.learned_priors.append(constraint)
        hierarchy.updated_at = datetime.utcnow()

        await self.persist_hierarchy(hierarchy)
        return True


# Singleton instance
_service_instance: Optional[PriorPersistenceService] = None


def get_prior_persistence_service() -> PriorPersistenceService:
    """Get the singleton PriorPersistenceService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = PriorPersistenceService()
    return _service_instance
