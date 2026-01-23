
import json
import hmac
import hashlib
import os
import urllib.request
import urllib.error
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

HMAC_SECRET = load_env_secret()
print(f"Using Secret Config: {HMAC_SECRET[:4]}...{HMAC_SECRET[-4:]}")

DEPRECATION_MESSAGE = (
    "Deprecated: this script sends pre-extracted entities/edges and is blocked by the API. "
    "Use scripts/ingest_vigilant_sentinel_experiential.py instead."
)

# --- Data Generation ---

def get_avatar_core():
    return {
        "name": "The Vigilant Sentinel",
        "type": "AvatarArchetype",
        "description": "High-functioning adults with ADHD, gifted/twice-exceptional minds. Hyper-analytical, emotionally hypersensitive. 'Hunters' trapped in a 'Farmer's world'."
    }

def get_psychographic_landscape():
    entities = []
    edges = []
    
    # 1.1 The Defining Paradox
    paradox = {
        "name": "Twice-Exceptional Paradox", 
        "type": "NeurologicalCondition", 
        "description": "Gifted-level intelligence juxtaposed against executive dysfunction (ADHD). The 'Intelligence-Performance Gap'."
    }
    entities.append(paradox)
    
    edges.append({
        "source": "The Vigilant Sentinel", "target": "Twice-Exceptional Paradox", "relation": "EMBODIES",
        "evidence": "I feel like I constantly underperform and my life is kind of a mess... how can my brain be capable of so much and still forget to eat or do laundry?"
    })

    # Metaphor: Ferrari with Bicycle Brakes
    metaphor = {
        "name": "Ferrari with Bicycle Brakes",
        "type": "Metaphor",
        "description": "High-performance neurological engine (rapid processing) with underdeveloped executive function (brakes/steering)."
    }
    entities.append(metaphor)
    edges.append({
        "source": "The Vigilant Sentinel", "target": "Ferrari with Bicycle Brakes", "relation": "RESONATES_WITH",
        "evidence": "I feel like a Ferrari engine with bicycle brakes. I'm revving so high but going nowhere, and I smell burning rubber."
    })

    # The Secret Flailer
    flailer = {
        "name": "The Secret Flailer",
        "type": "IdentityState",
        "description": "Successful on paper (The Swan Effect), but privately drowning in administrative backlog and sensory exhaustion."
    }
    entities.append(flailer)
    edges.append({
        "source": "The Vigilant Sentinel", "target": "The Secret Flailer", "relation": "MASKS_AS",
        "evidence": "I feel like I'm not using my intelligence in a positive way... I feel like everything I do is not enough, never enough."
    })

    return entities, edges

def get_neurological_mechanisms():
    entities = []
    edges = []

    # 1.3 IBNS
    ibns = {
        "name": "Interest-Based Nervous System",
        "type": "NeurologicalMechanism",
        "description": "Motivated exclusively by Interest, Novelty, Challenge, and Urgency. Not Importance."
    }
    entities.append(ibns)
    edges.append({
        "source": "The Vigilant Sentinel", "target": "Interest-Based Nervous System", "relation": "OPERATES_ON",
        "evidence": "Your problem isn't that you can't focus; it's that your focus runs on a different fuel source (Interest) than the rest of the world (Importance)."
    })

    # Drivers of IBNS
    drivers = ["Interest", "Novelty", "Challenge", "Urgency"]
    for d in drivers:
        ent = {"name": f"Driver: {d}", "type": "MotivationFactor", "description": f"Core fuel for IBNS: {d}"}
        entities.append(ent)
        edges.append({"source": "Interest-Based Nervous System", "target": f"Driver: {d}", "relation": "POWERED_BY"})

    # Empathy Overdrive
    mirror = {
        "name": "Mirror Neuron Overdrive",
        "type": "NeurologicalMechanism",
        "description": "Physiological state of high permeability. Affective Empathy overload."
    }
    entities.append(mirror)
    edges.append({
        "source": "The Vigilant Sentinel", "target": "Mirror Neuron Overdrive", "relation": "POSSESSES",
        "evidence": "I don't just 'have' empathy. I am the room's emotional thermostat. If you're cold, I'm freezing."
    })

    return entities, edges

def get_pain_points_deep():
    entities = []
    edges = []

    pains = [
        {
            "name": "Rejection Sensitive Dysphoria",
            "type": "PainPoint",
            "desc": "Extreme emotional sensitivity to perceived rejection. Physical pain.",
            "quote": "It's like someone is stabbing me in the chest with a white hot iron... Rejection makes me feel like I'm a kid who lost his parents in the mall."
        },
        {
            "name": "Executive Paralysis",
            "type": "PainPoint",
            "desc": "Intention Deficit. Knowing what to do but being chemically unable to start.",
            "quote": "It's not that I won't do it, it's that I can't make my body move. It's like I'm screaming inside my own head."
        },
        {
            "name": "The Too Much Wound",
            "type": "Trauma",
            "desc": "Lifelong belief of being too loud, too sensitive, too intense.",
            "quote": "I'm always 'too much' for everyone. Too loud, too intense, too needy. I just want someone who doesn't need me to shrink."
        },
        {
            "name": "Existential Boredom",
            "type": "PainPoint",
            "desc": "Chronic, painful boredom when novelty fades. Existential crisis.",
            "quote": "I seem to find people interesting at first but after some dates... I get bored."
        }
    ]

    for p in pains:
        entities.append({"name": p["name"], "type": p["type"], "description": p["desc"]})
        edges.append({
            "source": "The Vigilant Sentinel", "target": p["name"], "relation": "EXPERIENCES_PAIN",
            "evidence": p["quote"],
            "confidence": 0.95
        })

    return entities, edges

def get_narratives_and_conspiracies():
    entities = []
    edges = []

    narratives = [
        {
            "name": "Prussian Education Conspiracy",
            "type": "CorruptionNarrative",
            "desc": "Belief that school was designed to create obedient workers and crush 'Hunter' traits.",
            "quote": "I didn't fail school; school failed me. It taught me to be a worker bee, and I'm a wasp."
        },
        {
            "name": "Big Pharma skepticism",
            "type": "CorruptionNarrative",
            "desc": "Belief that ADHD is a personality variant pathologized by capitalism to sell cures.",
            "quote": "They invented a disease to sell a cure."
        },
        {
            "name": "Attention Economy Prevention",
            "type": "CorruptionNarrative",
            "desc": "Belief that algorithms hijack their executive function.",
            "quote": "Social media companies have weaponized behavioral psychology to hijack my dopamine."
        }
    ]

    for n in narratives:
        entities.append({"name": n["name"], "type": n["type"], "description": n["desc"]})
        edges.append({
            "source": "The Vigilant Sentinel", "target": n["name"], "relation": "SUBSCRIBES_TO",
            "evidence": n["quote"]
        })

    return entities, edges

def get_archetypes():
    entities = []
    edges = []

    archetypes = [
        {
            "name": "Hunter vs Farmer",
            "desc": "ADHD traits were evolutionary adaptations for Hunters (scanning, hyperfocus).",
            "quote": "I am a Hunter in a Farmer's world."
        },
        {
            "name": "The Shamanic Archetype",
            "desc": "Neurodivergent individuals as Village Seers or Watchmen.",
            "quote": "In a tribal society, I would be the shaman."
        },
        {
            "name": "Orchid vs Dandelion",
            "desc": "Highly sensitive to environment (Orchid) vs resilient (Dandelion).",
            "quote": "In the right greenhouse, I produce flowers of exceptional beauty."
        }
    ]

    for a in archetypes:
        entities.append({"name": a["name"], "type": "HistoricalArchetype", "description": a["desc"]})
        edges.append({
            "source": "The Vigilant Sentinel", "target": a["name"], "relation": "IDENTIFIES_WITH",
            "evidence": a["quote"]
        })

    return entities, edges

def get_failed_solutions():
    entities = []
    edges = []
    
    solutions = [
        ("CBT", "Cognitive Behavioral Therapy", "It feels like gaslighting to someone whose nervous system is signaling a genuine threat."),
        ("Hustle Culture", "Napoleon Hill / Dale Carnegie", "Feels manipulative and fake. Rejects 'Just believe harder'."),
        ("Linear Productivity", "GTD / Time Blocking", "Stop telling me to make a list. If a list could save me, I would be the king of the world by now.")
    ]
    
    for name, full, quote in solutions:
        entities.append({"name": f"Failed: {name}", "type": "FailedSolution", "description": full})
        edges.append({
            "source": "The Vigilant Sentinel", "target": f"Failed: {name}", "relation": "REJECTS_SOLUTION",
            "evidence": quote
        })

    return entities, edges

def create_payload():
    entities = [get_avatar_core()]
    all_edges = []
    
    generators = [
        get_psychographic_landscape, 
        get_neurological_mechanisms, 
        get_pain_points_deep,
        get_narratives_and_conspiracies,
        get_archetypes,
        get_failed_solutions
    ]
    
    for gen in generators:
        ents, edges = gen()
        entities.extend(ents)
        all_edges.extend(edges)
    
    trajectory = {
        "query": "Ingest Vigilant Sentinel Deep Dossier (Avatar 2.0)",
        "summary": "Deep enrichment of avatar profile with extensive psychographic data, corruption narratives, and verbatim quotes.",
        "steps": [
            {
                "observation": "Parsed comprehensive psychographic dossier",
                "action": "Mapped to Graphiti entities (Archetypes, Narratives, Mechanisms)",
                "thought": "Preserved 'Voice of Customer' quotes in edge evidence for high-fidelity recall."
            }
        ],
        "metadata": {
            "project_id": "dionysus_core",
            "session_id": "avatar_deep_enrichment",
            "timestamp": datetime.utcnow().isoformat(),
            "tags": ["avatar", "deep_dive", "psychometrics", "vigilant_sentinel_v2"],
            "trajectory_type": "structural"
        }
    }
    
    payload = {
        "trajectory": trajectory,
        "entities": entities,
        "edges": all_edges,
        "project_id": "dionysus_core",
        "session_id": "avatar_deep_enrichment",
        "memory_type": "semantic"
    }
    return payload

# --- Execution ---

def generate_signature(payload_bytes: bytes, secret: str) -> str:
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"

def main():
    raise SystemExit(DEPRECATION_MESSAGE)
    print("Preparing Deep Dossier payload (Avatar 2.0)...")
    data = create_payload()
    json_data = json.dumps(data)
    payload_bytes = json_data.encode("utf-8")
    
    print(f"Payload Size: {len(payload_bytes)} bytes")
    print(f"Entities: {len(data['entities'])}")
    print(f"Edges: {len(data['edges'])}")
    
    print("Signing request...")
    signature = generate_signature(payload_bytes, HMAC_SECRET)
    
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
        print("Ensure dionysus-api is running on remote VPS.")

if __name__ == "__main__":
    main()
