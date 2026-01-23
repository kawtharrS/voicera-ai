import os
import httpx
from fastapi import HTTPException, Response
from config import TTS_MODEL, SPEED, TIMEOUT, VOICE_MAPPING, HEADERS

async def generate_tts(text: str, voice: str, category: str | None):
    api_key = os.getenv("OPENAI_API_KEY")
    selected_voice = VOICE_MAPPING.get(category, voice)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers=HEADERS,
            json={
                "model": TTS_MODEL,
                "input": text,
                "voice": selected_voice,
                "speed": SPEED,
            },
            timeout=TIMEOUT,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return Response(
            content=response.content,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Content-Length": str(len(response.content)),
                "Accept-Ranges": "bytes",
            },
        )
