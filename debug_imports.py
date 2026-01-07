import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("import_check")

print("1. Importing models.autobiographical")
try:
    from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("2. Importing services.llm_service")
try:
    from api.services.llm_service import chat_completion
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("3. Importing services.graphiti_service")
try:
    from api.services.graphiti_service import GraphitiService
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("4. Importing services.webhook_neo4j_driver")
try:
    from api.services.webhook_neo4j_driver import WebhookNeo4jDriver
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("5. Importing agents.consolidated_memory_stores")
try:
    from api.agents.consolidated_memory_stores import ConsolidatedMemoryStore
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("6. Importing services.nemori_river_flow")
try:
    from api.services.nemori_river_flow import NemoriRiverFlow
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("7. Importing agents.consciousness_memory_core")
try:
    from api.agents.consciousness_memory_core import ConsciousnessMemoryCore
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("All imports completed.")
