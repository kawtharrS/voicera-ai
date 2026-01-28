from fastapi import APIRouter, HTTPException, Response
from services.tts_service import generate_tts

router = APIRouter()

@router.get("/tts")
async def text_to_speech(text: str, voice: str = "alloy", category: str | None = None):
    return await generate_tts(text, voice, category)
