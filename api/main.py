import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


langgraph_src = Path(__file__).parent.parent / "langgraph" / "src"
sys.path.insert(0, str(langgraph_src))

from agents.router.router_graph import graph

DEFAULT_MAX_TRIALS = 3
DEFAULT_STUDENT_ID = "default_student"
TTS_MODEL = "tts-1"
SPEED = 1.0
TIMEOUT=30.0

VOICE_MAPPING = {
    "study": "alloy",
    "work": "onyx",
    "personal": "shimmer",
    "gmail": "onyx",
    "calendar": "onyx",
}

app = FastAPI(
    title="Voicera API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudentQuestion(BaseModel):
    question: str
    course_id: Optional[str] = None
    student_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    preferences: Optional[Dict[str, Any]] = None


class AIResponse(BaseModel):
    question: str
    response: str
    recommendations: List[str]
    feedback: str
    sendable: bool
    trials: int
    observation: Optional[str] = ""
    category: Optional[str] = None
    emotion: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    message: str


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_ai_response(result: Dict[str, Any]) -> str:
    response = result.get("ai_response")

    if not response:
        interaction = result.get("current_interaction")
        if interaction:
            response = _get_val(interaction, "ai_response", "")

    if response and isinstance(response, str) and response.startswith("I noticed you're feeling"):
        response = response.split(". ", 1)[-1]

    return response or "How can I help you today?"


def extract_recommendations(result: Dict[str, Any]) -> List[str]:
    recs = result.get("recommendations")

    if not recs:
        interaction = result.get("current_interaction")
        if interaction:
            recs = _get_val(interaction, "recommendations", [])

    return recs or []


def extract_emotion(result: Dict[str, Any]) -> Optional[str]:
    emotion = result.get("emotion")

    if not emotion:
        detected = result.get("detected_emotion")
        if detected:
            emotion = getattr(detected, "value", str(detected))

    if not emotion:
        emotion_output = result.get("emotion_output", {})
        emotion = emotion_output.get("emotion")

    return None if emotion in (None, "unknown") else emotion

async def process_question(query: StudentQuestion) -> AIResponse:
    try:
        initial_state = {
            "courses": [],
            "courseworks": [],
            "requested_course_id": query.course_id,
            "student_id": query.student_id or DEFAULT_STUDENT_ID,
            "student_context": "",
            "conversation_history": [],
            "user_preferences": query.preferences or {},
            "current_interaction": {
                "current_course": None,
                "current_coursework": None,
                "student_question": query.question,
                "ai_response": "",
                "recommendations": [],
            },
            "agent_messages": query.conversation_history or [],
            "sendable": False,
            "trials": 0,
            "max_trials": DEFAULT_MAX_TRIALS,
            "rewrite_feedback": "",
            "query": query.question,
            "category": None,
        }

        result = graph.invoke(
            initial_state,
            {"configurable": {"thread_id": str(initial_state["student_id"])}},
        )

        return AIResponse(
            question=query.question,
            response=extract_ai_response(result),
            recommendations=extract_recommendations(result),
            feedback="Response generated successfully",
            sendable=result.get("sendable", False),
            trials=result.get("trials", 0),
            observation=result.get("observation", ""),
            category=result.get("category"),
            emotion=extract_emotion(result),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "healthy", "message": "Voicera API is running"}


@app.post("/ask-anything", response_model=AIResponse)
async def ask_anything(query: StudentQuestion):
    return await process_question(query)


@app.get("/tts")
async def text_to_speech(
    text: str,
    voice: Optional[str] = "alloy",
    category: Optional[str] = None,
):
    api_key = os.getenv("OPENAI_API_KEY")
    selected_voice = VOICE_MAPPING.get(category, voice)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": TTS_MODEL,
                "input": text,
                "voice": selected_voice,
                "speed": SPEED,
            },
            timeout=TIMEOUT,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )

        return StreamingResponse(
            iter([response.content]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"},
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
