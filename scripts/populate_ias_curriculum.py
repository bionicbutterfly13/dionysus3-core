#!/usr/bin/env python3
"""
Populate IAS Curriculum in Neo4j via n8n Webhook

CRITICAL: This script ONLY uses n8n webhooks. NEVER touches Neo4j directly.

Usage:
    python scripts/populate_ias_curriculum.py

Prerequisites:
    1. Import n8n-workflows/ias-curriculum-manager.json into n8n
    2. Activate the workflow
    3. Verify n8n is running at https://72.61.78.89:5678

Author: Dr. Mani Saint-Victor
Date: 2026-01-01
"""

import json
import requests
from pathlib import Path
import sys

# n8n webhook base URL
N8N_BASE_URL = "https://72.61.78.89:5678/webhook"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_DATA_FILE = PROJECT_ROOT / "data" / "ias-curriculum-full.json"


def load_curriculum_data():
    """Load the full IAS curriculum from JSON file."""
    print(f"📂 Loading curriculum data from: {CURRICULUM_DATA_FILE}")

    if not CURRICULUM_DATA_FILE.exists():
        print(f"❌ ERROR: Curriculum data file not found: {CURRICULUM_DATA_FILE}")
        sys.exit(1)

    with open(CURRICULUM_DATA_FILE, 'r') as f:
        data = json.load(f)

    print(f"✅ Loaded curriculum with {data['curriculum']['total_lessons']} lessons")
    return data


def populate_curriculum(data):
    """
    Populate the full IAS curriculum via n8n webhook.

    NEVER touches Neo4j directly - only uses n8n webhook endpoint.
    """
    url = f"{N8N_BASE_URL}/ias/create-curriculum"

    print(f"\n🌐 Calling n8n webhook: {url}")
    print(f"📤 Sending curriculum data...")

    try:
        response = requests.post(
            url,
            json=data,
            headers={'Content-Type': 'application/json'},
            verify=False  # Self-signed cert on VPS
        )

        response.raise_for_status()
        result = response.json()

        print(f"✅ Curriculum created successfully!")
        print(f"📊 Response: {json.dumps(result, indent=2)}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR calling n8n webhook: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        sys.exit(1)


def query_curriculum():
    """
    Query the curriculum structure via n8n webhook to verify creation.

    NEVER touches Neo4j directly - only uses n8n webhook endpoint.
    """
    url = f"{N8N_BASE_URL}/ias/query-curriculum"

    print(f"\n🔍 Querying curriculum via n8n webhook: {url}")

    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        result = response.json()

        print(f"✅ Query successful!")

        # Parse and display structure
        curriculum = result.get('curriculum', {})
        phases = result.get('phases', [])
        lessons = result.get('lessons', [])

        print(f"\n📚 Curriculum: {curriculum.get('name', 'N/A')}")
        print(f"   Version: {curriculum.get('version', 'N/A')}")
        print(f"   Total Phases: {curriculum.get('total_phases', 0)}")
        print(f"   Total Lessons: {curriculum.get('total_lessons', 0)}")

        print(f"\n📖 Phases:")
        for phase in sorted(phases, key=lambda p: p.get('order', 0)):
            print(f"   {phase.get('order')}. {phase.get('name')} - {phase.get('description', 'N/A')[:60]}...")

        print(f"\n📝 Lessons:")
        for lesson in sorted(lessons, key=lambda l: l.get('global_order', 0)):
            print(f"   {lesson.get('global_order')}. {lesson.get('name')} (Phase {lesson.get('phase_order')})")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR querying curriculum: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None


def get_lesson_details(lesson_id: str):
    """
    Get detailed information about a specific lesson via n8n webhook.

    NEVER touches Neo4j directly - only uses n8n webhook endpoint.
    """
    url = f"{N8N_BASE_URL}/ias/get-lesson/{lesson_id}"

    print(f"\n🔍 Getting lesson details for: {lesson_id}")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        result = response.json()

        lesson = result.get('lesson', {})
        steps = result.get('steps', [])

        print(f"\n📖 Lesson: {lesson.get('name', 'N/A')}")
        print(f"   Description: {lesson.get('description', 'N/A')}")
        print(f"   Objective: {lesson.get('objective', 'N/A')}")
        print(f"   Total Steps: {len(steps)}")

        for step in sorted(steps, key=lambda s: s.get('order', 0)):
            print(f"\n   Step {step.get('order')}: {step.get('name')}")
            print(f"      Instruction: {step.get('instruction', 'N/A')[:80]}...")
            print(f"      Tagline: {step.get('tagline', 'N/A')}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR getting lesson details: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None


def main():
    """
    Main execution flow.

    Demonstrates proper n8n-only access pattern for IAS curriculum.
    """
    print("=" * 60)
    print("IAS Curriculum Population Script")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: This script uses n8n webhooks ONLY.")
    print("   NEVER touches Neo4j directly per prime directive.\n")

    # Step 1: Load curriculum data
    data = load_curriculum_data()

    # Step 2: Populate curriculum via n8n
    populate_curriculum(data)

    # Step 3: Verify by querying
    query_curriculum()

    # Step 4: Get detailed lesson view (example: Replay Loop Breaker)
    get_lesson_details("lesson-3")

    print("\n" + "=" * 60)
    print("✅ IAS Curriculum population complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. View curriculum in Neo4j Browser (via n8n query webhook)")
    print("  2. Add remaining lessons (4, 5, 6, 8, 9) as content becomes available")
    print("  3. Build AI systems that query this curriculum via n8n webhooks")
    print("\n⚠️  Remember: ALL Neo4j access MUST use n8n webhooks!")


if __name__ == "__main__":
    main()
