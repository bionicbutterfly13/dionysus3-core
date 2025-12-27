
import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from api.services.ghl_service import GHLService

# Load environment variables
load_dotenv()

# Extracted from the provided API key
LOCATION_ID = "fN0QarEDRnyO351rNCD3"
WORKFLOW_NAME = "IAS Group Long Nurture Workflow"

async def sync_ghl_emails():
    print(f"🚀 Connecting to GHL for Location: {LOCATION_ID}...")
    ghl = GHLService()
    
    if not ghl.api_key:
        print("Error: GHL_API_KEY not found in environment.")
        return

    # 1. List Workflows
    print(f"🔍 Searching for workflow: '{WORKFLOW_NAME}'...")
    workflows = await ghl.get_workflows(LOCATION_ID)
    
    target_workflow = None
    for wf in workflows:
        if wf.get("name") == WORKFLOW_NAME:
            target_workflow = wf
            break
            
    if not target_workflow:
        print(f"❌ Could not find workflow: {WORKFLOW_NAME}")
        print("Available workflows:")
        for wf in workflows:
            print(f"- {wf.get('name')} (id: {wf.get('id')})")
        return

    workflow_id = target_workflow["id"]
    print(f"✅ Found Workflow! ID: {workflow_id}")

    # 2. Get Workflow Details (Actions)
    print("📥 Retrieving email content from workflow actions...")
    # Some GHL API versions include actions in the list, others need a detail call
    # If the list response is enough, we use it. Otherwise we'd need another endpoint.
    # Note: GHL API v2 Workflows endpoint can be limited. 
    # If direct workflow action retrieval is restricted, we might need to 
    # look at the 'Campaigns' if it's an old-style campaign.
    
    # For now, let's print what we have in the workflow object
    print(json.dumps(target_workflow, indent=2))
    
    # If target_workflow doesn't have actions, we try to fetch detail if available
    # GHL API v2 doesn't always expose workflow nodes via this endpoint.
    # We might need to iterate through 'emails' or 'campaigns' instead.
    
async def fetch_all_emails():
    # Fallback if workflows don't show actions: Fetch all email templates or campaigns
    ghl = GHLService()
    print("🔍 Fetching all email templates as fallback...")
    # This would use a different GHL endpoint: GET /emails/builder
    # But let's first see what the workflow gives us.
    pass

if __name__ == "__main__":
    asyncio.run(sync_ghl_emails())
