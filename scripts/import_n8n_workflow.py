#!/usr/bin/env python3
"""
n8n Workflow Import Script
Feature: 002-remote-persistence-safety

Imports the memory_sync workflow from contracts/n8n-workflow.json to n8n.

Note: This script uses the n8n REST API. You may need to enable API access
in your n8n instance and provide an API key.

Alternative: Manual import via n8n UI at http://localhost:5678
1. Login to n8n
2. Go to Workflows > Import from File
3. Select specs/002-remote-persistence-safety/contracts/n8n-workflow.json
4. Configure Neo4j credentials in Credentials section
5. Activate the workflow

Usage:
    # Start SSH tunnel first:
    ssh -L 5678:127.0.0.1:5678 -N root@72.61.78.89

    # Then run this script:
    python scripts/import_n8n_workflow.py
"""

import asyncio
import json
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


WORKFLOW_FILE = (
    project_root / "specs" / "002-remote-persistence-safety" / "contracts" / "n8n-workflow.json"
)


async def import_workflow():
    """Import workflow to n8n via REST API."""
    # n8n base URL
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/memory-sync")
    base_url = "/".join(webhook_url.split("/")[:3])
    api_url = f"{base_url}/api/v1"

    # n8n API key (if configured)
    api_key = os.getenv("N8N_API_KEY", "")

    print(f"n8n base URL: {base_url}")

    # Load workflow JSON
    if not WORKFLOW_FILE.exists():
        print(f"✗ Workflow file not found: {WORKFLOW_FILE}")
        return False

    with open(WORKFLOW_FILE) as f:
        workflow_data = json.load(f)

    print(f"✓ Loaded workflow: {workflow_data.get('name', 'Unknown')}")

    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-N8N-API-KEY"] = api_key

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check if n8n is reachable
        try:
            health_response = await client.get(f"{base_url}/healthz")
            if health_response.status_code != 200:
                print(f"⚠ n8n health check returned {health_response.status_code}")
        except httpx.ConnectError:
            print(f"✗ Cannot connect to n8n at {base_url}")
            print("  Ensure SSH tunnel is running and n8n is accessible")
            return False

        # Try to import via API
        try:
            # n8n workflow import endpoint
            import_url = f"{api_url}/workflows"

            response = await client.post(import_url, json=workflow_data, headers=headers)

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Workflow imported successfully!")
                print(f"  ID: {result.get('id')}")
                print(f"  Name: {result.get('name')}")
                return True
            elif response.status_code == 401:
                print("⚠ API authentication required")
                print("  Set N8N_API_KEY in your .env file")
                print("  Or import manually via n8n UI")
                return False
            elif response.status_code == 409:
                print("⚠ Workflow already exists")
                print("  Update it manually via n8n UI if needed")
                return True
            else:
                print(f"⚠ Import returned {response.status_code}")
                print(f"  Response: {response.text}")
                return False

        except Exception as e:
            print(f"⚠ API import failed: {e}")
            print()
            print("Manual import instructions:")
            print("  1. Open n8n at http://localhost:5678")
            print("  2. Go to Workflows > Import from File")
            print(f"  3. Select: {WORKFLOW_FILE}")
            print("  4. Configure Neo4j credentials:")
            print("     - Host: neo4j")
            print("     - Port: 7687")
            print("     - User: neo4j")
            print("     - Password: (from NEO4J_PASSWORD env)")
            print("  5. Activate the workflow")
            return False


async def main():
    """Run workflow import."""
    print("=" * 60)
    print("n8n Workflow Import")
    print("Feature: 002-remote-persistence-safety")
    print("=" * 60)
    print()

    print("Prerequisites:")
    print("  Ensure SSH tunnel is running:")
    print("    ssh -L 5678:127.0.0.1:5678 -N root@72.61.78.89")
    print()

    success = await import_workflow()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
