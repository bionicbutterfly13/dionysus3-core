
import asyncio
from api.services.remote_sync import get_neo4j_driver

async def diag():
    try:
        driver = get_neo4j_driver()
        print("--- CONSTRAINTS ---")
        try:
            res = await driver.execute_query("SHOW CONSTRAINTS")
            for r in res:
                print(r)
        except Exception as e:
            print(f"Error showing constraints: {e}")
            
        print("\n--- JOURNEY SAMPLES ---")
        try:
            res2 = await driver.execute_query("MATCH (j:Journey) RETURN j as node LIMIT 5")
            for r in res2:
                node = r["node"]
                print(f"Node Type: {type(node)}")
                print(f"Properties: {list(node.keys())}")
                print(f"Values: {node}")
                # Check for specific fields
                print(f"device_id: {node.get('device_id')} ({type(node.get('device_id'))})")
        except Exception as e:
            print(f"Error matching journeys: {e}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(diag())
