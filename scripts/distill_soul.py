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
from api.agents.knowledge.wisdom_distiller import WisdomDistiller
from api.models.wisdom import WisdomUnit, MentalModel, StrategicPrinciple, CaseStudy, WisdomType

logger = logging.getLogger("dionysus.distill_soul")

def repair_json(text):
    """Robust JSON cleaning for LLM outputs."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    # Replace single quotes with double quotes around keys and strings
    text = re.sub(r"(['])(?=\s*[a-zA-Z0-9_]+\s*[']\s*:)", '"', text)
    text = re.sub(r'(:\s*)(["])', r'\1"', text)
    text = re.sub(r"(['])(\s*[,}\]])", r'"\2', text)
    text = re.sub(r"([{\[, ]\s*)(['])", r'\1"', text)
    
    # Handle trailing commas
    text = re.sub(r',\s*([\}\]])', r'\1', text)
    
    return text

async def distill_batch(distiller, batch, batch_idx, total_batches):
    """Worker function for parallel batch distillation."""
    print(f"Distilling batch {batch_idx+1}/{total_batches}...")
    prompt = f"""
    Synthesize the following {len(batch)} fragments into canonical Wisdom Units.
    FRAGMENTS:
    {json.dumps(batch, indent=2)}
    
    CRITICAL: Your final answer MUST be a valid JSON list of objects.
    Each object MUST have:
    - "type": "mental_model" or "strategic_principle"
    - "name": "A concise name"
    - "summary": "A high-fidelity canonical description"
    - "provenance_chain": ["list", "of", "session_ids"]
    
    Respond with ONLY the JSON list.
    """
    try:
        # Use to_thread because distiller.agent.run is sync
        result = await asyncio.to_thread(distiller.run, prompt)
        
        content = repair_json(str(result))
        data = json.loads(content)
        
        batch_units = []
        if isinstance(data, list):
            for d in data:
                w_type = d.get("type", "strategic_principle")
                d["wisdom_id"] = f"distilled-{uuid4().hex[:8]}"
                # Map internal names to model names
                if w_type == "mental_model":
                    batch_units.append(MentalModel(**d))
                else:
                    batch_units.append(StrategicPrinciple(**d))
        return batch_units
    except Exception as e:
        print(f"Failed to distill batch {batch_idx+1}: {e}")
        return []

async def main():
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
        elif isinstance(insights, dict):
            for k, v in insights.items():
                if isinstance(v, list):
                    for i in v:
                        if isinstance(i, str):
                            all_insights.append({"content": i, "session_id": session_id})
                        elif isinstance(i, dict):
                            i["session_id"] = session_id
                            all_insights.append(i)

    print(f"Extracted {len(all_insights)} atomic insight fragments.")

    distiller = WisdomDistiller()
    
    batch_size = 10
    batches = [all_insights[i:i + batch_size] for i in range(0, len(all_insights), batch_size)]
    
    # Process batches in parallel chunks
    CONCURRENCY = 3 
    all_distilled = []
    
    with distiller:
        for i in range(0, len(batches), CONCURRENCY):
            chunk = batches[i : i + CONCURRENCY]
            tasks = [distill_batch(distiller, b, i + j, len(batches)) for j, b in enumerate(chunk)]
            chunk_results = await asyncio.gather(*tasks)
            for res in chunk_results:
                all_distilled.extend(res)

    print(f"Distillation complete. Created {len(all_distilled)} canonical units.")

    # 3. Persist to Neo4j
    count = 0
    for unit in all_distilled:
        success = await service.persist_distilled_unit(unit)
        if success:
            count += 1
            print(f"Persisted [{count}/{len(all_distilled)}]: {unit.name}")

    print(f"\n✅ System Soul Distillation successful! Persisted {count} units.")

if __name__ == "__main__":
    asyncio.run(main())