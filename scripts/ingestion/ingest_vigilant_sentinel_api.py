
import json
import hmac
import hashlib
import os
import urllib.request
import urllib.error
import time
from datetime import datetime

# --- Configuration ---
API_BASE_URL = "http://72.61.78.89:8000"
INGEST_ENDPOINT = "/webhook/memevolve/v1/ingest"

# Load secret from environment (required)
def load_env_secret():
    secret = os.environ.get("MEMEVOLVE_HMAC_SECRET")
    if not secret:
        raise RuntimeError("MEMEVOLVE_HMAC_SECRET must be set for ingestion.")
    return secret

DEPRECATION_MESSAGE = (
    "Deprecated: this script sends pre-extracted entities/edges and is blocked by the API. "
    "Use scripts/ingest_vigilant_sentinel_experiential.py instead."
)

# --- Data Generators (Pure Python Dicts) ---

def create_vigilant_sentinel_data():
    profile_name = "The Vigilant Sentinel"
    profile_desc = "High-functioning adults with ADHD, gifted/twice-exceptional minds. Hyper-analytical, emotionally hypersensitive."
    
    # ENTITIES
    entities = []
    
    # Main Avatar
    entities.append({
        "name": profile_name,
        "type": "AvatarArchetype",
        "description": profile_desc
    })
    
    # Pain Points
    pain_points = [
        ("Pain: RSD", "Rejection Sensitive Dysphoria", 0.9, "Not just sensitive — it hurts in my nervous system."),
        ("Pain: Paralysis", "Executive Dysfunction/Task Paralysis", 0.9, "I know exactly what to do... I just can't make myself do it."),
        ("Pain: Hollow Success", "Hollow Success Paradox", 0.8, "External wins coupled with internal exhaustion."),
        ("Pain: Masking", "Masking and Burnout", 0.85, "Exhausting effort to appear normal.")
    ]
    for name, desc, intensity, quote in pain_points:
        entities.append({"name": name, "type": "PainPoint", "description": desc})

    # Beliefs
    beliefs = [
        ("Belief: Hunter/Farmer", "I'm a Hunter in a Farmer's world."),
        ("Belief: System Failure", "Conventional productivity systems crumble under executive dysfunction."),
        ("Belief: Broken Self", "I am broken because I can't do simple things.")
    ]
    for name, desc in beliefs:
        entities.append({"name": name, "type": "Belief", "description": desc})

    # Desires
    desires = [
        ("Desire: Psychological Traction", "Collapse inner-critic loops within minutes."),
        ("Desire: Stop Paralysis", "Escape neuro-emotional paralysis reliably.")
    ]
    for name, desc in desires:
        entities.append({"name": name, "type": "Desire", "description": desc})

    # Failed Solutions
    solutions = [
        ("Failed: Standard Planners", "Frames struggle as ignorance/laziness vs neurological.")
    ]
    for name, desc in solutions:
        entities.append({"name": name, "type": "FailedSolution", "description": desc})


    # RELATIONSHIPS
    relationships = []
    
    # Avatar -> Pain
    for name, _, intensity, quote in pain_points:
        relationships.append({
            "source": profile_name, "target": name, "relation": "EXPERIENCES_PAIN", 
            "evidence": quote, "confidence": intensity, "type": "EXPERIENCES_PAIN"
        })
    
    # Avatar -> Belief
    for name, desc in beliefs:
        relationships.append({
            "source": profile_name, "target": name, "relation": "HOLDS_BELIEF",
            "evidence": desc, "confidence": 0.9, "type": "HOLDS_BELIEF"
        })

    # Avatar -> Desire
    for name, desc in desires:
        relationships.append({
            "source": profile_name, "target": name, "relation": "DESIRES",
            "evidence": desc, "confidence": 1.0, "type": "DESIRES"
        })

    # Avatar -> Failed Solution
    for name, desc in solutions:
        relationships.append({
            "source": profile_name, "target": name, "relation": "REJECTS_SOLUTION",
            "evidence": desc, "confidence": 0.9, "type": "REJECTS_SOLUTION"
        })

    return entities, relationships

def create_payload():
    entities, edges = create_vigilant_sentinel_data()
    
    trajectory = {
        "query": "Ingest Vigilant Sentinel Avatar Profile (API)",
        "summary": "Ingestion of the 'Vigilant Sentinel' avatar profile via API Gateway.",
        "steps": [
            {
                "observation": "Constructed AvatarProfile payload",
                "action": "POST to /webhook/memevolve/v1/ingest",
                "thought": "Ensuring structural integrity via Graphiti schema"
            }
        ],
        "metadata": {
            "project_id": "dionysus_core",
            "session_id": "avatar_ingest_api",
            "timestamp": datetime.utcnow().isoformat(),
            "tags": ["avatar", "marketing", "psychographics", "vigilant_sentinel", "api_ingest"],
            "trajectory_type": "structural"
        }
    }
    
    payload = {
        "trajectory": trajectory,
        "entities": entities,
        "edges": edges,
        "project_id": "dionysus_core",
        "session_id": "avatar_ingest_api",
        "memory_type": "semantic"
    }
    return payload

# --- Signing Logic ---

def generate_signature(payload_bytes: bytes, secret: str) -> str:
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"

# --- Execution ---

def main():
    raise SystemExit(DEPRECATION_MESSAGE)
    # Deprecated path retained for historical reference only.
    print("Preparing ingestion payload...")
    data = create_payload()
    json_data = json.dumps(data)
    payload_bytes = json_data.encode("utf-8")
    
    print("Signing request...")
    signature = generate_signature(payload_bytes, load_env_secret())
    
    url = f"{API_BASE_URL}{INGEST_ENDPOINT}"
    
    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature
        },
        method="POST"
    )
    
    print(f"Sending POST to {url}...")
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            print("\n✅ Success!")
            print(f"Status: {response.status}")
            print(f"Response: {resp_body}")
            
    except urllib.error.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.code}")
        print(e.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"\n❌ Connection Error: {e.reason}")
        print("Ensure dionysus-api is running on localhost:8000")

if __name__ == "__main__":
    main()
