
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
                print(f"Labels: {await driver.execute_query('MATCH (n) WHERE id(n) = $id RETURN labels(n) as l', {'id': node.id})}")
                print(f"Properties: {node.keys()}")
                print(f"Values: {node}")
        except Exception as e:
            print(f"Error matching journeys: {e}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(diag())
