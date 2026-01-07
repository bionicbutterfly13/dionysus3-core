import asyncio
import os
import json
import hashlib
import hmac
import httpx
from datetime import datetime

# Configuration
SOURCE_OF_TRUTH_PATH = "/Volumes/Asylum/dev/dionysus3-core/reference/IAS-OFFICIAL-SOURCE-OF-TRUTH.md"
CURRICULUM_ID = "ias-core-v1"
CURRICULUM_TITLE = "The Inner Architect System"

# Mock URL if not provided
WEBHOOK_URL = os.getenv("IAS_WEBHOOK_URL", "http://localhost:5678/webhook/ias/v1/manipulate")
HMAC_SECRET = os.getenv("MEMEVOLVE_HMAC_SECRET", "mock_secret")

# Official Schema Definition (Hardcoded from Source of Truth for strictness)
IAS_SCHEMA = {
    "phases": [
        {
            "id": "phase-1", "title": "REVELATION", "theme": "Predictive Self-Mapping", "order": 1,
            "promise": "Expose the hidden sabotage loop that quietly drives every setback.",
            "goal": "From Hidden Patterns to Clear Insights",
            "lessons": [
                {
                    "id": "lesson-1", "title": "Breakthrough Mapping", "focus": "Self-Awareness", "order": 1,
                    "transformation": "From unknowingly held back to consciously aware of patterns.",
                    "actions": [
                        "Choose problematic behaviors, emotions, or patterns to address",
                        "Pinpoint how these choices are driven by underlying beliefs",
                        "Name what the pattern protects emotionally (e.g. rejection, invisibility)"
                    ]
                },
                {
                    "id": "lesson-2", "title": "Mosaeic Method", "focus": "Mental Agility", "order": 2,
                    "transformation": "From performance anxiety to self-regulated clarity in high-pressure situations.",
                    "actions": [
                        "Choose a context where you want to be more effective under pressure",
                        "Apply the Mosaeic Method to observe thoughts, emotions, and behaviors",
                        "Track how your brain predicts what’s safe and shapes behavior"
                    ]
                },
                {
                    "id": "lesson-3", "title": "Replay Loop Breaker", "focus": "Emotional Clarity & Self-Regulation", "order": 3,
                    "transformation": "From drowning in mental replays to skillful loop breaking.",
                    "actions": [
                        "Spot the story behind your most frustrating replay pattern",
                        "Label the feeling the story causes you to experience",
                        "Identify the protective prediction the replay is trying to fulfill"
                    ]
                }
            ]
        },
        {
            "id": "phase-2", "title": "REPATTERNING", "theme": "Reconsolidation Design", "order": 2,
            "promise": "Recode that loop fast—spark the new identity in real time.",
            "goal": "From Internal Conflict to Sustained Clarity",
            "lessons": [
                {
                    "id": "lesson-4", "title": "Conviction Gauntlet", "focus": "Hope", "order": 4,
                    "transformation": "From belief disruption to integrating new, empowering convictions.",
                    "actions": [
                        "Review prioritized beliefs and associated narratives",
                        "Analyze origins and supporting 'evidence'",
                        "Run an emotionally vivid mismatch experiment that disproves the old belief"
                    ]
                },
                {
                    "id": "lesson-5", "title": "Perspective Matrix", "focus": "Insight", "order": 5,
                    "transformation": "From rigid certainty to flexible, multi-perspective awareness.",
                    "actions": [
                        "Identify and analyze current perspective",
                        "Explore alternative viewpoints and possibilities",
                        "Dialogue between conflicting parts (protector vs visionary)"
                    ]
                },
                {
                    "id": "lesson-6", "title": "Vision Accelerator", "focus": "Inspiration", "order": 6,
                    "transformation": "From playing small to envisioning and owning an authentic future.",
                    "actions": [
                        "Explore expanded possibilities",
                        "Contrast outdated self-image with lived mismatches",
                        "Design a vivid, values-aligned future scenario that feels safe"
                    ]
                }
            ]
        },
        {
            "id": "phase-3", "title": "STABILIZATION", "theme": "Identity–Action Synchronization", "order": 3,
            "promise": "Embed the identity so actions, habits, and results stay congruent.",
            "goal": "From Fragile to Fortified Growth",
            "lessons": [
                {
                    "id": "lesson-7", "title": "Habit Harmonizer", "focus": "Conviction", "order": 7,
                    "transformation": "From relapse fear to anchoring new beliefs.",
                    "actions": [
                        "Internalize new beliefs through structured reflection",
                        "Apply new beliefs in real-life scenarios",
                        "Track small protective relapses as feedback, not failure"
                    ]
                },
                {
                    "id": "lesson-8", "title": "Execution Engine", "focus": "Momentum", "order": 8,
                    "transformation": "From stalled motivation to consistent, value-aligned action.",
                    "actions": [
                        "Create a personalized, testable action plan",
                        "Anticipate challenges and plan supportive responses",
                        "Use feedback loops to refine action without overextension"
                    ]
                },
                {
                    "id": "lesson-9", "title": "Growth Anchor", "focus": "Perseverance", "order": 9,
                    "transformation": "From isolated progress to embedded, resilient growth.",
                    "actions": [
                        "Build your sustainable personal growth system",
                        "Reframe setbacks as predictive updates, not personal regression",
                        "Curate your ongoing circle of support and accountability"
                    ]
                }
            ]
        }
    ]
}

async def send_to_webhook(operation: str, data: dict):
    payload = { "operation": operation, "data": data }
    body = json.dumps(payload)
    signature = "sha256=" + hmac.new(HMAC_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    headers = { "Content-Type": "application/json", "X-Dionysus-Signature": signature, "X-Timestamp": datetime.utcnow().isoformat() }
    
    # MOCK MODE
    if HMAC_SECRET == "mock_secret" or "localhost" in WEBHOOK_URL:
        print(f"[MOCK] {operation} -> {data.get('id', 'unknown')}")
        return

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(WEBHOOK_URL, content=body, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                print(f"✅ {operation}: {resp.json().get('node_id')}")
            else:
                print(f"❌ Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")

async def seed_ias_via_webhook():
    print(f"Starting FULL IAS Seeding via Webhook...")
    
    # 1. Root Curriculum
    await send_to_webhook("upsert_curriculum", {
        "id": CURRICULUM_ID,
        "title": CURRICULUM_TITLE,
        "description": "Neuroscience-backed guided breakthrough program for high-performing analytical empaths."
    })
    
    # 2. Iterate Phases -> Modules
    for phase in IAS_SCHEMA["phases"]:
        mod_id = f"module-{phase['id']}"
        await send_to_webhook("upsert_module", {
            "parent_id": CURRICULUM_ID,
            "id": mod_id,
            "title": f"{phase['title']}: {phase['theme']}",
            "phase": phase['title'],
            "order": phase['order'],
            "promise": phase['promise'],
            "goal": phase['goal']
        })
        
        # 3. Iterate Lessons
        for lesson in phase["lessons"]:
            less_id = f"lesson-{lesson['id']}-v1"
            await send_to_webhook("upsert_lesson", {
                "parent_id": mod_id,
                "id": less_id,
                "title": lesson['title'],
                "order": lesson['order'],
                "focus": lesson['focus'],
                "transformation": lesson['transformation']
            })
            
            # 4. Iterate Actions (As Assets or Sub-nodes? Using 'upsert_action' logic or generic Asset)
            # Simplification: Creating them as 'Action' Assets linked to the Lesson
            for i, action_text in enumerate(lesson["actions"]):
                act_id = f"{less_id}-action-{i+1}"
                await send_to_webhook("link_asset", {
                    "parent_id": less_id,
                    "id": act_id,
                    "type": "action_step",
                    "path": "N/A", # Virtual node
                    "description": action_text
                })

    # 5. Link Source of Truth Asset
    asset_id = f"asset-{CURRICULUM_ID}-sot"
    await send_to_webhook("link_asset", {
        "parent_id": CURRICULUM_ID,
        "id": asset_id,
        "type": "notion_snapshot",
        "path": "Notion ID / Export",
        "description": "Snapshot of IAS Official High View Map (Master in Notion)"
    })

    # 6. Launch Event
    launch_id = f"launch-{CURRICULUM_ID}-jan8"
    await send_to_webhook("upsert_launch", {
        "parent_id": CURRICULUM_ID,
        "id": launch_id,
        "deadline": "2026-01-08T23:59:59-05:00",
        "price_charter": 3975,
        "price_regular": 5475,
        "framework": "Todd Brown Bullet Campaign"
    })
    
    print("\n✅ Full Granular Seeding Complete.")

if __name__ == "__main__":
    asyncio.run(seed_ias_via_webhook())
