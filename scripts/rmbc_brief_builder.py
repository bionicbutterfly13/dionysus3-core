
import asyncio
import json
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
import textwrap

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.services.llm_service import chat_completion, GPT5_NANO
except ImportError:
    # Fallback/Mock for testing without full env
    print("⚠️  Warning: Could not import llm_service. LLM features will be disabled.")
    chat_completion = None
    GPT5_NANO = "gpt-5-nano"

# --- Configuration ---
BRIEF_OUTPUT_DIR = "data/briefs"
SKILL_FILE_PATH = "/Users/manisaintvictor/.claude/skills/061-rmbc-methodology.SKILL.md"

# --- The 25-Point New Brief Structure ---
BRIEF_STRUCTURE = [
    {
        "section": "Part 1: The Core Foundation",
        "questions": [
            {"id": "1", "q": "Who is the Audience? (Demographics + Psychographics)"},
            {"id": "2", "q": "What are the Pain Points/Fears? (1-3 HUGE ones, Short term vs Long term)"},
            {"id": "3", "q": "The Big Promise (Reversed Pain): How will this change their lives forever?"},
            {"id": "4", "q": "The 'Solved' State: What does life look like after the pain is gone?"}
        ]
    },
    {
        "section": "Part 2: The Mechanism (The Heart)",
        "questions": [
            {"id": "5", "q": "Existing Solutions: What exists? Why aren't they working?"},
            {"id": "6", "q": "The UMP & UMS Pair (The Real Root Cause & The Fix). Constraint: Be detailed."},
            {"id": "7", "q": "Unique Nickname (The 'Hook' name, e.g., 'The 7-Second Ritual')."},
            {"id": "8", "q": "Ingredients/Components (components + studies)."}
        ]
    },
    {
        "section": "Part 3: The Offer & Claims",
        "questions": [
            {"id": "9", "q": "Bold Product Claims: Specific life changes (different from #3)."},
            {"id": "10", "q": "Product Details: Name, Format, Quantity, Fascinations."},
            {"id": "11", "q": "Background/Discovery Story: Maximum drama. Hero's Journey."},
            {"id": "12", "q": "Main Speaker: Credibility snapshot. [Default: Dr. Mani]"},
            {"id": "13", "q": "Second Speaker/Expert (Optional)."},
            {"id": "14", "q": "Brand/Company (If applicable)."}
        ]
    },
    {
        "section": "Part 4: Proof & Logistics",
        "questions": [
            {"id": "15", "q": "Testimonials/Social Proof."},
            {"id": "16", "q": "Credibility Builders: Studies, Endorsements, As Seen On."},
            {"id": "17", "q": "Retail Price (Anchor High)."},
            {"id": "18", "q": "Actual Price (The Offer)."},
            {"id": "19", "q": "Options: Bundles/Pricing tiers."},
            {"id": "20", "q": "The Guarantee: Risk Reversal details."},
            {"id": "21", "q": "Bonuses: Value stack additions."}
        ]
    },
    {
        "section": "Part 5: Closing Logic",
        "questions": [
            {"id": "22", "q": "Scarcity Elements: Why buy now?"},
            {"id": "23", "q": "Future-Paced Results: 'Imagine a week from now...'"},
            {"id": "24", "q": "Objections: Common reasons for 'No' -> How to answer them."},
            {"id": "25", "q": "Hooks/Big Ideas: Specific angles to test in lead."}
        ]
    }
]

# --- Helper Functions ---

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text: str):
    print(f"\n\033[1;36m{text}\033[0m")
    print("=" * len(text))

def print_section(text: str):
    print(f"\n\033[1;33m--- {text} ---\033[0m\n")

async def critique_answer(question: str, answer: str) -> str:
    """Uses LLM to critique the answer based on RMBC principles."""
    if not chat_completion:
        return "LLM Critique Unavailable."

    system_prompt = (
        "You are the RMBC Critique Engine. You are Stefan Georgi's AI clone.\n"
        "Critique the user's answer to the brief question. Be ruthless but helpful.\n"
        "If the Mechanism is weak (generic), demand a 'Metaphorical' or 'Transubstantiated' mechanism.\n"
        "Keep it brief (bullet points)."
    )
    
    prompt = f"Question: {question}\nUser Answer: {answer}\n\nCritique this answer:"
    
    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            model=GPT5_NANO
        )
        return response
    except Exception as e:
        return f"Critique failed: {e}"

# --- Main Interaction Loop ---

async def main():
    if not os.path.exists(BRIEF_OUTPUT_DIR):
        os.makedirs(BRIEF_OUTPUT_DIR)

    clear_screen()
    print_header("📝 RMBC 2.0 Brief Builder (The Coordination Pool Interrogation)")
    print("Type 'skip' to skip a question. Type 'exit' to save and quit early.\n")

    project_name = input("Enter Project Name (e.g., 'solar_generator'): ").strip().replace(" ", "_")
    if not project_name:
        project_name = f"brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    brief_data = {"project_name": project_name, "timestamp": datetime.now().isoformat(), "sections": {}}

    for section in BRIEF_STRUCTURE:
        print_section(section["section"])
        section_data = {}
        
        for item in section["questions"]:
            q_text = f"[{item['id']}] {item['q']}"
            print(f"\033[1m{q_text}\033[0m")
            
            answer = input("> ").strip()
            
            if answer.lower() == 'exit':
                break
            
            # Default Overrides
            if item["id"] == "12" and not answer:
                answer = "Dr. Mani"
                print(f"\033[3mUsing Default: {answer}\033[0m")

            # "Ultrathink" Critique Mode
            # If answer is substantial, offer critique
            if len(answer) > 10 and chat_completion:
                print("\n🧐 analyzing...")
                critique = await critique_answer(item['q'], answer)
                print(f"\n\033[3mCritique:\n{critique}\033[0m\n")
                
                refine = input("Update answer based on critique? (Enter new answer or 'n' to keep): ").strip()
                if refine.lower() != 'n':
                    answer = refine

            section_data[item["id"]] = {"question": item["q"], "answer": answer}
            print() # Newline for spacing
        
        brief_data["sections"][section["section"]] = section_data
        if answer.lower() == 'exit':
            break

    # Save
    filepath = os.path.join(BRIEF_OUTPUT_DIR, f"{project_name}_brief.json")
    with open(filepath, "w") as f:
        json.dump(brief_data, f, indent=2)
    
    print_header("✅ Brief Initialized")
    print(f"Saved to: {filepath}")
    print("Next Step: Run 'Draft Assembly' to generate the VSL.")

if __name__ == "__main__":
    asyncio.run(main())
