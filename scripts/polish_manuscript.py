
import os
import re

INPUT_FILE = "specs/018-ias-knowledge-base/04_bridged_manuscript_copy.md"
OUTPUT_FILE = "specs/018-ias-knowledge-base/04_polished_manuscript.md"

def polish_text(text: str) -> str:
    # 1. Remove Estimated Runtime blocks
    text = re.sub(r'\*Estimated Runtime:.*?\*', '', text)
    text = re.sub(r'Estimated Runtime:.*?\n', '', text)
    
    # 2. Remove Chapter markers
    text = re.sub(r'\*\*\[CHAPTER (OPEN|OPENING|CLOSE|CLOSING)\]\*\*', '', text)
    
    # 3. Clean up specific dictation artifacts
    # "Is Dr. Mani" -> "Hi, this is Dr. Mani" or just remove "Is"
    text = text.replace("Is Dr. Mani", "I'm Dr. Mani")
    
    # "grab you bad" often used as a crutch
    text = text.replace("grab you bad", "stay stuck")
    
    # "There's that" or "that's that" often trailing
    text = text.replace("There's that.", "")
    text = text.replace("That's that.", "")
    
    # 4. Remove excessive the "Let's get it" or other intro artifacts if redundant
    # (Keeping it for now as it feels like his voice unless it's repeated every chapter)
    
    # 5. Clean up extra newlines and separators
    text = re.sub(r'---', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 6. Remove remaining Markdown bold/italics for TTS
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    return text.strip()

def run_polish():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return
        
    print(f"Polishing manuscript: {INPUT_FILE}")
    with open(INPUT_FILE, 'r') as f:
        content = f.read()
        
    polished = polish_text(content)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(polished)
        
    print(f"Polished manuscript saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_polish()
