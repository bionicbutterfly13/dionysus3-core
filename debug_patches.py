import unittest.mock
import sys

print("DEBUG: Isolating patch hang")

mock_driver = unittest.mock.MagicMock()

print("1. Patching api.services.remote_sync.get_neo4j_driver")
try:
    p1 = unittest.mock.patch("api.services.remote_sync.get_neo4j_driver", return_value=mock_driver)
    p1.start()
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("2. Patching api.services.webhook_neo4j_driver.get_neo4j_driver")
try:
    p2 = unittest.mock.patch("api.services.webhook_neo4j_driver.get_neo4j_driver", return_value=mock_driver)
    p2.start()
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("3. Patching api.services.graphiti_service.get_graphiti_service")
try:
    p3 = unittest.mock.patch("api.services.graphiti_service.get_graphiti_service", unittest.mock.AsyncMock())
    p3.start()
    print("✓ Success")
except Exception as e:
    print(f"✗ Failed: {e}")

print("All patches completed.")
