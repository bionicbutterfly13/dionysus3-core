#!/usr/bin/env python3
"""
Test script for the MemEvolve /recall endpoint.
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
    print("--- Testing MemEvolve /recall Endpoint ---")
    
    # 1. Load environment variables from .env
    config = dotenv_values(".env")
    secret = config.get("MEMEVOLVE_HMAC_SECRET")

    if not secret:
        print("Error: MEMEVOLVE_HMAC_SECRET not found in .env file.")
        return

    # 2. Start server as a subprocess with the loaded environment
    server_env = {**os.environ, **config}
    server_process = subprocess.Popen(
        ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=server_env
    )
    print(f"Started server with PID: {server_process.pid}. Waiting for it to initialize...")
    time.sleep(5) # Wait for server to start

    try:
        # 3. Prepare and run the test
        base_url = "http://localhost:8000"
        endpoint = "/webhook/memevolve/v1/recall"
        
        body = {
            "query": "smolagents integration",
            "limit": 5,
            "memory_types": ["procedural", "semantic"],
            "include_temporal_metadata": True
        }
        body_bytes = json.dumps(body, separators=(',', ':')).encode("utf-8")

        signature = "sha256=" + hmac.new(
            key=secret.encode("utf-8"),
            msg=body_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature
        }

        print(f"Sending POST request to {base_url + endpoint}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(base_url + endpoint, content=body_bytes, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        response_json = response.json()
        print(f"Response Body: {json.dumps(response_json, indent=2)}")

        if response.status_code == 200:
            print("\n✅ Test Passed: Received a 200 OK response.")
        else:
            print(f"\n❌ Test Failed: Received status code {response.status_code}.")

    finally:
        # 4. Terminate the server
        print(f"\nTerminating server with PID: {server_process.pid}")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())

