"""
Lightweight Wisdom Fleet Extraction
Uses direct LLM calls instead of heavy CodeAgent framework.
Much faster: ~5-10 sec/file vs 30+ sec/file
"""

import asyncio
import os
import glob
import json
import logging
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger("dionysus.wisdom_fleet_lite")

# Config
ARCHIVE_PATH = "/Volumes/Asylum/repos/claude-conversation-extractor/Claude Conversations/*.md"
OUTPUT_FILE = "wisdom_extraction_raw.json"
BATCH_SIZE = 10  # Parallel requests
MAX_CONTENT_CHARS = 12000  # Truncate long conversations

EXTRACTION_PROMPT = """You are a wisdom extraction agent. Analyze this conversation and extract:

1. MENTAL MODELS: Recurring principles, decision frameworks, contrarian insights
2. STRATEGIC PRINCIPLES: Actionable guidelines that emerged from problem-solving
3. KEY INSIGHTS: Important learnings, realizations, or breakthroughs

SESSION_ID: {session_id}

CONTENT (truncated if long):
{content}

Respond with ONLY valid JSON:
{{
  "session_id": "{session_id}",
  "wisdom_insights": [
    {{"type": "mental_model", "name": "...", "summary": "...", "importance": "high|medium|low"}},
    {{"type": "strategic_principle", "name": "...", "summary": "...", "importance": "high|medium|low"}}
  ],
  "key_themes": ["theme1", "theme2"],
  "reasoning": "Brief explanation of extraction logic"
}}

If the conversation has no extractable wisdom (trivial, interrupted, or purely technical), return:
{{"session_id": "{session_id}", "wisdom_insights": [], "key_themes": [], "reasoning": "No significant wisdom found"}}
"""

def repair_json(text):
    """Clean LLM JSON output."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text

async def extract_single(path: str) -> dict:
    """Extract wisdom from a single conversation file."""
    session_id = os.path.basename(path).replace(".md", "")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Truncate if too long
        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS] + "\n\n[TRUNCATED]"
        
        prompt = EXTRACTION_PROMPT.format(session_id=session_id, content=content)
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a precise JSON-only responder. Extract wisdom insights.",
            model=GPT5_NANO,
            max_tokens=1024
        )
        
        cleaned = repair_json(response)
        result = json.loads(cleaned)
        result["session_id"] = session_id  # Ensure session_id is set
        return result
        
    except json.JSONDecodeError as e:
        print(f"  JSON error for {session_id}: {e}")
        return {"session_id": session_id, "wisdom_insights": [], "error": "json_parse_error"}
    except Exception as e:
        print(f"  Error for {session_id}: {e}")
        return {"session_id": session_id, "wisdom_insights": [], "error": str(e)}

async def process_batch(paths: list, batch_num: int, total_batches: int) -> list:
    """Process a batch of files in parallel."""
    print(f"Batch {batch_num}/{total_batches} ({len(paths)} files)...")
    tasks = [extract_single(p) for p in paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid = []
    for r in results:
        if isinstance(r, Exception):
            print(f"  Exception: {r}")
        elif r:
            valid.append(r)
    return valid

async def main():
    # Load existing results for resumption
    all_results = []
    processed_ids = set()
    
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                all_results = json.load(f)
                processed_ids = {r.get("session_id") for r in all_results if r.get("session_id")}
            print(f"Resuming: {len(processed_ids)} files already processed.")
        except Exception as e:
            print(f"Warning: Could not load existing results: {e}")
    
    # Get all files
    all_files = sorted(glob.glob(ARCHIVE_PATH))
    remaining = [f for f in all_files if os.path.basename(f).replace(".md", "") not in processed_ids]
    
    print(f"Starting Lite Fleet: {len(remaining)} remaining of {len(all_files)} total files.")
    
    if not remaining:
        print("All files already processed!")
        return
    
    # Process in batches
    batches = [remaining[i:i + BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]
    
    for i, batch in enumerate(batches):
        batch_results = await process_batch(batch, i + 1, len(batches))
        all_results.extend(batch_results)
        
        # Save after each batch
        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_results, f, indent=2)
        
        # Progress
        insights_count = sum(len(r.get("wisdom_insights", [])) for r in batch_results)
        print(f"  → {insights_count} insights extracted. Total: {len(all_results)} sessions.")
    
    print(f"\n✅ Extraction complete. {len(all_results)} total sessions processed.")

if __name__ == "__main__":
    asyncio.run(main())
