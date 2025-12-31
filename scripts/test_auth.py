#!/usr/bin/env python3
# DEV-ONLY UTILITY - NOT USED IN PRODUCTION
# Direct Neo4j connection for local testing only
# Production code uses webhook_neo4j_driver.py exclusively

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(override=True)
uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD")

print(f"Connecting to {uri} with user {user}")
if password:
    print(f"Password length: {len(password)}")
    print(f"Password starts with: {password[:2]}")
    print(f"Password ends with: {password[-2:]}")
else:
    print("Password not found in env")

try:
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        print("Success!")
except Exception as e:
    print(f"Failed: {e}")
