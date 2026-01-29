
import asyncio
import os
import sys
import subprocess
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.elevenlabs_service import get_elevenlabs_service, ElevenLabsService
from api.services.dream_service import get_dream_service, DreamService

load_dotenv()

# Configuration
# User provided: "Dr Mani 620"
# Since we don't have the ID, we use a placeholder or check env
DR_MANI_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Defaults to Rachel if not set
OUTPUT_FILE = "data/guidance.mp3"

async def main():
    print("🔮  Connecting to Subconscious Stream...")
    
    # 1. Fetch Guidance
    try:
        try:
            dream_service = await get_dream_service()
        except:
            # Fallback for local testing without DB
            dream_service = DreamService(graphiti=None)
            from api.models.hexis_ontology import DriveType
            dream_service._state.drives[DriveType.MASTERY].level = 0.2
            dream_service._state.blocks["guidance"].value = "This is a test of the Dr Mani voice system. The architecture is sound."

        guidance_text = await dream_service.generate_guidance()
        
        # We only want to speak the "Guidance" part, not the whole markdown block with headers
        # Extract the text under "## GUIDANCE"
        if "## GUIDANCE" in guidance_text:
             parts = guidance_text.split("## GUIDANCE")[1].split("## ")[0]
             # Clean cleanup
             clean_text = parts.replace("_Active advice for the next session._", "").strip()
             clean_text = clean_text.replace("> [!TIP]", "Tip:").replace("> [!NOTE]", "Note:")
             clean_text = clean_text.replace("**", "")
        else:
             clean_text = "No active guidance found."

        print(f"🗣️  Speaking: {clean_text[:100]}...")
        
    except Exception as e:
        print(f"❌ Error fetching guidance: {e}")
        return

    # 2. Generate Audio
    service = get_elevenlabs_service()
    
    print(f"🎧 Generating Audio with Voice ID: {DR_MANI_VOICE_ID}...")
    try:
        if not os.path.exists("data"):
            os.makedirs("data")
            
        with open(OUTPUT_FILE, "wb") as f:
            async for chunk in service.stream_speech(clean_text, voice_id=DR_MANI_VOICE_ID):
                f.write(chunk)
        
        print(f"✅ Audio saved to {OUTPUT_FILE}")
        
        # 3. Play Audio (Mac specific)
        if sys.platform == "darwin":
            print("▶️  Playing...")
            subprocess.run(["afplay", OUTPUT_FILE])
            
    except Exception as e:
        print(f"❌ Audio Generation Error: {e}")
        if "API key not configured" in str(e):
             print("💡 Set ELEVENLABS_API_KEY in .env")

if __name__ == "__main__":
    asyncio.run(main())
