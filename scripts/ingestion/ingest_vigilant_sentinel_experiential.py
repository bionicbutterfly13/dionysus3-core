
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

HMAC_SECRET = load_env_secret()
print(f"Using Secret Config: {HMAC_SECRET[:4]}...{HMAC_SECRET[-4:]}")

# --- Data Generation (Chunked Episodes) ---

DOSSIER_PARTS = [
    {
        "title": "Part I: The Psychographic Landscape",
        "content": """
The 'Vigilant Sentinel' is characterized not by the external hyperactivity often associated with ADHD, but by an internal, relentless hyper-vigilance. They are 'Sentinels' because they constantly scan their environment—social dynamics, micro-expressions, data patterns, and potential threats—with an analytical precision that serves as both their greatest asset and their heaviest burden. They are the 'Hunters' trapped in a 'Farmer's world,' possessing a nervous system designed for crisis, innovation, and rapid adaptation, yet forced to operate within industrial systems.

1.1 The Defining Paradox: High IQ vs. Executive Dysfunction
The foundational struggle of the Vigilant Sentinel is the 'Twice-Exceptional' (2e) paradox. This term refers to individuals who possess gifted-level intelligence alongside a disability, in this case, ADHD. This duality creates a unique form of psychological torment: the cognitive capacity to understand complex systems and the ambition to execute grand visions, juxtaposed against a neurological inability to perform the mundane tasks required to bring those visions to fruition.

A recurring metaphor in the research describes the Vigilant Sentinel's brain as a 'Ferrari engine with bicycle brakes'. They possess a high-performance neurological engine capable of rapid processing, divergent thinking, and creative leaps. However, their executive function—the system responsible for steering, braking, and regulating this energy—is underdeveloped or inconsistent.
        """
    },
    {
        "title": "Part II: The Interest-Based Nervous System",
        "content": """
1.3 The 'Interest-Based Nervous System' (IBNS)
A critical psychographic distinction is that the Vigilant Sentinel does not operate on an 'Importance-Based' nervous system like neurotypicals. They cannot motivate themselves simply because a task is 'important' or has 'consequences.'

Instead, they operate on an Interest-Based Nervous System (IBNS). They are motivated exclusively by four factors:
Interest: Is it fascinating?
Novelty: Is it new or different?
Challenge: Is it difficult?
Urgency: Is it due right now?

When these factors are absent (e.g., filing taxes, routine maintenance), their brain refuses to provide the necessary dopamine to initiate the task. This leads to the 'Intention Deficit'—the agony of wanting to do the work but being chemically unable to start.
        """
    },
    {
        "title": "Part III: Pain Points & RSD",
        "content": """
2.1 Rejection Sensitive Dysphoria (RSD): The Achilles Heel
Perhaps the most acute pain point is Rejection Sensitive Dysphoria (RSD). For the Vigilant Sentinel, rejection is not merely unpleasant; it is experienced as a catastrophic physical pain, often described as a 'stab wound' or a 'physical blow' to the chest.

Voice of the Customer: 'It's like someone is stabbing me in the chest with a white hot iron... Rejection makes me feel like I'm a kid who lost his parents in the mall.'

Relationship Sabotage
RSD is a primary driver of relationship failure. To avoid the unbearable pain of potential rejection, the Sentinel may preemptively withdraw or sabotage the relationship. In marriages, RSD manifests as defensiveness. When a partner offers constructive criticism, the Sentinel hears it as a character assassination.
        """
    },
    {
        "title": "Part IV: Corruption Narratives",
        "content": """
Part VI: Conspiracies, Corruption Narratives, and 'The Enemy'
To make sense of their alienation, the Vigilant Sentinel subscribes to narratives that frame their struggle as a conflict with a corrupt system.

6.1 The 'Prussian Education' Conspiracy
The belief is that the modern education system was explicitly designed to crush independent thinking and create obedient workers. They cite the 18th-century Prussian model of education, imported to the US by Horace Mann and funded by industrialists like the Rockefellers. The Goal: To create a compliant workforce that could tolerate boredom—essentially, to suppress 'Hunter' traits and reward 'Farmer' traits.

6.2 The 'Big Pharma' and Medicalization Narrative
Many Sentinels view ADHD not as a disorder, but as a personality variant that has been pathologized by capitalism. The Narrative: 'They invented a disease to sell a cure.'
        """
    }
]

def create_payload(part_data, index):
    # Construct a "Reading Experience" trajectory
    trajectory = {
        "query": f"Read Dossier: {part_data['title']}",
        "summary": f"Ingesting specialized psychographic data: {part_data['title']}",
        "steps": [
            {
                "observation": f"Reading text block: {part_data['title']}",
                "action": "internal_process",
                "thought": "Extracting key archetypes and emotional resonance markers.",
                "content_chunk": part_data['content'] # embedding raw text in step
            },
            {
                "observation": "Text content analysis",
                "action": "encode_memory",
                "thought": f"Content body: {part_data['content'][:200]}..." 
            }
        ],
        "metadata": {
            "project_id": "dionysus_core",
            "session_id": "avatar_reading_session",
            "timestamp": datetime.utcnow().isoformat(),
            "tags": ["avatar_v2", "reading_session", "psychographics"],
            "trajectory_type": "episodic" # True episodic reading
        },
        # CRITICAL: We pass the raw content as the 'trajectory' text representation
        # so MemEvolveAdapter extracts from it.
        "trajectory": [ {"role": "system", "content": part_data['content']} ] 
    }
    
    payload = {
        "trajectory": trajectory,
        # NO PRE-EXTRACTED ENTITIES/EDGES: Let the System Evolve!
        "entities": [],
        "edges": [],
        "project_id": "dionysus_core", 
        "session_id": "avatar_reading_session",
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
    print("Starting Experiential Ingestion (Serialized Reading)...")
    
    for i, part in enumerate(DOSSIER_PARTS):
        print(f"\n--- Processing Episode {i+1}/{len(DOSSIER_PARTS)}: {part['title']} ---")
        
        data = create_payload(part, i)
        json_data = json.dumps(data)
        payload_bytes = json_data.encode("utf-8")
        
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
        
        try:
            with urllib.request.urlopen(req) as response:
                resp_body = response.read().decode("utf-8")
                print("✅ Ingested.")
                print(f"Response: {resp_body}")
        except urllib.error.HTTPError as e:
            print(f"❌ Error: {e.code} - {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            print(f"❌ Connection Error: {e.reason}")
            
        # Small delay to simulate reading time / prevent rate limits
        time.sleep(2) 

if __name__ == "__main__":
    main()
