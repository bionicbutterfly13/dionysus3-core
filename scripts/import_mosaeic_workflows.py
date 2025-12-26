#!/usr/bin/env python3
"""
MoSAEIC Workflow Import Script

Imports MoSAEIC v1 workflows to n8n via REST API.

Prerequisites:
    1. SSH tunnel to VPS: ssh -L 5678:localhost:5678 mani@72.61.78.89
    2. N8N_API_KEY environment variable set
    3. n8n environment variables configured:
       - MEMORY_WEBHOOK_TOKEN
       - NEO4J_BASIC_AUTH

Usage:
    # Start SSH tunnel first:
    ssh -L 5678:localhost:5678 -N mani@72.61.78.89

    # Then run:
    N8N_API_KEY=your-key python scripts/import_mosaeic_workflows.py

Alternative: Manual import via n8n UI
    1. Open http://localhost:5678
    2. Workflows > Import from File
    3. Import each workflow from n8n-workflows/
    4. Activate workflows
"""

import asyncio
import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx

WORKFLOWS_DIR = project_root / "n8n-workflows"

MOSAEIC_WORKFLOWS = [
    "mosaeic_v1_profile_initialize.json",
    "mosaeic_v1_capture_create.json",
    "mosaeic_v1_pattern_detect.json",
]

N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")


async def check_n8n_health() -> bool:
    """Check if n8n is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{N8N_BASE_URL}/healthz")
            return response.status_code == 200
    except Exception:
        return False


async def get_existing_workflows(client: httpx.AsyncClient, headers: dict) -> dict:
    """Get list of existing workflows by name."""
    try:
        response = await client.get(f"{N8N_BASE_URL}/api/v1/workflows", headers=headers)
        if response.status_code == 200:
            data = response.json()
            workflows = data.get("data", [])
            return {w["name"]: w["id"] for w in workflows}
        return {}
    except Exception:
        return {}


async def import_workflow(
    client: httpx.AsyncClient, headers: dict, workflow_path: Path, existing: dict
) -> dict:
    """Import a single workflow."""
    with open(workflow_path) as f:
        workflow_data = json.load(f)

    workflow_name = workflow_data.get("name", workflow_path.stem)
    result = {"name": workflow_name, "file": workflow_path.name, "success": False}

    # Check if workflow already exists
    if workflow_name in existing:
        workflow_id = existing[workflow_name]
        # Update existing workflow
        try:
            response = await client.patch(
                f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
                json=workflow_data,
                headers=headers,
            )
            if response.status_code == 200:
                result["success"] = True
                result["action"] = "updated"
                result["id"] = workflow_id
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            result["error"] = str(e)
    else:
        # Create new workflow
        try:
            response = await client.post(
                f"{N8N_BASE_URL}/api/v1/workflows",
                json=workflow_data,
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                result["success"] = True
                result["action"] = "created"
                result["id"] = data.get("id")
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            result["error"] = str(e)

    return result


async def activate_workflow(
    client: httpx.AsyncClient, headers: dict, workflow_id: str
) -> bool:
    """Activate a workflow."""
    try:
        response = await client.patch(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
            json={"active": True},
            headers=headers,
        )
        return response.status_code == 200
    except Exception:
        return False


async def main():
    """Import MoSAEIC workflows."""
    print("=" * 60)
    print("MoSAEIC Workflow Import")
    print("=" * 60)
    print()

    # Check API key
    if not N8N_API_KEY:
        print("ERROR: N8N_API_KEY environment variable not set")
        print()
        print("Get API key from n8n:")
        print("  1. Open n8n Settings")
        print("  2. Go to API")
        print("  3. Create API Key")
        print()
        print("Then run:")
        print("  N8N_API_KEY=your-key python scripts/import_mosaeic_workflows.py")
        return 1

    # Check n8n health
    print(f"Checking n8n at {N8N_BASE_URL}...")
    if not await check_n8n_health():
        print(f"ERROR: Cannot reach n8n at {N8N_BASE_URL}")
        print()
        print("Ensure SSH tunnel is running:")
        print("  ssh -L 5678:localhost:5678 -N mani@72.61.78.89")
        return 1
    print("  n8n is reachable")
    print()

    # Check workflow files
    print("Workflow files:")
    missing = []
    for wf in MOSAEIC_WORKFLOWS:
        path = WORKFLOWS_DIR / wf
        if path.exists():
            print(f"  [OK] {wf}")
        else:
            print(f"  [MISSING] {wf}")
            missing.append(wf)

    if missing:
        print(f"\nERROR: Missing workflow files: {missing}")
        return 1
    print()

    # Import workflows
    headers = {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get existing workflows
        print("Checking existing workflows...")
        existing = await get_existing_workflows(client, headers)
        if existing:
            print(f"  Found {len(existing)} existing workflows")
        print()

        # Import each workflow
        print("Importing workflows:")
        results = []
        for wf in MOSAEIC_WORKFLOWS:
            path = WORKFLOWS_DIR / wf
            result = await import_workflow(client, headers, path, existing)
            results.append(result)

            if result["success"]:
                action = result.get("action", "imported")
                print(f"  [OK] {result['name']} ({action}, ID: {result.get('id', 'N/A')})")

                # Activate workflow
                if result.get("id"):
                    if await activate_workflow(client, headers, result["id"]):
                        print(f"       Activated!")
                    else:
                        print(f"       WARNING: Failed to activate")
            else:
                print(f"  [FAIL] {result['name']}: {result.get('error', 'Unknown error')}")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    success_count = sum(1 for r in results if r["success"])
    print(f"  Imported: {success_count}/{len(results)}")

    if success_count == len(results):
        print()
        print("Webhook endpoints available:")
        print(f"  POST {N8N_BASE_URL}/webhook/mosaeic/v1/profile/initialize")
        print(f"  POST {N8N_BASE_URL}/webhook/mosaeic/v1/capture/create")
        print(f"  POST {N8N_BASE_URL}/webhook/mosaeic/v1/pattern/detect")
        print()
        print("Required n8n environment variables:")
        print("  MEMORY_WEBHOOK_TOKEN - HMAC signature validation")
        print("  NEO4J_BASIC_AUTH     - Base64 encoded 'neo4j:password'")
        return 0
    else:
        print()
        print("Some imports failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
