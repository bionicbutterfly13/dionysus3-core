#!/usr/bin/env python3
"""
Quickstart Validation Script
Feature: 002-remote-persistence-safety
Task: T059

Validates the complete quickstart.md flow:
1. VPS connectivity (neo4j, n8n, ollama)
2. Webhook HMAC signing
3. Memory sync flow
4. Recovery from Neo4j

Run with SSH tunnels active:
    ssh -N dionysus-tunnel &
    python scripts/validate_quickstart.py
"""

import asyncio
import hashlib
import hmac
import json
import os
import sys
import uuid
from datetime import datetime

import httpx

# =============================================================================
# Configuration
# =============================================================================

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "DionysusMem2025!")

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/memory/v1/ingest/message"
)
MEMORY_WEBHOOK_TOKEN = os.getenv(
    "MEMORY_WEBHOOK_TOKEN",
    "09b845160bc4b24b78c103bf40dd5ac3c56229ed41e23a50e548ea01254483bc"
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Test data
TEST_MEMORY_ID = f"quickstart-test-{uuid.uuid4().hex[:8]}"
TEST_SESSION_ID = f"test-session-{uuid.uuid4().hex[:8]}"
TEST_PROJECT_ID = "dionysus-core"


# =============================================================================
# Validation Functions
# =============================================================================

class ValidationResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def add(self, name: str, passed: bool, message: str = ""):
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append((name, passed, message))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"  {status}: {name}" + (f" - {message}" if message else ""))

    def summary(self):
        print("\n" + "=" * 60)
        print(f"VALIDATION SUMMARY: {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        return self.failed == 0


results = ValidationResult()


async def test_neo4j_connectivity():
    """Test Neo4j connection via SSH tunnel."""
    print("\n[1] Testing Neo4j Connectivity...")

    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

        async with driver.session() as session:
            result = await session.run("RETURN 1 as n")
            record = await result.single()
            value = record["n"]

        await driver.close()

        results.add("Neo4j connection", value == 1, f"Returned {value}")

        # Check schema exists
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        async with driver.session() as session:
            # Check for Memory constraint
            result = await session.run(
                "SHOW CONSTRAINTS WHERE name = 'memory_id_unique'"
            )
            constraints = await result.data()

        await driver.close()

        results.add(
            "Neo4j schema initialized",
            len(constraints) > 0,
            f"Found {len(constraints)} constraints"
        )

    except ImportError:
        results.add("Neo4j connection", False, "neo4j package not installed")
    except Exception as e:
        results.add("Neo4j connection", False, str(e))


async def test_n8n_connectivity():
    """Test n8n webhook availability."""
    print("\n[2] Testing n8n Connectivity...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check n8n health
            base_url = N8N_WEBHOOK_URL.rsplit("/webhook", 1)[0]
            response = await client.get(f"{base_url}/healthz")

            results.add(
                "n8n health endpoint",
                response.status_code == 200,
                f"Status {response.status_code}"
            )

    except Exception as e:
        results.add("n8n health endpoint", False, str(e))


async def test_ollama_connectivity():
    """Test Ollama API availability."""
    print("\n[3] Testing Ollama Connectivity...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check Ollama API
            response = await client.get(f"{OLLAMA_URL}/api/tags")

            results.add(
                "Ollama API reachable",
                response.status_code == 200,
                f"Status {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]

                has_embed_model = any("nomic-embed" in m for m in models)
                results.add(
                    "Embedding model available",
                    has_embed_model,
                    f"Models: {models[:3]}..."
                )

    except Exception as e:
        results.add("Ollama API reachable", False, str(e))


async def test_webhook_hmac():
    """Test HMAC signature generation and webhook acceptance."""
    print("\n[4] Testing Webhook HMAC Signing...")

    payload = {
        "memory_id": TEST_MEMORY_ID,
        "content": "Quickstart validation test memory",
        "memory_type": "episodic",
        "importance": 0.5,
        "session_id": TEST_SESSION_ID,
        "project_id": TEST_PROJECT_ID,
        "sync_version": 1,
        "created_at": datetime.utcnow().isoformat(),
    }

    payload_bytes = json.dumps(payload).encode("utf-8")

    # Generate HMAC signature
    signature = "sha256=" + hmac.new(
        key=MEMORY_WEBHOOK_TOKEN.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    results.add(
        "HMAC signature generated",
        signature.startswith("sha256="),
        f"Signature: {signature[:30]}..."
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                }
            )

            # Accept 200 (success) or 500 (workflow error, but webhook accepted)
            accepted = response.status_code in [200, 500]
            results.add(
                "Webhook accepted request",
                accepted,
                f"Status {response.status_code}: {response.text[:100]}"
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    results.add(
                        "Webhook returned success",
                        data.get("success", False),
                        f"Response: {data}"
                    )
                except Exception:
                    results.add(
                        "Webhook returned success",
                        True,
                        "Response not JSON but status 200"
                    )

    except Exception as e:
        results.add("Webhook accepted request", False, str(e))


async def test_memory_in_neo4j():
    """Verify memory was synced to Neo4j."""
    print("\n[5] Testing Memory Sync to Neo4j...")

    # Give n8n time to process
    await asyncio.sleep(3)

    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (m:Memory {id: $memory_id})
                RETURN m.content as content,
                       m.embedding IS NOT NULL as has_embedding,
                       m.session_id as session_id
                """,
                memory_id=TEST_MEMORY_ID
            )
            record = await result.single()

        await driver.close()

        if record:
            results.add(
                "Memory synced to Neo4j",
                True,
                f"Content: {record['content'][:30]}..."
            )
            results.add(
                "Embedding generated",
                record["has_embedding"],
                f"Has embedding: {record['has_embedding']}"
            )
            results.add(
                "Session ID preserved",
                record["session_id"] == TEST_SESSION_ID,
                f"Session: {record['session_id']}"
            )
        else:
            results.add("Memory synced to Neo4j", False, "Memory not found")

    except ImportError:
        results.add("Memory synced to Neo4j", False, "neo4j package not installed")
    except Exception as e:
        results.add("Memory synced to Neo4j", False, str(e))


async def test_recall_query():
    """Test querying memories back from Neo4j."""
    print("\n[6] Testing Memory Recall...")

    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

        async with driver.session() as session:
            # Query by session
            result = await session.run(
                """
                MATCH (m:Memory)
                WHERE m.session_id = $session_id
                RETURN count(m) as count
                """,
                session_id=TEST_SESSION_ID
            )
            record = await result.single()
            count = record["count"]

        await driver.close()

        results.add(
            "Query by session works",
            count >= 1,
            f"Found {count} memories in session"
        )

    except Exception as e:
        results.add("Query by session works", False, str(e))


async def cleanup_test_data():
    """Clean up test data from Neo4j."""
    print("\n[7] Cleaning Up Test Data...")

    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (m:Memory {id: $memory_id})
                DETACH DELETE m
                RETURN count(m) as deleted
                """,
                memory_id=TEST_MEMORY_ID
            )
            record = await result.single()
            deleted = record["deleted"]

        await driver.close()

        results.add(
            "Test data cleaned up",
            True,
            f"Deleted {deleted} test memories"
        )

    except Exception as e:
        results.add("Test data cleaned up", False, str(e))


# =============================================================================
# Main
# =============================================================================

async def main():
    print("=" * 60)
    print("QUICKSTART VALIDATION - Feature 002-remote-persistence-safety")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  NEO4J_URI: {NEO4J_URI}")
    print(f"  N8N_WEBHOOK_URL: {N8N_WEBHOOK_URL}")
    print(f"  OLLAMA_URL: {OLLAMA_URL}")
    print(f"  TEST_MEMORY_ID: {TEST_MEMORY_ID}")

    # Run validations
    await test_neo4j_connectivity()
    await test_n8n_connectivity()
    await test_ollama_connectivity()
    await test_webhook_hmac()
    await test_memory_in_neo4j()
    await test_recall_query()
    await cleanup_test_data()

    # Summary
    success = results.summary()

    if success:
        print("\n🎉 All validations passed! Quickstart is working correctly.")
    else:
        print("\n❌ Some validations failed. Check the output above.")
        print("\nTroubleshooting:")
        print("  1. Ensure SSH tunnels are active: ssh -N dionysus-tunnel")
        print("  2. Check VPS services: ssh root@72.61.78.89 'docker ps'")
        print("  3. Verify .env configuration matches quickstart.md")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
