
import asyncio
import sys
import uuid
from typing import Any, Optional

# Mocking parts of the system if needed, or just importing
try:
    from api.services.remote_sync import get_neo4j_driver
except ImportError:
    print("FATAL: Could not import get_neo4j_driver. Make sure PYTHONPATH is set.")
    sys.exit(1)

async def diag():
    driver = get_neo4j_driver()
    print("--- 1. CONSTRAINTS & INDEXES ---")
    for q in ["CALL db.constraints", "SHOW CONSTRAINTS", "CALL db.indexes"]:
        try:
            print(f"Executing: {q}")
            res = await driver.execute_query(q)
            print(f"Result: {res}")
        except Exception as e:
            print(f"Query {q} failed: {e}")

    print("\n--- 2. TEST CREATE (Optimistic Path) ---")
    did = str(uuid.uuid4())
    jid = str(uuid.uuid4())
    # Exact properties from SessionManager
    q_create = """
    CREATE (j:Journey:AutobiographicalJourney)
    SET j.device_id = $device_id,
        j.id = $id,
        j.participant_id = $participant_id,
        j.created_at = datetime(),
        j.updated_at = datetime(),
        j.metadata = '{}',
        j._is_new = true
    RETURN j {.*} as journey_data, 0 as session_count
    """
    params = {
        "device_id": did,
        "id": jid,
        "participant_id": "diag_user"
    }
    try:
        print(f"Creating node with device_id: {did}")
        res_c = await driver.execute_query(q_create, params)
        print(f"CREATE Result: {res_c}")
        
        print("\n--- 3. TEST MATCH (Verification) ---")
        q_match = "MATCH (j:Journey) WHERE j.device_id = $device_id RETURN j {.*} as data"
        res_m = await driver.execute_query(q_match, {"device_id": did})
        print(f"MATCH Result: {res_m}")
        
        if not res_m:
            print("ERROR: Node was NOT found immediately after CREATE.")
            # Try matching any Journey to see what labels/properties are actually being used
            res_all = await driver.execute_query("MATCH (j:Journey) RETURN j {.*} as data, labels(j) as labels LIMIT 1")
            print(f"PEEK at existing Journey: {res_all}")
        else:
            print("SUCCESS: Persistence verified.")

    except Exception as e:
        print(f"Surgical Diag Failed: {e}")

if __name__ == "__main__":
    asyncio.run(diag())
