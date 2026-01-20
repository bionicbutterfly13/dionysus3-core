
import asyncio
import os
import sys
import re
import argparse
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.elevenlabs_service import get_elevenlabs_service

from dotenv import load_dotenv
load_dotenv()

# Configuration
DRAFTS_DIR = "specs/marketing_rhapsodies/drafts"
AUDIO_OUTPUT_DIR = "data/audio_validation"

def strip_markdown(text: str) -> str:
    """
    Strips markdown formatting for cleaner TTS reading.
    - Removes **bold**, *italics*, [links]
    - Removes H1/H2 headers (#)
    - Removes metadata blocks
    """
    # Remove metadata block at top (simplified)
    if text.startswith("#"):
        lines = text.split('\n')
        # Skip lines until first separator
        content_start = 0
        for i, line in enumerate(lines):
            if line.strip() == "---":
                content_start = i + 1
                break
        text = "\n".join(lines[content_start:])

    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text) # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)     # Italics
    text = re.sub(r'#+\s', '', text)             # Headers
    text = re.sub(r'\[(.*?)\]', r'\1', text)     # Brackets (keep content)
    text = re.sub(r'\(.*?\)', '', text)          # Parentheses (often stage directions!) - Wait, keep stage directions?
                                                 # Actually, stage directions like (Pattern Interrupt) should NOT be read.
                                                 # We remove them for the audio read-through.
    
    # Remove stage directions lines that start with (
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        if line.strip().startswith("(") and line.strip().endswith(")"):
            continue # Skip stage direction lines
        if line.strip().startswith("SCENE:"):
            continue # Skip scene headers
        clean_lines.append(line)
        
    return "\n".join(clean_lines)

async def generate_audio(filepath: str):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return

    # Ensure output dir
    if not os.path.exists(AUDIO_OUTPUT_DIR):
        os.makedirs(AUDIO_OUTPUT_DIR)

    filename = os.path.basename(filepath).replace(".md", ".mp3").replace("_vsl_draft", "_validation")
    output_path = os.path.join(AUDIO_OUTPUT_DIR, filename)

    print(f"📖 Reading: {filepath}")
    with open(filepath, 'r') as f:
        raw_text = f.read()

    clean_text = strip_markdown(raw_text)
    
    # Preview
    preview = clean_text[:200].replace('\n', ' ')
    print(f"🗣️  Preview Text: \"{preview}...\"")
    print(f"⏳ Generating Audio via ElevenLabs (Stream -> File)...")

    service = get_elevenlabs_service()
    
    try:
        chunk_count = 0
        with open(output_path, "wb") as f_out:
            async for chunk in service.stream_speech(clean_text):
                f_out.write(chunk)
                chunk_count += 1
                if chunk_count % 10 == 0:
                    print(".", end="", flush=True)
        
        print(f"\n✅ Audio Saved: {output_path}")
        print("🎧 Validate rhythm now.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if "API key not configured" in str(e):
             print("💡 Tip: Ensure ELEVENLABS_API_KEY is set in docker environment.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RMBC Voice Validation")
    parser.add_argument("file", nargs="?", help="Path to markdown draft file", default=None)
    args = parser.parse_args()

    target_file = args.file
    
    # Auto-pick latest draft if no file provided
    if not target_file:
        if os.path.exists(DRAFTS_DIR):
            files = [os.path.join(DRAFTS_DIR, f) for f in os.listdir(DRAFTS_DIR) if f.endswith(".md")]
            if files:
                target_file = max(files, key=os.path.getmtime)
                print(f"Auto-selected latest draft: {target_file}")
    
    if target_file:
        asyncio.run(generate_audio(target_file))
    else:
        print("No draft provided and none found in default directory.")
