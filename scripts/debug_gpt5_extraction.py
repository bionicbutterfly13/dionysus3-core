import os
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.llm_service import chat_completion, GPT5_NANO
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_gpt5")

async def debug_extraction():
    content = """
    Stefan Georgi's RMBC method stands for Research, Mechanism, Brief, Copy.
    The Unique Mechanism is the 'thing' that makes the product work and why other things failed.
    The Problem Mechanism is why they are currently stuck.
    """
    
    insight_type = "process_insight"
    schema_hints = {
        "process_insight": '{"name": "...", "steps": ["...", "..."], "goal": "...", "why_it_works": "..."}'
    }
    
    system_prompt = ""

    print(f"Model: {GPT5_NANO}")
    print(f"System Prompt: {system_prompt}")
    
    user_content = f"""You are a wisdom extraction analyst. Extract a structured {insight_type} from the content.
    Respond with JSON only using this schema:
    {schema_hints.get(insight_type, '{}')}
    
    CONTENT:
    {content}"""

    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": user_content}],
            system_prompt=system_prompt,
            model=GPT5_NANO,
            max_tokens=512,
        )
        
        print(f"Raw Response: '{response}'")
        if not response:
            print("ALERT: Response is empty string!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_extraction())
