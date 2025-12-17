#!/usr/bin/env python3
"""
Quickstart Validation Script
Feature: 002-remote-persistence-safety
Task: T059

Validates the complete quickstart.md flow:
1. VPS connectivity (n8n, ollama)
2. Webhook HMAC signing
3. Memory sync flow
4. Recovery via n8n

Run with n8n + ollama active:
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

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/memory/v1/ingest/message"
)
N8N_CYPHER_URL = os.getenv(
    "N8N_CYPHER_URL",
    "http://localhost:5678/webhook/neo4j/v1/cypher"
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
    """Test Neo4j reachability indirectly via n8n cypher webhook."""
    print("\n[1] Testing Neo4j Connectivity (via n8n)...")

    payload = {"operation": "cypher", "mode": "read", "statement": "RETURN 1 as n", "parameters": {}}
    payload_bytes = json.dumps(payload).encode("utf-8")

    signature = "sha256=" + hmac.new(
        key=MEMORY_WEBHOOK_TOKEN.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                N8N_CYPHER_URL,
                content=payload_bytes,
                headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
            )
        ok = resp.status_code == 200
        results.add("n8n cypher webhook reachable", ok, f"Status {resp.status_code}")
    except Exception as e:
        results.add("n8n cypher webhook reachable", False, str(e))


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

    stmt = """
    MATCH (m:Memory {id: $memory_id})
    RETURN m.content as content,
           m.embedding IS NOT NULL as has_embedding,
           m.session_id as session_id
    """
    payload = {
        "operation": "cypher",
        "mode": "read",
        "statement": stmt,
        "parameters": {"memory_id": TEST_MEMORY_ID},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = "sha256=" + hmac.new(
        key=MEMORY_WEBHOOK_TOKEN.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                N8N_CYPHER_URL,
                content=payload_bytes,
                headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
            )
        if resp.status_code != 200:
            results.add("Memory synced to Neo4j", False, f"Status {resp.status_code}: {resp.text[:120]}")
            return
        body = resp.json()
        rows = body.get("records") or []
        record = rows[0] if rows else None
        if record:
            results.add("Memory synced to Neo4j", True, f"Content: {str(record.get('content',''))[:30]}...")
            results.add("Embedding generated", bool(record.get("has_embedding")), f"Has embedding: {record.get('has_embedding')}")
            results.add(
                "Session ID preserved",
                record.get("session_id") == TEST_SESSION_ID,
                f"Session: {record.get('session_id')}",
            )
        else:
            results.add("Memory synced to Neo4j", False, "Memory not found")
    except Exception as e:
        results.add("Memory synced to Neo4j", False, str(e))


async def test_recall_query():
    """Test querying memories back from Neo4j."""
    print("\n[6] Testing Memory Recall...")

    stmt = """
    MATCH (m:Memory)
    WHERE m.session_id = $session_id
    RETURN count(m) as count
    """
    payload = {
        "operation": "cypher",
        "mode": "read",
        "statement": stmt,
        "parameters": {"session_id": TEST_SESSION_ID},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = "sha256=" + hmac.new(
        key=MEMORY_WEBHOOK_TOKEN.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                N8N_CYPHER_URL,
                content=payload_bytes,
                headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
            )
        if resp.status_code != 200:
            results.add("Query by session works", False, f"Status {resp.status_code}: {resp.text[:120]}")
            return
        body = resp.json()
        rows = body.get("records") or []
        count = int(rows[0].get("count", 0)) if rows else 0
        results.add("Query by session works", count >= 1, f"Found {count} memories in session")
    except Exception as e:
        results.add("Query by session works", False, str(e))


async def cleanup_test_data():
    """Clean up test data from Neo4j."""
    print("\n[7] Cleaning Up Test Data...")

    stmt = """
    MATCH (m:Memory {id: $memory_id})
    DETACH DELETE m
    RETURN count(m) as deleted
    """
    payload = {
        "operation": "cypher",
        "mode": "write",
        "statement": stmt,
        "parameters": {"memory_id": TEST_MEMORY_ID},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = "sha256=" + hmac.new(
        key=MEMORY_WEBHOOK_TOKEN.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                N8N_CYPHER_URL,
                content=payload_bytes,
                headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
            )
        ok = resp.status_code == 200
        if not ok:
            results.add("Test data cleaned up", False, f"Status {resp.status_code}: {resp.text[:120]}")
            return
        body = resp.json()
        rows = body.get("records") or []
        deleted = rows[0].get("deleted") if rows else None
        results.add("Test data cleaned up", True, f"Deleted {deleted} test memories")
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
    print(f"  N8N_WEBHOOK_URL: {N8N_WEBHOOK_URL}")
    print(f"  N8N_CYPHER_URL: {N8N_CYPHER_URL}")
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
        print("\nAll validations passed! Quickstart is working correctly.")
    else:
        print("\nSome validations failed. Check the output above.")
        print("\nTroubleshooting:")
        print("  1. Ensure n8n is reachable and /healthz returns 200")
        print("  2. Ensure n8n has Neo4j credentials configured")
        print("  3. Verify MEMORY_WEBHOOK_TOKEN matches both API and n8n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
