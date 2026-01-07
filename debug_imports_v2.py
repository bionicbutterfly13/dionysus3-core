import sys
import os

print("DEBUG: Starting import trace")

print("DEBUG: Patching get_neo4j_driver early")
import unittest.mock
mock_driver = unittest.mock.MagicMock()
mock_driver.execute_query = unittest.mock.AsyncMock(return_value=[])

# Patch before any imports
with unittest.mock.patch("api.services.remote_sync.get_neo4j_driver", return_value=mock_driver), \
     unittest.mock.patch("api.services.webhook_neo4j_driver.get_neo4j_driver", return_value=mock_driver), \
     unittest.mock.patch("api.services.graphiti_service.get_graphiti_service", unittest.mock.AsyncMock()):

    print("DEBUG: Importing api.models.autobiographical")
    from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
    print("DEBUG: Done importing api.models.autobiographical")

    print("DEBUG: Importing api.agents.consciousness_memory_core")
    # This might trigger imports of nemori_river_flow and consolidated_memory_stores
    from api.agents.consciousness_memory_core import ConsciousnessMemoryCore
    print("DEBUG: Done importing api.agents.consciousness_memory_core")

    print("DEBUG: Instantiating ConsciousnessMemoryCore")
    core = ConsciousnessMemoryCore(journey_id="test_journey")
    print("DEBUG: Done instantiating")

print("DEBUG: Success")
