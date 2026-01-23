"""
MemEvolve HMAC Ping Test Script

Simulates a MemEvolve client sending a signed request to Dionysus API.
Feature: 009-memevolve-integration
Phase: 1 - Foundation

Usage:
    python scripts/test_memevolve_ping.py [--endpoint health|ingest|recall]
"""

import asyncio
import os
import sys
import json
import argparse
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.services.hmac_utils import sign_request


load_dotenv()


async def test_health(client: httpx.AsyncClient, base_url: str, secret: str) -> bool:
    """Test the /health endpoint."""
    print("\n--- Testing /webhook/memevolve/v1/health ---")
    
    body = {"ping": "hello", "timestamp": datetime.utcnow().isoformat()}
    body_bytes = json.dumps(body).encode("utf-8")
    
    headers = sign_request(body_bytes, secret)
    
    try:
        response = await client.post(
            f"{base_url}/webhook/memevolve/v1/health",
            content=body_bytes,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
        if response.status_code == 200 and response.json().get("status") == "ok":
            print("\n✅ Health check passed: HMAC signature validated!")
            return True
        else:
            print("\n❌ Health check failed: Unexpected response")
            return False
            
    except httpx.ConnectError as e:
        print(f"\n❌ Connection failed: Is the API running at {base_url}?")
        print(f"   Error: {e}")
        return False


async def test_ingest(client: httpx.AsyncClient, base_url: str, secret: str) -> bool:
    """Test the /ingest endpoint."""
    print("\n--- Testing /webhook/memevolve/v1/ingest ---")
    
    body = {
        "trajectory": {
            "steps": [
                {"observation": "Test memory 1", "thought": "Reasoning 1", "action": "Action 1"},
                {"observation": "Test memory 2", "thought": "Reasoning 2", "action": "Action 2"}
            ],
            "metadata": {
                "agent_id": "test-agent",
                "session_id": "test-session",
                "project_id": "test-project",
                "trajectory_type": "episodic"
            },
            "summary": "This is a test summary"
        }
    }
    body_bytes = json.dumps(body).encode("utf-8")
    
    headers = sign_request(body_bytes, secret)
    
    try:
        response = await client.post(
            f"{base_url}/webhook/memevolve/v1/ingest",
            content=body_bytes,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
        if response.status_code == 200 and response.json().get("success"):
            print("\n✅ Ingest test passed!")
            return True
        else:
            print("\n❌ Ingest test failed")
            return False
            
    except httpx.ConnectError as e:
        print(f"\n❌ Connection failed: {e}")
        return False


async def test_recall(client: httpx.AsyncClient, base_url: str, secret: str) -> bool:
    """Test the /recall endpoint."""
    print("\n--- Testing /webhook/memevolve/v1/recall ---")
    
    body = {
        "query": "test memory recall",
        "context": {"agent_id": "test-agent"},
        "max_results": 5
    }
    body_bytes = json.dumps(body).encode("utf-8")
    
    headers = sign_request(body_bytes, secret)
    
    try:
        response = await client.post(
            f"{base_url}/webhook/memevolve/v1/recall",
            content=body_bytes,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ Recall test passed!")
            return True
        else:
            print("\n❌ Recall test failed")
            return False
            
    except httpx.ConnectError as e:
        print(f"\n❌ Connection failed: {e}")
        return False


async def test_invalid_signature(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test that invalid signatures are rejected."""
    print("\n--- Testing Invalid Signature Rejection ---")
    
    body = {"ping": "hello"}
    body_bytes = json.dumps(body).encode("utf-8")
    
    # Use wrong signature
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": "sha256=invalid_signature_here"
    }
    
    try:
        response = await client.post(
            f"{base_url}/webhook/memevolve/v1/health",
            content=body_bytes,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("\n✅ Invalid signature correctly rejected with 401!")
            return True
        else:
            print(f"\n❌ Expected 401, got {response.status_code}")
            return False
            
    except httpx.ConnectError as e:
        print(f"\n❌ Connection failed: {e}")
        return False


async def test_missing_signature(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test that missing signatures are rejected."""
    print("\n--- Testing Missing Signature Rejection ---")
    
    body = {"ping": "hello"}
    body_bytes = json.dumps(body).encode("utf-8")
    
    # No signature header
    headers = {"Content-Type": "application/json"}
    
    try:
        response = await client.post(
            f"{base_url}/webhook/memevolve/v1/health",
            content=body_bytes,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("\n✅ Missing signature correctly rejected with 400!")
            return True
        else:
            print(f"\n❌ Expected 400, got {response.status_code}")
            return False
            
    except httpx.ConnectError as e:
        print(f"\n❌ Connection failed: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test MemEvolve HMAC integration")
    parser.add_argument(
        "--endpoint",
        choices=["health", "ingest", "recall", "all"],
        default="health",
        help="Which endpoint to test"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the API"
    )
    parser.add_argument(
        "--security-tests",
        action="store_true",
        help="Also run security tests (invalid/missing signatures)"
    )
    args = parser.parse_args()
    
    print("=" * 50)
    print("MemEvolve HMAC Ping Test")
    print("=" * 50)
    
    secret = os.getenv("MEMEVOLVE_HMAC_SECRET")
    
    if not secret:
        print("\n❌ Error: MEMEVOLVE_HMAC_SECRET not found in environment")
        print("   Please set it in your .env file:")
        print('   MEMEVOLVE_HMAC_SECRET="your-secret-here"')
        return 1
    
    print(f"\nBase URL: {args.base_url}")
    print(f"Secret configured: {'Yes' if secret else 'No'}")
    
    results = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        if args.endpoint in ["health", "all"]:
            results.append(await test_health(client, args.base_url, secret))
        
        if args.endpoint in ["ingest", "all"]:
            results.append(await test_ingest(client, args.base_url, secret))
        
        if args.endpoint in ["recall", "all"]:
            results.append(await test_recall(client, args.base_url, secret))
        
        if args.security_tests:
            results.append(await test_invalid_signature(client, args.base_url))
            results.append(await test_missing_signature(client, args.base_url))
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
