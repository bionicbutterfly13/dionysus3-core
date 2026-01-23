#!/usr/bin/env python3
"""
Test script for the MemEvolve /ingest endpoint.
"""

import asyncio
import os
import httpx
import hmac
import hashlib
import json

async def main():
    print("--- Testing MemEvolve /ingest Endpoint ---")
    
    # Configuration
    base_url = "http://localhost:8000"
    endpoint = "/webhook/memevolve/v1/ingest"
    secret = os.getenv("MEMEVOLVE_HMAC_SECRET")

    if not secret:
        print("Error: MEMEVOLVE_HMAC_SECRET environment variable not set.")
        return

    # 1. Prepare Mock Trajectory Data
    trajectory = {
        "trajectory": {
            "steps": [
                {
                    "observation": "Initial state observed. User wants to integrate smolagents.",
                    "thought": "Analyze project structure and dependencies.",
                    "action": "run_shell_command('ls -R')"
                }
            ],
            "metadata": {
                "agent_id": "test_agent_001",
                "session_id": "session_abc_123"
            },
            "summary": "Agent explored the project and analyzed the MemEvolve integration plan."
        }
    }
    body_bytes = json.dumps(trajectory, separators=(',', ':')).encode("utf-8")

    # 2. Generate Signature
    signature = "sha256=" + hmac.new(
        key=secret.encode("utf-8"),
        msg=body_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature
    }

    # 3. Make API Call
    print(f"Sending POST request to {base_url + endpoint}...")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(base_url + endpoint, content=body_bytes, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        response_json = response.json()
        print(f"Response Body: {json.dumps(response_json, indent=2)}")

        # 4. Validate Response
        if response.status_code == 200:
            print("\n✅ Test Passed: Received a 200 OK response.")
        else:
            print(f"\n❌ Test Failed: Received status code {response.status_code}.")
    
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())