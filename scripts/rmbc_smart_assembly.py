
import asyncio
import json
import os
import sys
import datetime

# Add project root to sys.path to allow imports from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.llm_service import chat_completion

# Configuration
BRIEF_DIR = "data/briefs"
OUTPUT_DIR = "specs/marketing_rhapsodies/drafts"

VSL_FRAMEWORK_PROMPT = """
You are a legendary direct response copywriter (Stefan Georgi/Perry Marshall hybrid).
You write with "Rhythm", "Short sentences", and "Punch".
You despise "Corporate Speak" and "Template Filler" language.

OBJECTIVE:
Write a high-converting Video Sales Letter (VSL) script based on the provided BRIEF data.
Follow the 10-Step CVSL Framework Structure perfectly, but SMOOTH the transitions.
Do NOT just paste the variable values. WEAVE them into sentences that sound colloquial and spoken.

FRAMEWORK STEPS:
1. PRE-LEAD (0-15s): Pattern interrupt. If they want {solved_state} without {failed_solution_1}, listen up.
2. THE LEAD (15s-2m): Agitate pain {pain_point_1}. The Old Lie: {enemy}. It's not their fault.
3. BACKGROUND STORY (2-4m): {discovery_story}. The moment of truth: {event_trigger}.
4. THE MECHANISM (4-6m): The Pivot. The problem is {ump}. The solution is {ums}.
5. PRODUCT REVEAL (6-8m): Introducing {product_name}. Features: {ingredients}.
6. THE CLOSE (8m+): Offer stack. Price drop from {retail_price} to {actual_price}. Guarantee: {guarantee}. Scarcity: {scarcity}.

BRIEF VARIABLES:
{variables_json}

INSTRUCTIONS:
- Write the full script in Markdown.
- Use ## SCENE Headers.
- Use **Bold** for emphasis.
- Spoken word: "Don't" instead of "Do not". "Here's the thing" instead of "Consider the following".
- Output ONLY the Markdown VSL.
"""

def load_brief(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def map_brief_to_variables(brief: dict) -> dict:
    """Maps the 25-point brief answers to a flat dictionary for the LLM."""
    secs = brief["sections"]
    
    def get_a(part, q_id):
        return secs.get(part, {}).get(q_id, {}).get("answer", "[MISSING]")

    p1 = "Part 1: The Core Foundation"
    p2 = "Part 2: The Mechanism (The Heart)"
    p3 = "Part 3: The Offer & Claims"
    p4 = "Part 4: Proof & Logistics"
    p5 = "Part 5: Closing Logic"

    return {
        "project_name": brief.get("project_name", "Untitled"),
        "pain_point_1": get_a(p1, "2"),
        "solved_state": get_a(p1, "4"),
        "enemy": get_a(p1, "3"),
        
        "failed_solution_1": get_a(p2, "5").split(".")[0],
        "ump": get_a(p2, "6"),
        "ums": get_a(p2, "6"), # Logic handles distinction in prompt context usually, passing raw is safer for LLM to parse
        "unique_nickname": get_a(p2, "7"),
        "ingredients": get_a(p2, "8"),
        
        "product_name": get_a(p3, "10"),
        "discovery_story": get_a(p3, "11"),
        "spokesperson": get_a(p3, "12"),
        
        "retail_price": get_a(p4, "17"),
        "actual_price": get_a(p4, "18"),
        "guarantee": get_a(p4, "20"),
        
        "scarcity": get_a(p5, "22"),
        "hook_angle": get_a(p5, "25")
    }

async def generate_draft():
    if not os.path.exists(BRIEF_DIR):
        print("No briefs found.")
        return
        
    files = [f for f in os.listdir(BRIEF_DIR) if f.endswith(".json")]
    if not files:
        print("No brief JSON files found.")
        return
        
    # Use latest brief
    latest_file = max([os.path.join(BRIEF_DIR, f) for f in files], key=os.path.getmtime)
    print(f"Smart Assembly: Using latest brief -> {latest_file}")
    
    brief = load_brief(latest_file)
    variables = map_brief_to_variables(brief)
    
    # Construct Prompt
    user_message = VSL_FRAMEWORK_PROMPT.format(
        solved_state=variables["solved_state"],
        failed_solution_1=variables["failed_solution_1"],
        pain_point_1=variables["pain_point_1"],
        enemy=variables["enemy"],
        discovery_story=variables["discovery_story"],
        event_trigger="The moment I realized...", # simplified
        ump=variables["ump"],
        ums=variables["ums"],
        product_name=variables["product_name"],
        ingredients=variables["ingredients"],
        retail_price=variables["retail_price"],
        actual_price=variables["actual_price"],
        guarantee=variables["guarantee"],
        scarcity=variables["scarcity"],
        variables_json=json.dumps(variables, indent=2)
    )
    
    print("🧠 Generating Smart Draft with GPT-5 Nano...")
    content = await chat_completion(
        messages=[{"role": "user", "content": user_message}],
        system_prompt="You are an expert copywriter."
    )
    
    # Save
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    output_filename = f"{variables['project_name']}_SMART_vsl_draft.md"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    with open(output_path, "w") as f:
        f.write(content)
        
    print(f"\n✅ Smart Draft Assembled: {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_draft())
