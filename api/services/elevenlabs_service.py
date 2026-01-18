
import os
import logging
import httpx
from fastapi import HTTPException
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        # Use a default voice ID (e.g., standard generic), or let it be passed in.
        # Rachel: 21m00Tcm4TlvDq8ikWAM
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM" 

    async def stream_speech(self, text: str, voice_id: str = None) -> AsyncGenerator[bytes, None]:
        """
        Stream audio from ElevenLabs API.
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            raise ValueError("ElevenLabs API key not configured")

        voice_id = voice_id or self.default_voice_id
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }

        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_content = await response.aread()
                    logger.error(f"ElevenLabs API Error: {response.status_code} - {error_content}")
                    raise HTTPException(status_code=response.status_code, detail=f"ElevenLabs Error: {error_content.decode()}")

                async for chunk in response.aiter_bytes():
                    yield chunk

_service = None

def get_elevenlabs_service() -> ElevenLabsService:
    global _service
    if _service is None:
        _service = ElevenLabsService()
    return _service
