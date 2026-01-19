import re
import os

SOURCE_FILE = "scripts/narrative_active_inference_paper.md"
OUTPUT_DIR = "scripts/chunks"

def split_document():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(SOURCE_FILE, "r") as f:
        content = f.read()

    # Define split points based on headers
    # Chunk 1: Intro to Event Narrative
    # Chunk 2: Event Narrative to Identity
    # Chunk 3: Identity to Conclusion
    # Chunk 4: Conclusion to End

    # Regex to find headers
    # Note: Adjust these based on actual file content if headers differ slightly
    headers = [
        ("chunk_01_intro.md", r"^# Narrative as active inference"),
        ("chunk_02_event_narrative.md", r"^# Event narratives"),
        ("chunk_03_identity_social.md", r"^# Narrative Identity"),
        ("chunk_04_conclusion.md", r"^# Future directions")
    ]
    
    # We will find indices of these headers
    indices = []
    for filename, pattern in headers:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            indices.append((filename, match.start()))
        else:
            print(f"Warning: Header for {filename} not found with pattern '{pattern}'")

    if not indices:
        print("No headers found using current patterns. Aborting split.")
        return

    # Sort indices just in case (though they should be in order usually)
    indices.sort(key=lambda x: x[1])

    # Now slice
    for i in range(len(indices)):
        filename, start_idx = indices[i]
        
        # End index is the start of the next chunk, or end of file
        if i + 1 < len(indices):
            end_idx = indices[i+1][1]
        else:
            end_idx = len(content)

        chunk_content = content[start_idx:end_idx].strip()
        
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, "w") as out:
            out.write(chunk_content)
        
        print(f"Created {filename} ({len(chunk_content)} chars)")

if __name__ == "__main__":
    split_document()
