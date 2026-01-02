#!/usr/bin/env python3
"""
Populate Unified IAS Curriculum in Neo4j via n8n Webhook

Combines:
1. Full 9-lesson structure (business/marketing layer)
2. Lesson 3 pedagogical framework (coaching layer with obstacles/actions)

CRITICAL: Uses n8n webhooks ONLY. NEVER touches Neo4j directly.

Usage:
    python scripts/populate_ias_unified.py

Prerequisites:
    1. Import n8n-workflows/ias-unified-manager.json into n8n
    2. Activate the workflow
    3. Verify n8n is running at https://72.61.78.89:5678
    4. Set MEMEVOLVE_HMAC_SECRET environment variable

Author: Dr. Mani Saint-Victor
Date: 2026-01-02
"""

import json
import requests
import hashlib
import hmac
import os
from datetime import datetime
from pathlib import Path

# Configuration
N8N_WEBHOOK_URL = "https://72.61.78.89:5678/webhook/ias/v1/manipulate"
HMAC_SECRET = os.getenv("MEMEVOLVE_HMAC_SECRET", "")
PROJECT_ROOT = Path(__file__).parent.parent

# Full Curriculum Schema (from seed_ias_via_webhook.py)
CURRICULUM_SCHEMA = {
    "id": "ias-core-v1",
    "title": "The Inner Architect System",
    "description": "Neuroscience-backed guided breakthrough program for high-performing analytical empaths",
    "target_audience": "Analytical Empaths",
    "total_modules": 3,
    "total_lessons": 9,
    "phases": [
        {
            "id": "phase-1",
            "title": "REVELATION",
            "theme": "Predictive Self-Mapping",
            "order": 1,
            "promise": "Expose the hidden sabotage loop that quietly drives every setback.",
            "goal": "From Hidden Patterns to Clear Insights",
            "lessons": [
                {
                    "id": "lesson-1-v1",
                    "title": "Breakthrough Mapping",
                    "focus": "Self-Awareness",
                    "order": 1,
                    "transformation": "From unknowingly held back to consciously aware of patterns."
                },
                {
                    "id": "lesson-2-v1",
                    "title": "Mosaeic Method",
                    "focus": "Mental Agility",
                    "order": 2,
                    "transformation": "From performance anxiety to self-regulated clarity in high-pressure situations."
                },
                {
                    "id": "lesson-3-v1",
                    "title": "Replay Loop Breaker",
                    "focus": "Emotional Clarity & Self-Regulation",
                    "order": 3,
                    "transformation": "From drowning in mental replays to skillful loop breaking.",
                    "has_pedagogical_framework": True
                }
            ]
        },
        {
            "id": "phase-2",
            "title": "REPATTERNING",
            "theme": "Reconsolidation Design",
            "order": 2,
            "promise": "Recode that loop fast—spark the new identity in real time.",
            "goal": "From Internal Conflict to Sustained Clarity",
            "lessons": [
                {
                    "id": "lesson-4-v1",
                    "title": "Conviction Gauntlet",
                    "focus": "Hope",
                    "order": 4,
                    "transformation": "From belief disruption to integrating new, empowering convictions."
                },
                {
                    "id": "lesson-5-v1",
                    "title": "Perspective Matrix",
                    "focus": "Insight",
                    "order": 5,
                    "transformation": "From rigid certainty to flexible, multi-perspective awareness."
                },
                {
                    "id": "lesson-6-v1",
                    "title": "Vision Accelerator",
                    "focus": "Inspiration",
                    "order": 6,
                    "transformation": "From playing small to envisioning and owning an authentic future."
                }
            ]
        },
        {
            "id": "phase-3",
            "title": "STABILIZATION",
            "theme": "Identity–Action Synchronization",
            "order": 3,
            "promise": "Embed the identity so actions, habits, and results stay congruent.",
            "goal": "From Fragile to Fortified Growth",
            "lessons": [
                {
                    "id": "lesson-7-v1",
                    "title": "Habit Harmonizer",
                    "focus": "Conviction",
                    "order": 7,
                    "transformation": "From relapse fear to anchoring new beliefs."
                },
                {
                    "id": "lesson-8-v1",
                    "title": "Execution Engine",
                    "focus": "Momentum",
                    "order": 8,
                    "transformation": "From stalled motivation to consistent, value-aligned action."
                },
                {
                    "id": "lesson-9-v1",
                    "title": "Growth Anchor",
                    "focus": "Perseverance",
                    "order": 9,
                    "transformation": "From isolated progress to embedded, resilient growth."
                }
            ]
        }
    ]
}

# Lesson 3 Pedagogical Framework (from ias-curriculum-full.json)
LESSON_3_PEDAGOGICAL = {
    "steps": [
        {
            "id": "step-3-1",
            "name": "Spot the Story",
            "order": 1,
            "instruction": "Identify the narrative your brain is trying to prove right now.",
            "tagline": "Observe the prediction. Don't collapse your life.",
            "obstacle": {
                "id": "obstacle-step-3-1",
                "false_belief": "If I see the real story, I'll have to admit I've been wrong about everything—and that will unravel my entire identity.",
                "what_they_dread": [
                    "Exposing themselves as a fraud or failure",
                    "Dismantling the competence they've built and starting over",
                    "Having to blow up their life (quit the job, leave the relationship)",
                    "Confirming their worst fear: 'I've wasted years building the wrong life.'"
                ],
                "truth_they_dont_know": "Spotting the story doesn't mean you were wrong—it means you were loyal to old data. The story was adaptive once; now it's just outdated."
            },
            "false_actions": [
                "Confess to everyone that they've been 'faking it'",
                "Quit their job or relationship",
                "Relive every moment they 'got it wrong'",
                "Justify or defend the old story",
                "Generate a perfect replacement narrative in the same breath"
            ],
            "true_action": {
                "action": "Simply observe",
                "description": "My brain has been running this prediction. Here's the evidence it's been collecting. Now I see it. No confession. No collapse. Just clarity."
            }
        },
        {
            "id": "step-3-2",
            "name": "Name the Feeling",
            "order": 2,
            "instruction": "Label the emotion fueling the spiral: shame, fear, guilt, or inadequacy.",
            "tagline": "Name it. Don't become it.",
            "obstacle": {
                "id": "obstacle-step-3-2",
                "false_belief": "If I name the feeling, it will consume me. I'll fall apart, lose control, or prove I'm as weak as I've always feared.",
                "what_they_dread": [
                    "That naming shame or fear means becoming it—that acknowledgment = surrender",
                    "That if they let themselves feel inadequacy or guilt fully, the emotion will be bottomless",
                    "That naming it out loud (even to themselves) makes it 'real' in a way that can't be undone",
                    "That emotions are proof of weakness, and naming them confirms they don't belong",
                    "That once they start feeling, the floodgates open and they lose composure"
                ],
                "truth_they_dont_know": "Naming the feeling de-fuses you from it. It moves the emotion from 'I AM ashamed' to 'Shame is present.' That shift alone reduces the hijack by 40–60%."
            },
            "false_actions": [
                "Sit with the feeling for hours in painful excavation",
                "Cry or 'release' it in some performative cathartic way",
                "Trace it back to childhood wounds",
                "Justify why they feel this way",
                "Fix or eliminate the feeling immediately"
            ],
            "true_action": {
                "action": "Label it in one sentence",
                "description": "The feeling fueling this loop right now is [shame / fear / inadequacy / guilt]. That's it. Label it. Move on."
            }
        },
        {
            "id": "step-3-3",
            "name": "Reveal the Prediction",
            "order": 3,
            "instruction": "Uncover what outcome the replay is trying to protect you from.",
            "tagline": "See the prediction. Test it against reality.",
            "obstacle": {
                "id": "obstacle-step-3-3",
                "false_belief": "If I uncover what I'm really afraid of, I'll have to face that it's true—and I won't be able to handle it.",
                "what_they_dread": [
                    "That the prediction their brain is making is accurate—and if they see it clearly, they'll have to accept it as inevitable",
                    "If I admit I'm afraid of being rejected, it's because I'm actually unlovable",
                    "If I admit I'm afraid of failing, it's because I don't actually have what it takes",
                    "That revealing the prediction means admitting the fear is rational, not paranoid",
                    "That once they see what the replay is protecting them from, they'll realize how fragile their entire life structure is",
                    "That the prediction will sound so 'small' or 'stupid' that they'll be embarrassed",
                    "That revealing it = having to immediately fix it or disprove it, which feels impossible"
                ],
                "truth_they_dont_know": "The prediction is your nervous system's best guess based on old data—it's not a prophecy. Seeing it clearly doesn't make it true; it makes it testable."
            },
            "false_actions": [
                "Prove the prediction wrong immediately",
                "Go back and analyze every past instance where the fear 'came true'",
                "Defend themselves against the prediction",
                "Build an airtight case for why the fear is irrational",
                "Eliminate the fear before moving forward"
            ],
            "true_action": {
                "action": "Complete this sentence",
                "description": "The outcome this replay is trying to protect me from is: [losing respect / being exposed as incompetent / being abandoned / failing publicly / etc.]."
            }
        }
    ]
}


def send_webhook(operation: str, data: dict):
    """Send operation to n8n webhook with HMAC signature."""
    payload = {"operation": operation, "data": data}
    body = json.dumps(payload)

    # Generate HMAC signature
    if HMAC_SECRET:
        signature = "sha256=" + hmac.new(
            HMAC_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    else:
        print("⚠️  WARNING: No HMAC_SECRET set, using mock signature")
        signature = "sha256=mock"

    headers = {
        "Content-Type": "application/json",
        "X-Dionysus-Signature": signature,
        "X-Timestamp": datetime.utcnow().isoformat()
    }

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            data=body,
            headers=headers,
            verify=False,
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ {operation}: {result.get('node_id', 'success')}")
            return result
        else:
            print(f"❌ {operation} failed ({response.status_code}): {response.text[:200]}")
            return None

    except Exception as e:
        print(f"❌ {operation} error: {e}")
        return None


def populate_curriculum():
    """Populate full IAS curriculum via n8n webhook."""
    print("=" * 70)
    print("IAS Unified Curriculum Population")
    print("=" * 70)
    print()

    # 1. Create curriculum root
    print("📚 Creating curriculum root...")
    send_webhook("upsert_curriculum", {
        "id": CURRICULUM_SCHEMA["id"],
        "title": CURRICULUM_SCHEMA["title"],
        "description": CURRICULUM_SCHEMA["description"],
        "target_audience": CURRICULUM_SCHEMA["target_audience"],
        "total_modules": CURRICULUM_SCHEMA["total_modules"],
        "total_lessons": CURRICULUM_SCHEMA["total_lessons"]
    })

    # 2. Create modules (phases) and lessons
    for phase in CURRICULUM_SCHEMA["phases"]:
        module_id = f"module-{phase['id']}"

        print(f"\n📖 Creating {phase['title']} module...")
        send_webhook("upsert_module", {
            "parent_id": CURRICULUM_SCHEMA["id"],
            "id": module_id,
            "title": f"{phase['title']}: {phase['theme']}",
            "phase": phase['title'],
            "order": phase['order'],
            "promise": phase['promise'],
            "goal": phase['goal']
        })

        # 3. Create lessons within module
        for lesson in phase["lessons"]:
            print(f"  📝 Creating {lesson['title']}...")
            send_webhook("upsert_lesson", {
                "parent_id": module_id,
                "id": lesson['id'],
                "title": lesson['title'],
                "order": lesson['order'],
                "focus": lesson['focus'],
                "transformation": lesson['transformation'],
                "has_pedagogical_framework": lesson.get('has_pedagogical_framework', False)
            })

    # 4. Add Lesson 3 pedagogical framework
    print("\n🎯 Adding Lesson 3 pedagogical framework...")
    for step_data in LESSON_3_PEDAGOGICAL["steps"]:
        print(f"  🔹 Step {step_data['order']}: {step_data['name']}")

        # Create step
        send_webhook("upsert_step", {
            "parent_id": "lesson-3-v1",
            "id": step_data['id'],
            "name": step_data['name'],
            "order": step_data['order'],
            "instruction": step_data['instruction'],
            "tagline": step_data['tagline']
        })

        # Create obstacle
        obstacle = step_data['obstacle']
        send_webhook("upsert_obstacle", {
            "parent_id": step_data['id'],
            "id": obstacle['id'],
            "false_belief": obstacle['false_belief'],
            "what_they_dread": obstacle['what_they_dread'],
            "truth_they_dont_know": obstacle['truth_they_dont_know']
        })

        # Create true action
        true_action = step_data['true_action']
        send_webhook("upsert_true_action", {
            "parent_id": step_data['id'],
            "id": f"true-action-{step_data['id']}",
            "action": true_action['action'],
            "description": true_action['description']
        })

        # Create false actions
        for i, false_action in enumerate(step_data['false_actions'], 1):
            send_webhook("upsert_false_action", {
                "parent_id": step_data['id'],
                "id": f"false-action-{step_data['id']}-{i}",
                "action": false_action,
                "order": i,
                "why_unnecessary": "Not required for step completion"
            })

    # 5. Link source documents
    print("\n📄 Linking source documents...")
    source_docs = [
        {
            "id": "source-avatar-sot",
            "title": "Analytical Empath Avatar Source of Truth",
            "file_path": f"{PROJECT_ROOT}/data/ground-truth/analytical-empath-avatar-source-of-truth.md",
            "doc_type": "avatar"
        },
        {
            "id": "source-product-arch",
            "title": "97 Product Architecture",
            "file_path": f"{PROJECT_ROOT}/data/ground-truth/97-product-architecture.md",
            "doc_type": "product"
        },
        {
            "id": "source-replay-loop",
            "title": "Replay Loop Concept",
            "file_path": f"{PROJECT_ROOT}/docs/concepts/Replay Loop.md",
            "doc_type": "concept"
        }
    ]

    for doc in source_docs:
        send_webhook("link_source_document", {
            "parent_id": CURRICULUM_SCHEMA["id"],
            "id": doc['id'],
            "title": doc['title'],
            "file_path": doc['file_path'],
            "doc_type": doc['doc_type']
        })

    print("\n" + "=" * 70)
    print("✅ Unified IAS Curriculum Population Complete!")
    print("=" * 70)
    print("\n📊 Summary:")
    print(f"  - Curriculum: {CURRICULUM_SCHEMA['title']}")
    print(f"  - Modules: {CURRICULUM_SCHEMA['total_modules']}")
    print(f"  - Lessons: {CURRICULUM_SCHEMA['total_lessons']}")
    print(f"  - Lesson 3 Steps: {len(LESSON_3_PEDAGOGICAL['steps'])}")
    print(f"  - Source Documents: {len(source_docs)}")
    print("\n⚠️  Remember: ALL Neo4j access MUST use n8n webhooks!")


if __name__ == "__main__":
    populate_curriculum()
