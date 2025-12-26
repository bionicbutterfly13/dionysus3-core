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
import subprocess
import time
from dotenv import dotenv_values

async def main():
    print("--- Testing MemEvolve /ingest Endpoint ---")
    
    # 1. Load environment
    config = dotenv_values(".env")
    secret = config.get("MEMEVOLVE_HMAC_SECRET")
    anthropic_key = config.get("ANTHROPIC_API_KEY")

    if not secret or not anthropic_key:
        print("Error: MEMEVOLVE_HMAC_SECRET or ANTHROPIC_API_KEY not found in .env file.")
        return

    # 2. Start server
    server_env = {**os.environ, **config}
    server_process = subprocess.Popen(
        ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=server_env
    )
    print(f"Started server with PID: {server_process.pid}. Waiting for it to initialize...")
    time.sleep(5)

    try:
        # 3. Prepare and run the test
        base_url = "http://localhost:8000"
        endpoint = "/webhook/memevolve/v1/ingest"

        trajectory = {
            "trajectory": {
                "steps": [
                    {"observation": "User wants to integrate smolagents.", "thought": "Analyze project structure."},
                    {"observation": "User mentioned MemEvolve.", "thought": "Analyze integration plan."}
                ],
                "metadata": {"agent_id": "test_agent_001", "session_id": "session_abc_123"},
                "summary": "Agent explored smolagents and MemEvolve integration."
            }
        }
        body_bytes = json.dumps(trajectory, separators=(',', ':')).encode("utf-8")

        signature = "sha256=" + hmac.new(
            key=secret.encode("utf-8"), msg=body_bytes, digestmod=hashlib.sha256
        ).hexdigest()

        headers = {"Content-Type": "application/json", "X-Webhook-Signature": signature}

        print(f"Sending POST request to {base_url + endpoint}...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(base_url + endpoint, content=body_bytes, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        response_json = response.json()
        print(f"Response Body: {json.dumps(response_json, indent=2)}")

        if response.status_code == 200:
            print("\n✅ Test Passed: Received a 200 OK response.")
        else:
            print(f"\n❌ Test Failed: Received status code {response.status_code}.")

    finally:
        # 4. Terminate server
        print(f"\nTerminating server with PID: {server_process.pid}")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())

