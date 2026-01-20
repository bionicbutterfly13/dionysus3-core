
import asyncio
import os
import sys
import re
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.elevenlabs_service import get_elevenlabs_service

from dotenv import load_dotenv
load_dotenv()

# Configuration
POLISHED_MANUSCRIPT = "specs/018-ias-knowledge-base/04_polished_manuscript.md"
AUDIO_OUTPUT_DIR = "data/audiobook"
CHUNK_SIZE = 2500  # ElevenLabs recommended for stability

def split_manuscript(text: str) -> List[dict]:
    """
    Splits the manuscript into logical chapters and chunks.
    Returns a list of segments with meta info.
    """
    # Split by Chapter headers first
    chapters = re.split(r'(# (?:INTRODUCTION|CHAPTER \d+:|OUTRO))', text)
    
    segments = []
    current_title = "Title"
    
    for i in range(1, len(chapters), 2):
        title = chapters[i].strip()
        body = chapters[i+1].strip()
        
        # Sub-split body into chunks of ~CHUNK_SIZE
        # Try to split at paragraph ends (. \n\n)
        paragraphs = body.split('\n\n')
        current_chunk = ""
        chunk_idx = 1
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < CHUNK_SIZE:
                current_chunk += p + "\n\n"
            else:
                segments.append({
                    "chapter": title,
                    "chunk": chunk_idx,
                    "text": current_chunk.strip()
                })
                current_chunk = p + "\n\n"
                chunk_idx += 1
        
        if current_chunk:
            segments.append({
                "chapter": title,
                "chunk": chunk_idx,
                "text": current_chunk.strip()
            })
            
    return segments

async def generate_audiobook():
    if not os.path.exists(POLISHED_MANUSCRIPT):
        print(f"Error: {POLISHED_MANUSCRIPT} not found.")
        return

    # Ensure output dir
    parts_dir = os.path.join(AUDIO_OUTPUT_DIR, "parts")
    if not os.path.exists(parts_dir):
        os.makedirs(parts_dir)

    print(f"📖 Reading polished manuscript...")
    with open(POLISHED_MANUSCRIPT, 'r') as f:
        text = f.read()

    segments = split_manuscript(text)
    print(f"📦 Split into {len(segments)} segments.")

    service = get_elevenlabs_service()
    
    # Process segments
    for i, seg in enumerate(segments):
        # Create safe filename
        safe_chapter = re.sub(r'[^a-zA-Z0-9]', '_', seg['chapter']).strip('_')
        filename = f"{i:03d}_{safe_chapter}_part_{seg['chunk']}.mp3"
        output_path = os.path.join(parts_dir, filename)
        
        if os.path.exists(output_path):
            print(f"⏭️  Skipping existing: {filename}")
            continue

        print(f"🗣️  Generating [{i+1}/{len(segments)}]: {filename} ({len(seg['text'])} chars)")
        
        try:
            with open(output_path, "wb") as f_out:
                async for chunk in service.stream_speech(seg['text']):
                    f_out.write(chunk)
            print(f"✅ Saved.")
        except Exception as e:
            print(f"❌ Error generating {filename}: {e}")
            break # Stop on error to avoid burning quota/partial failed states

    print(f"\n🎧 Audiobook generation complete. Files located in: {parts_dir}")

if __name__ == "__main__":
    asyncio.run(generate_audiobook())
