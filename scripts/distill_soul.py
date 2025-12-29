import asyncio
import os
import json
import logging
import re
from pathlib import Path
import sys
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.wisdom_service import get_wisdom_service
from api.models.wisdom import WisdomUnit, MentalModel, StrategicPrinciple, CaseStudy, WisdomType
from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger("dionysus.distill_soul")

DISTILLED_FILE = "wisdom_distilled.json"

def repair_json(text):
    """Robust JSON cleaning for LLM outputs."""
    try:
        text = text.strip()
        # 1. Basic markdown removal
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # 2. Extract JSON part if mixed with text
        if not (text.startswith("[") or text.startswith("{")):
            start_bracket = text.find("[")
            start_brace = text.find("{")
            start = min(start_bracket, start_brace) if (start_bracket != -1 and start_brace != -1) else max(start_bracket, start_brace)
            end_bracket = text.rfind("]")
            end_brace = text.rfind("}")
            end = max(end_bracket, end_brace)
            if start != -1 and end != -1:
                text = text[start:end+1]
        
        # 3. Simple replace for single quotes around keys/values
        text = re.sub(r"([{,[\]\s*)\'([^\']*)\'", r"\1\"\2\"", text)
        text = re.sub(r"(: \s*)\'([^\']*)\'", r"\1\"\2\"", text)
        
        # 4. Handle trailing commas
        text = re.sub(r",\s*([\}\]])", r"\1", text)
        
        return text
    except Exception:
        return text

async def distill_batch_direct(batch, batch_idx, total_batches):
    """Distill using direct chat_completion for maximum reliability and speed."""
    print(f"Distilling batch {batch_idx+1}/{total_batches} (GPT-5 Nano)...")
    
    system_prompt = "You are a master of conceptual synthesis. Merge fragmented insights into ONE high-fidelity JSON list of Wisdom Units."
    user_content = f"""
    Merge these {len(batch)} insight fragments into a canonical JSON list.
    
    FRAGMENTS:
    {json.dumps(batch, indent=2)}
    
    JSON SCHEMA FOR EACH OBJECT:
    {{
        "type": "mental_model" or "strategic_principle",
        "name": "Canonical Name",
        "summary": "Detailed, high-fidelity description",
        "provenance_chain": ["list", "of", "session_ids"],
        "core_logic": "Optional for mental_model",
        "rationale": "Optional for strategic_principle"
    }}
    
    Respond with ONLY the JSON list.
    """
    
    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": user_content}],
            system_prompt=system_prompt,
            model=GPT5_NANO,
            max_tokens=2048
        )
        
        content = repair_json(response)
        data = json.loads(content)
        
        batch_units = []
        if isinstance(data, list):
            for d in data:
                w_type = str(d.get("type", "strategic_principle")).lower()
                d["wisdom_id"] = f"distilled-{uuid4().hex[:8]}"
                # Ensure fields match Pydantic model
                if "mental" in w_type:
                    d["type"] = WisdomType.MENTAL_MODEL
                    batch_units.append(MentalModel(**d))
                else:
                    d["type"] = WisdomType.STRATEGIC_PRINCIPLE
                    batch_units.append(StrategicPrinciple(**d))
        return batch_units
    except Exception as e:
        print(f"Failed to distill batch {batch_idx+1}: {e}")
        return []

async def main():
    # Force local tunnel URLs for Darwin
    os.environ["N8N_CYPHER_URL"] = "http://localhost:5678/webhook/neo4j/v1/cypher"
    os.environ["N8N_WEBHOOK_URL"] = "http://localhost:5678/webhook/memory/v1/ingest/message"
    
    service = get_wisdom_service()
    raw_data = service.load_raw_extracts("wisdom_extraction_raw.json")
    
    if not raw_data:
        print("No raw data found to distill.")
        return

    print(f"Loaded {len(raw_data)} raw session extracts.")
    
    all_insights = []
    for entry in raw_data:
        insights = entry.get("wisdom_insights", [])
        session_id = entry.get("session_id", "unknown")
        
        if isinstance(insights, list):
            for i in insights:
                if isinstance(i, dict):
                    i["session_id"] = session_id
                    all_insights.append(i)
                elif isinstance(i, str):
                    all_insights.append({"summary": i, "session_id": session_id})
        elif isinstance(insights, dict):
            for k, v in insights.items():
                if isinstance(v, list):
                    for val in v:
                        if isinstance(val, dict):
                            val["session_id"] = session_id
                            all_insights.append(val)
                        else:
                            all_insights.append({"summary": str(val), "session_id": session_id})
                else:
                    all_insights.append({"summary": str(v), "session_id": session_id})

    print(f"Extracted {len(all_insights)} insight fragments.")

    batch_size = 15 
    batches = [all_insights[i:i + batch_size] for i in range(0, len(all_insights), batch_size)]
    
    print(f"Processing {len(batches)} batches in parallel...")
    tasks = [distill_batch_direct(b, i, len(batches)) for i, b in enumerate(batches)]
    all_results = await asyncio.gather(*tasks)
    
    all_distilled = []
    for res in all_results:
        all_distilled.extend(res)

    with open(DISTILLED_FILE, "w") as f:
        json.dump([u.model_dump(mode='json') for u in all_distilled], f, indent=2)

    print(f"Distillation complete. Created {len(all_distilled)} canonical units.")

    print("Persisting to Neo4j...")
    count = 0
    for unit in all_distilled:
        try:
            success = await service.persist_distilled_unit(unit)
            if success:
                count += 1
                if count % 10 == 0:
                    print(f"Progress: {count}/{len(all_distilled)} units persisted.")
        except Exception as e:
            print(f"Error persisting {unit.name}: {e}")

    print(f"\n✅ System Soul Distillation successful! Persisted {count} units to Neo4j.")

if __name__ == "__main__":
    asyncio.run(main())