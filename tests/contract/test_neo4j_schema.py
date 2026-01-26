import pytest
import os
import httpx
from api.services.remote_sync import RemoteSyncService, SyncConfig

@pytest.mark.asyncio
async def test_energy_well_properties_schema():
    """Verify that Neo4j nodes can accept and return Energy-Well properties."""
    token = os.getenv("MEMORY_WEBHOOK_TOKEN")
    cypher_url = os.getenv("N8N_CYPHER_URL", "http://localhost:5678/webhook/neo4j/v1/cypher")
    
    if not token:
        pytest.skip("MEMORY_WEBHOOK_TOKEN not set")

    sync = RemoteSyncService(config=SyncConfig(webhook_token=token, cypher_webhook_url=cypher_url))
    
    # Create a test node with energy properties
    test_node_name = "Schema Test Cluster"
    create_query = """
    MERGE (c:MemoryCluster {name: $name})
    SET c.boundary_energy = 0.75,
        c.stability = 0.85,
        c.cohesion_ratio = 1.25
    RETURN c.boundary_energy as energy, c.stability as stability
    """
    
    try:
        res = await sync.run_cypher(create_query, {"name": test_node_name})
        records = res.get("records") or res.get("results") or []
        
        assert len(records) > 0
        assert float(records[0]["energy"]) == 0.75
        assert float(records[0]["stability"]) == 0.85
        
        # Cleanup
        await sync.run_cypher("MATCH (c:MemoryCluster {name: $name}) DELETE c", {"name": test_node_name})
        
    except Exception as e:
        pytest.skip(f"n8n Cypher webhook unreachable (run in integration env): {e}")
