
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from api.services.elevenlabs_service import get_elevenlabs_service, ElevenLabsService

router = APIRouter(prefix="/voice", tags=["voice"])

class SpeakRequest(BaseModel):
    text: str
    voice_id: str | None = None

@router.post("/speak")
async def speak(
    request: SpeakRequest,
    service: ElevenLabsService = Depends(get_elevenlabs_service)
):
    """
    Stream audio for the given text using ElevenLabs.
    """
    try:
        return StreamingResponse(
            service.stream_speech(request.text, request.voice_id),
            media_type="audio/mpeg"
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
