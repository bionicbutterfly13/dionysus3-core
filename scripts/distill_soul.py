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
        
        # 2. Fix common LLM mistakes (single quotes around keys/values)
        text = re.sub(r"(?<=[\{\[,])\s*'([^']*)'\s*:", r'"\1":', text) # Keys
        text = re.sub(r":\s*'([^']*)'\s*(?=[,\}\]])", r': "\1"', text) # Values
        
        # 3. Handle trailing commas
        text = re.sub(r",\s*([\}\]])", r"\1", text)
        
        return text
    except Exception:
        return text

async def distill_batch(distiller, batch, batch_idx, total_batches):
    """Worker function for parallel batch distillation."""
    from api.agents.resource_gate import run_agent_with_timeout
    print(f"Distilling batch {batch_idx+1}/{total_batches}...")
    
    prompt = f"""
    You are a master of conceptual synthesis. Your goal is to merge these {len(batch)} insight fragments into canonical Wisdom Units. 
    
    FRAGMENTS:
    {json.dumps(batch, indent=2)}
    
    INSTRUCTIONS:
    1. Group similar ideas. 
    2. Synthesize them into canonical definitions.
    3. Output a valid JSON list.
    
    JSON SCHEMA FOR EACH OBJECT:
    {{
        "type": "mental_model" or "strategic_principle",
        "name": "Canonical Name",
        "summary": "Detailed, high-fidelity description",
        "provenance_chain": ["list", "of", "session_ids"]
    }}
    
    CRITICAL: Respond with ONLY the JSON list.
    """
    try:
        # Use centralized loop/resource management
        result = await run_agent_with_timeout(distiller.agent, prompt, timeout_seconds=120)
        
        content = repair_json(str(result))
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Aggressive fallback
            content = content.replace("'", '"')
            data = json.loads(content)
        
        batch_units = []
        if isinstance(data, list):
            for d in data:
                w_type = str(d.get("type", "strategic_principle")).lower()
                d["wisdom_id"] = f"distilled-{uuid4().hex[:8]}"
                
                if not d.get("name") or not d.get("summary"):
                    continue

                if "mental" in w_type:
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
            # Handle dictionary-style insights
            for k, v in insights.items():
                if isinstance(v, list):
                    for val in v:
                        if isinstance(val, str):
                            all_insights.append({"summary": val, "session_id": session_id})
                        elif isinstance(val, dict):
                            val["session_id"] = session_id
                            all_insights.append(val)
                elif isinstance(v, str):
                    all_insights.append({"summary": v, "session_id": session_id})

    print(f"Extracted {len(all_insights)} atomic insight fragments.")

    distiller = WisdomDistiller()
    
    batch_size = 8 # Slightly smaller batches for ToolCallingAgent stability
    batches = [all_insights[i:i + batch_size] for i in range(0, len(all_insights), batch_size)]
    
    # Process batches in parallel chunks
    CONCURRENCY = 3 # Conservative concurrency
    all_distilled = []
    
    # Clear existing distilled file to force fresh run
    if os.path.exists(DISTILLED_FILE):
        os.remove(DISTILLED_FILE)

    with distiller:
        for i in range(0, len(batches), CONCURRENCY):
            chunk = batches[i : i + CONCURRENCY]
            tasks = [distill_batch(distiller, b, i + j, len(batches)) for j, b in enumerate(chunk)]
            chunk_results = await asyncio.gather(*tasks)
            for res in chunk_results:
                all_distilled.extend(res)
            
            # Incremental save progress
            with open(DISTILLED_FILE, "w") as f:
                json.dump([u.model_dump(mode='json') for u in all_distilled], f, indent=2)

    print(f"Distillation stage complete. Total canonical units: {len(all_distilled)}")

    # 3. Persist to Neo4j
    count = 0
    # Point the sync service to avoid webhook issues if possible
    # We rely on persistent service driver
    for unit in all_distilled:
        success = await service.persist_distilled_unit(unit)
        if success:
            count += 1
            if count % 5 == 0:
                print(f"Persisted [{count}/{len(all_distilled)}]: {unit.name}")

    print(f"\n✅ System Soul Distillation successful! Persisted {count} units to Neo4j.")

if __name__ == "__main__":
    asyncio.run(main())