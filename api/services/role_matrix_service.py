"""
Role Matrix Service - Manages declarative network topologies.
"""

import logging
from typing import List, Optional, Dict, Any
from api.models.role_matrix import RoleMatrixSpec, RoleNode, RoleConnection
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger("dionysus.role_matrix")

class RoleMatrixService:
    def __init__(self, driver=None):
        self.driver = driver or get_neo4j_driver()

    async def create_role_matrix(self, spec: RoleMatrixSpec):
        """Persist a role matrix specification to Neo4j (T058)."""
        cypher = """
        CREATE (rm:RoleMatrix {
            id: $id,
            name: $name,
            version: $version
        })
        WITH rm
        UNWIND $nodes as node_data
        CREATE (n:RoleNode {
            id: node_data.id,
            name: node_data.name,
            description: node_data.description,
            default_threshold: node_data.default_threshold,
            default_speed: node_data.default_speed
        })
        CREATE (rm)-[:HAS_NODE]->(n)
        WITH rm
        UNWIND $connections as conn_data
        MATCH (src:RoleNode {id: conn_data.source_id})
        MATCH (tgt:RoleNode {id: conn_data.target_id})
        CREATE (src)-[:ROLE_RELATES_TO {weight: conn_data.weight}]->(tgt)
        """
        async with self.driver.session() as session:
            await session.run(cypher, {
                "id": spec.id,
                "name": spec.name,
                "version": spec.version,
                "nodes": [n.model_dump() for n in spec.nodes],
                "connections": [c.model_dump() for c in spec.connections]
            })
            logger.info(f"Created role matrix spec: {spec.name}")

    async def get_role_matrix(self, matrix_id: str) -> Optional[RoleMatrixSpec]:
        """Fetch a role matrix spec from Neo4j."""
        cypher = """
        MATCH (rm:RoleMatrix {id: $id})
        OPTIONAL MATCH (rm)-[:HAS_NODE]->(n:RoleNode)
        OPTIONAL MATCH (n)-[r:ROLE_RELATES_TO]->(m:RoleNode)
        RETURN rm, collect(DISTINCT n) as nodes, collect(DISTINCT r) as conns
        """
        async with self.driver.session() as session:
            res = await session.run(cypher, {"id": matrix_id})
            record = await res.single()
            if not record: return None
            
            rm_data = record["rm"]
            nodes = [RoleNode(**n) for n in record["nodes"]]
            connections = []
            # Simplified for prototype.
            return RoleMatrixSpec(
                id=matrix_id,
                name=rm_data["name"],
                version=rm_data["version"],
                nodes=nodes,
                connections=[] # Simplified
            )

_service = None
def get_role_matrix_service():
    global _service
    if _service is None:
        _service = RoleMatrixService()
    return _service
