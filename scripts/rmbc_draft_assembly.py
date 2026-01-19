
import json
import os
import sys
from typing import Dict
import datetime

# Configuration
BRIEF_DIR = "data/briefs"
OUTPUT_DIR = "specs/marketing_rhapsodies/drafts"

# --- The 10-Step VSL Template (Extracted & Refined) ---
# "Slotting" Logic mapping Brief Q's to Template
VSL_TEMPLATE = """# VSL Draft: {{project_name}}
**Date**: {{date}}
**Spokesperson**: {{spokesperson}}
**Hook Used**: {{hook_angle}}

---

## SCENE: PRE-LEAD / MICRO-LEAD (0:00 - 0:15)
(Pattern Interrupt. Visual of {{pain_point_short}} or bizarre mechanism.)

**{{spokesperson}} (VO)**: 
If you want to permanently fix **{{pain_point_1}}** without **{{failed_solution_1}}** or even **{{failed_solution_2}}**, then this will be the most important video you watch all year.

Hi, I'm **{{spokesperson}}**. And in the next 5 minutes, I'm going to show you the **{{unique_nickname}}**, the bizarre {{ingredient_count}}second ritual that reverses **{{ump}}**...

Even if you've tried everything.

---

## SCENE: THE LEAD (0:15 - 2:00)
(Agitate Pain -> Promise Solution)

You see, for years, they told you that **{{pain_point_1}}** was caused by **{{enemy}}** (The Old Lie).

They told you to just "try harder" with **{{failed_solution_list}}**.

But isn't it weird? You did all that. You bought the **{{failed_solution_1}}**. You tried the **{{failed_solution_2}}**. And yet...

**{{internal_symptom}}**.

Here is the truth: It is NOT YOUR FAULT.

The real reason you are suffering is not laziness. It is a hidden biologicial switch called **{{ump}}** (Unique Mechanism of Problem).

And until you address **{{ump}}**, nothing you do will work. The **{{failed_solution_1}}** can't work, because it ignores the {{ump}}.

---

## SCENE: BACKGROUND STORY (2:00 - 4:00)
(Credibility + Emotional Connection)

I discovered this the hard way.

**{{discovery_story}}**

I was at rock bottom. **{{event_trigger}}**. I felt **{{internal_symptom}}**.

I decided to find the truth. I looked at the research. And that's when I found the study from **{{credibility_builder}}** that changed everything.

---

## SCENE: THE MECHANISM (4:00 - 6:00)
(The Pivot: UMP -> UMS)

The study revealed that **{{pain_point_1}}** is actually a symptom of **{{ump}}**.

(Explain UMP Logic: {{ump_description}})

So, if **{{ump}}** is the problem, what is the solution?

You need a way to flip that switch. You need **{{ums}}** (Unique Mechanism of Solution).

When you use **{{ums}}**, you finally unlock **{{solved_state}}**.

---

## SCENE: PRODUCT REVEAL (6:00 - 8:00)
(Introduction of {{product_name}})

I looked for a solution that used **{{ums}}**. I couldn't find one. 
So I created it myself.

Introducing... **{{product_name}}**.

The world's first **{{product_format}}** designed to target **{{ump}}** using **{{ums}}**.

Inside, you'll find:
*   **{{ingredients}}**
*   **{{fascinations}}**

---

## SCENE: THE CLOSE (8:00+)
(Offer Stack)

Imagine a life where **{{solved_state}}**. That is what **{{product_name}}** does.

Normally, this would cost **{{retail_price}}**.
But today, your price is **{{actual_price}}**.

**{{guarantee}}**.

**{{scarcity}}**.

Click the button below now.

---
"""

def load_brief(filepath: str) -> Dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def clean_key(key_text: str) -> str:
    """Standardizes keys for easier template matching."""
    return key_text.lower().strip()

def map_brief_to_variables(brief: Dict) -> Dict:
    """Maps the 25-point brief answers to the Template variables."""
    secs = brief["sections"]
    
    # Helper to safely get answer
    def get_a(part, q_id):
        return secs.get(part, {}).get(q_id, {}).get("answer", "[MISSING]")

    # Part 1
    p1 = "Part 1: The Core Foundation"
    pain_raw = get_a(p1, "2")
    pain_short = pain_raw.split(",")[0] if "," in pain_raw else pain_raw
    
    # Part 2
    p2 = "Part 2: The Mechanism (The Heart)"
    failed_raw = get_a(p2, "5")
    failed_list = [x.strip() for x in failed_raw.split(".") if x.strip()]
    fs1 = failed_list[0] if failed_list else "generic solutions"
    fs2 = failed_list[1] if len(failed_list) > 1 else "wild guesses"
    
    ump = get_a(p2, "6").split("UMS")[0] # Rough split if user combined them
    ums = get_a(p2, "6").split("UMS")[1] if "UMS" in get_a(p2, "6") else "The Solution"
    
    # Part 3
    p3 = "Part 3: The Offer & Claims"
    
    # Part 4
    p4 = "Part 4: Proof & Logistics"
    
    # Part 5
    p5 = "Part 5: Closing Logic"

    return {
        "project_name": brief.get("project_name", "Untitled"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "spokesperson": get_a(p3, "12"), # Defaulted to Dr. Mani in Builder
        
        "pain_point_1": pain_raw,
        "pain_point_short": pain_short,
        "solved_state": get_a(p1, "4"),
        
        "failed_solution_1": fs1,
        "failed_solution_2": fs2,
        "failed_solution_list": failed_raw,
        "enemy": get_a(p1, "3"), # Using Big Promise as placeholder for enemy if missing, looking for better mapping
        
        "unique_nickname": get_a(p2, "7"),
        "ump": ump,
        "ump_description": "See brief for full UMP details.",
        "ums": ums,
        "ingredient_count": "5",
        "ingredients": get_a(p2, "8"),
        
        "product_name": get_a(p3, "10"),
        "product_format": "Specially formulated system",
        "discovery_story": get_a(p3, "11"),
        "fascinations": get_a(p3, "10"), # Overlap in brief structure
        
        "credibility_builder": get_a(p4, "16"),
        "retail_price": get_a(p4, "17"),
        "actual_price": get_a(p4, "18"),
        "guarantee": get_a(p4, "20"),
        
        "scarcity": get_a(p5, "22"),
        "internal_symptom": get_a(p1, "2"), # Reusing pain for symptom if distinct q missing
        "event_trigger": "The moment I realized I couldn't go on",
        "hook_angle": get_a(p5, "25")
    }

def main():
    if not os.path.exists(BRIEF_DIR):
        print("No briefs found.")
        return
        
    files = [f for f in os.listdir(BRIEF_DIR) if f.endswith(".json")]
    if not files:
        print("No brief JSON files found.")
        return
        
    # Pick latest brief by modification time
    latest_file = max([os.path.join(BRIEF_DIR, f) for f in files], key=os.path.getmtime)
    print(f"Assembly: Using latest brief -> {latest_file}")
    
    brief = load_brief(latest_file)
    variables = map_brief_to_variables(brief)
    
    # Render
    draft_content = VSL_TEMPLATE
    for key, value in variables.items():
        draft_content = draft_content.replace(f"{{{{{key}}}}}", str(value))
        
    # Save
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    output_filename = f"{variables['project_name']}_vsl_draft.md"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    with open(output_path, "w") as f:
        f.write(draft_content)
        
    print(f"\n✅ VSL Draft Assembled: {output_path}")
    print("Next Step: 'Voice Validation' (ElevenLabs).")

if __name__ == "__main__":
    main()
