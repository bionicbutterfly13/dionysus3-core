"""
Lightweight Soul Distillation
Sequential processing with longer timeouts to avoid API issues.
"""

import asyncio
import os
import json
import logging
import re
from pathlib import Path
import sys
from uuid import uuid4

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger("dionysus.distill_soul_lite")

RAW_FILE = "wisdom_extraction_raw.json"
DISTILLED_FILE = "wisdom_distilled.json"
BATCH_SIZE = 10  # Smaller batches

def repair_json(text):
    """Robust JSON cleaning."""
    try:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        if not (text.startswith("[") or text.startswith("{")):
            start = min(text.find("["), text.find("{"))
            if start == -1:
                start = max(text.find("["), text.find("{"))
            end = max(text.rfind("]"), text.rfind("}"))
            if start != -1 and end != -1:
                text = text[start:end+1]
        
        text = re.sub(r",\s*([\}\]])", r"\1", text)
        return text
    except Exception:
        return text

async def distill_batch(batch, batch_idx, total_batches):
    """Distill a batch of insights into canonical units."""
    print(f"Distilling batch {batch_idx}/{total_batches} ({len(batch)} fragments)...")
    
    system_prompt = "You are a master of conceptual synthesis. Merge insights into canonical wisdom units."
    user_content = f"""
Merge these insight fragments into a JSON list of wisdom units.

FRAGMENTS:
{json.dumps(batch, indent=2, default=str)[:8000]}

OUTPUT SCHEMA (respond with ONLY this JSON list):
[
  {{
    "type": "mental_model" or "strategic_principle",
    "name": "Canonical Name",
    "summary": "Detailed description (2-3 sentences)",
    "provenance_chain": ["session_id1", "session_id2"],
    "importance": "high" or "medium" or "low"
  }}
]

Rules:
- Merge similar concepts into single units
- Be specific and actionable
- Include provenance (source session IDs)
- Respond with ONLY the JSON list
"""
    
    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": user_content}],
            system_prompt=system_prompt,
            model="openai/gpt-4o-mini",  # Use gpt-4o-mini for reliability
            max_tokens=2048,
            # timeout handled by litellm default
        )
        
        cleaned = repair_json(response)
        data = json.loads(cleaned)
        
        units = []
        if isinstance(data, list):
            for d in data:
                d["wisdom_id"] = f"distilled-{uuid4().hex[:8]}"
                d["created_at"] = str(asyncio.get_event_loop().time())
                units.append(d)
        
        print(f"  → {len(units)} units created")
        return units
        
    except json.JSONDecodeError as e:
        print(f"  JSON error: {e}")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []

async def main():
    # Load raw extracts
    if not os.path.exists(RAW_FILE):
        print(f"No raw file found: {RAW_FILE}")
        return
    
    with open(RAW_FILE, "r") as f:
        raw_data = json.load(f)
    
    print(f"Loaded {len(raw_data)} raw session extracts.")
    
    # Flatten all insights
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
    
    print(f"Extracted {len(all_insights)} insight fragments.")
    
    # Load existing distilled units for resumption
    existing_units = []
    if os.path.exists(DISTILLED_FILE):
        try:
            with open(DISTILLED_FILE, "r") as f:
                existing_units = json.load(f)
            print(f"Loaded {len(existing_units)} existing distilled units.")
        except Exception as e:
            print(f"Warning: Could not load existing: {e}")
    
    # Process in batches SEQUENTIALLY (to avoid rate limits)
    batches = [all_insights[i:i + BATCH_SIZE] for i in range(0, len(all_insights), BATCH_SIZE)]
    
    all_units = existing_units.copy()
    processed_count = 0
    
    for i, batch in enumerate(batches):
        batch_units = await distill_batch(batch, i + 1, len(batches))
        all_units.extend(batch_units)
        processed_count += len(batch)
        
        # Save after each batch
        with open(DISTILLED_FILE, "w") as f:
            json.dump(all_units, f, indent=2, default=str)
        
        # Rate limiting - pause between batches
        if i < len(batches) - 1:
            await asyncio.sleep(1)
    
    print(f"\n✅ Distillation complete. {len(all_units)} total canonical units.")

if __name__ == "__main__":
    asyncio.run(main())
