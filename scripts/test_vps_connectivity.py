#!/usr/bin/env python3
"""
VPS Connectivity Test Script
Feature: 002-remote-persistence-safety

Tests connectivity to remote services on VPS:
- Neo4j (bolt://localhost:7687 via SSH tunnel)
- n8n (http://localhost:5678 via SSH tunnel)
- Ollama (http://localhost:11434 via SSH tunnel)

Usage:
    # Start SSH tunnel first:
    ssh -L 7474:127.0.0.1:7474 -L 7687:127.0.0.1:7687 \
        -L 5678:127.0.0.1:5678 -L 11434:127.0.0.1:11434 \
        -N root@72.61.78.89

    # Then run this script:
    python scripts/test_vps_connectivity.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_neo4j() -> bool:
    """Test Neo4j connection via bolt protocol."""
    try:
        from neo4j import AsyncGraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")

        if not password:
            print("⚠ NEO4J_PASSWORD not set in environment")
            return False

        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        async with driver.session() as session:
            result = await session.run("RETURN 1 as n")
            record = await result.single()
            if record and record["n"] == 1:
                print(f"✓ Neo4j connected at {uri}")
                await driver.close()
                return True
        await driver.close()
        return False
    except ImportError:
        print("✗ neo4j package not installed. Run: pip install neo4j")
        return False
    except Exception as e:
        print(f"✗ Neo4j connection failed: {e}")
        return False


async def test_n8n() -> bool:
    """Test n8n health endpoint."""
    try:
        url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/memory-sync")
        # Extract base URL from webhook URL
        base_url = "/".join(url.split("/")[:3])
        health_url = f"{base_url}/healthz"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
            if response.status_code == 200:
                print(f"✓ n8n health check passed at {base_url}")
                return True
            else:
                print(f"⚠ n8n returned status {response.status_code}")
                return False
    except httpx.ConnectError:
        print(f"✗ n8n connection refused at {base_url}")
        return False
    except Exception as e:
        print(f"✗ n8n health check failed: {e}")
        return False


async def test_ollama() -> bool:
    """Test Ollama API and check for embedding model."""
    try:
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        tags_url = f"{url}/api/tags"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(tags_url)
            if response.status_code != 200:
                print(f"✗ Ollama returned status {response.status_code}")
                return False

            data = response.json()
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]

            if model in models or any(model in m for m in models):
                print(f"✓ Ollama connected at {url}")
                print(f"  Models available: {models}")
                return True
            else:
                print(f"⚠ Ollama connected but {model} not found")
                print(f"  Available models: {models}")
                print(f"  Run: ollama pull {model}")
                return False
    except httpx.ConnectError:
        print(f"✗ Ollama connection refused at {url}")
        return False
    except Exception as e:
        print(f"✗ Ollama check failed: {e}")
        return False


async def test_webhook_endpoint() -> bool:
    """Test that the n8n webhook endpoint exists (without sending real data)."""
    try:
        url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/memory-sync")

        # OPTIONS request to check if endpoint exists
        async with httpx.AsyncClient(timeout=5.0) as client:
            # We'll send a malformed request to see if the endpoint responds
            # n8n will return 400 for bad payload, which means endpoint exists
            response = await client.post(
                url,
                json={},  # Empty payload will fail validation
                headers={"Content-Type": "application/json"},
            )

            # Any response (even error) means endpoint exists
            if response.status_code in [200, 400, 401, 403, 500]:
                print(f"✓ Webhook endpoint exists at {url}")
                return True
            else:
                print(f"⚠ Webhook endpoint returned {response.status_code}")
                return False
    except httpx.ConnectError:
        print(f"✗ Cannot reach webhook at {url}")
        return False
    except Exception as e:
        print(f"✗ Webhook check failed: {e}")
        return False


async def main():
    """Run all connectivity tests."""
    print("=" * 60)
    print("VPS Connectivity Test")
    print("Feature: 002-remote-persistence-safety")
    print("=" * 60)
    print()

    # Check if SSH tunnel is likely running
    print("Prerequisites:")
    print("  Ensure SSH tunnel is running:")
    print("    ssh -L 7474:127.0.0.1:7474 -L 7687:127.0.0.1:7687 \\")
    print("        -L 5678:127.0.0.1:5678 -L 11434:127.0.0.1:11434 \\")
    print("        -N root@72.61.78.89")
    print()

    results = {
        "neo4j": await test_neo4j(),
        "n8n": await test_n8n(),
        "ollama": await test_ollama(),
        "webhook": await test_webhook_endpoint(),
    }

    print()
    print("=" * 60)
    print("Summary:")
    all_passed = all(results.values())

    for service, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {service}: {status}")

    print()
    if all_passed:
        print("All connectivity tests passed!")
        return 0
    else:
        print("Some tests failed. Check configuration and SSH tunnel.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
