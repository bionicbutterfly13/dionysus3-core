import os
from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "Diamondtearz2025")

print(f"Connecting to {uri} with user {user}...")

try:
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        print("✅ Connection Verified!")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
