
import os
import re

AUDIO_DIR = "data/audiobook/parts"
OUTPUT_DIR = "data/audiobook/chapters"

def concatenate_chapters():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Get all parts
    files = sorted([f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")])
    
    # Group by chapter (e.g., 000_INTRODUCTION, 001_CHAPTER_1)
    # The filename format is: {i:03d}_{safe_chapter}_part_{chunk}.mp3
    # Actually, the index i is unique per chapter? 
    # Let's check format: 000_INTRODUCTION_part_1.mp3
    # 006_CHAPTER_2_part_1.mp3
    # We want to group by the logical chapter name, which includes the index prefix.
    
    chapters = {}
    
    for f in files:
        # Extract "000_INTRODUCTION" from "000_INTRODUCTION_part_1.mp3"
        match = re.match(r"(\d+_[a-zA-Z0-9_]+)_part_\d+\.mp3", f)
        if match:
            chapter_key = match.group(1)
            if chapter_key not in chapters:
                chapters[chapter_key] = []
            chapters[chapter_key].append(f)
            
    print(f"🧩 Found {len(chapters)} chapters to assemble.")
    
    for chapter, parts in chapters.items():
        # Sort parts just in case (though file list was sorted)
        # We rely on the filenames sorting correctly (part_1, part_2...)
        # Wait, sorted() on strings: part_1, part_10, part_2 -> incorrect.
        # We need natural sort or explicit part check.
        # But our parts are 1-based integers.
        # Let's sort by extracted part number.
        
        parts.sort(key=lambda x: int(re.search(r"_part_(\d+)\.mp3", x).group(1)))
        
        output_path = os.path.join(OUTPUT_DIR, f"{chapter}.mp3")
        print(f"  concatenating {len(parts)} parts into {chapter}.mp3...")
        
        with open(output_path, 'wb') as outfile:
            for part in parts:
                with open(os.path.join(AUDIO_DIR, part), 'rb') as infile:
                    outfile.write(infile.read())
                    
        print(f"  ✅ Created {output_path}")

if __name__ == "__main__":
    concatenate_chapters()
