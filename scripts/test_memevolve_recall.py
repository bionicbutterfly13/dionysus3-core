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
    
    # Debugging .env loading
    env_path = "/app/.env"
    print(f"DEBUG: Attempting to load .env from: {env_path}")
    if os.path.exists(env_path):
        print(f"DEBUG: .env file found at {env_path}")
        with open(env_path, 'r') as f:
            print("DEBUG: .env file content:\n---")
            print(f.read())
            print("---")
    else:
        print(f"DEBUG: .env file NOT found at {env_path}")

    # Load environment variables from .env
    config = dotenv_values(env_path)
    print(f"DEBUG: Loaded config from .env: {config}")

    secret = config.get("MEMEVOLVE_HMAC_SECRET")
    
    # Configuration
    base_url = "http://localhost:8000"
    endpoint = "/webhook/memevolve/v1/recall"

    if not secret:
        print("Error: MEMEVOLVE_HMAC_SECRET not found in .env file.")
        return

    # 2. Start server as a subprocess with the loaded environment
    # Note: This is now managed by the shell executing the tests.
    # The container itself is already running the API server.
    # We only need the config for the test client.


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

