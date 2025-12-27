
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.webhook_neo4j_driver import get_neo4j_driver

async def change_password():
    print("🔐 Attempting to change Neo4j password via n8n webhook...")
    driver = get_neo4j_driver()
    
    # New safe password from env
    new_pw = os.getenv("NEO4J_PASSWORD")
    if not new_pw:
        print("❌ Error: NEO4J_PASSWORD environment variable not set.")
        return
    
    # Note: We don't need to specify the old password in ALTER USER
    cypher = f"ALTER USER neo4j SET PASSWORD '{new_pw}'"
    
    try:
        await driver.execute_query(cypher)
        print(f"✅ Neo4j password successfully changed to: {new_pw}")
        print("🚀 Now update your .env files and restart the containers.")
    except Exception as e:
        print(f"❌ Failed to change password: {e}")
        print("Note: If you get a 401, n8n might also be locked out or using the wrong credentials.")

if __name__ == "__main__":
    asyncio.run(change_password())
