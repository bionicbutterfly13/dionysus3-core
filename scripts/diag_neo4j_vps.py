
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
            res2 = await driver.execute_query("MATCH (j:Journey) RETURN j.device_id as d, j.id as id LIMIT 5")
            for r in res2:
                print(r)
        except Exception as e:
            print(f"Error matching journeys: {e}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(diag())
