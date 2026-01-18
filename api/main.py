import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from fastapi.responses import StreamingResponse
import openai
import os 
import httpx
langgraph_src = str(Path(__file__).parent.parent / "langgraph" / "src")
sys.path.insert(0, langgraph_src)

from agents.router.router_graph import graph

app = FastAPI(
    title="Voicera ClassroomAI API",
    description="AI-powered assistant API",
    version="1.0.0"
)

VOICE_MAPPING = {
    "study": "alloy",     
    "work": "onyx",      
    "personal": "shimmer", 
    "gmail": "onyx",   
    "calendar": "onyx"  
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudentQuestion(BaseModel):
    question: str = Field(..., description="Student's question")
    course_id: Optional[str] = Field(None, description="Optional course ID")
    student_id: Optional[str] = Field(None, description="Optional student ID for memory/context")
    conversation_history: Optional[List[dict]] = Field(
        default=None,
        description="Previous messages for context"
    )
    preferences: Optional[dict] = Field(
        default=None,
        description="User preferences for language, tone, agent name, etc."
    )


DEFAULT_MAX_TRIALS = 3

class AIResponse(BaseModel):
    question: str
    response: str
    recommendations: List[str]
    feedback: str
    sendable: bool
    trials: int
    observation: Optional[str] = Field(default="", description="Agent observation")
    category: Optional[str] = Field(default=None, description="Query category")

class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "message": "Voicera API is running"
    }

async def process_question(query: StudentQuestion):
    try:
        initial_state = {
            "courses": [],
            "courseworks": [],
            "requested_course_id": query.course_id,
            "student_id": query.student_id or "default_student", 
            "student_context": "",
            "conversation_history": [],
            "user_preferences": query.preferences or {},
            "current_interaction": {
                "current_course": None,
                "current_coursework": None,
                "student_question": query.question,
                "ai_response": "",
                "recommendations": []
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
            {"configurable": {"thread_id": str(query.student_id or "default")}}
        )
        
        courses = result.get("courses", [])
        current_course = courses[0] if courses else None
        
        interaction = result.get("current_interaction", {})
        
        if isinstance(interaction, dict):
            if current_course and not interaction.get("current_course"):
                interaction["current_course"] = current_course
        
        ai_response = interaction.get("ai_response", "") if isinstance(interaction, dict) else getattr(interaction, "ai_response", "")
        recommendations = interaction.get("recommendations", []) if isinstance(interaction, dict) else getattr(interaction, "recommendations", [])
        observation = interaction.get("observation", "") if isinstance(interaction, dict) else getattr(interaction, "observation", "")
        category = result.get("category")
        
        return AIResponse(
            question=query.question,
            response=ai_response,
            recommendations=recommendations,
            feedback="Response generated successfully",
            sendable=result.get("sendable", False),
            trials=result.get("trials", 0),
            observation=observation,
            category=category
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-anything", response_model=AIResponse)
async def ask_anything(query: StudentQuestion):
    """Universal endpoint that routes to appropriate agent based on query category."""
    return await process_question(query)


@app.get("/tts")
async def text_to_speech(text: str, voice: Optional[str] = "alloy", category: Optional[str] = None):
    """Convert text to speech using OpenAI TTS API
    
    Args:
        text: The text to convert to speech
        voice: Specific voice to use (default: alloy)
        category: Optional category to determine voice automatically (overrides voice default if matches mapping)
    """
    try:
        print(f"Request received - text: {text[:50]}..., category: {category}")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("[TTS ERROR] OPENAI_API_KEY not found in environment")
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        selected_voice = voice
        if category and category in VOICE_MAPPING:
            selected_voice = VOICE_MAPPING[category]
        
        print(f"[TTS] Using voice: {selected_voice}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": selected_voice,
                    "speed": 1.0
                },
                timeout=30.0  
            )
            
            print(f"[TTS] OpenAI response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"[TTS ERROR] OpenAI API error: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=f"TTS API error: {error_detail}")
            
            print("Successfully generated audio")
            return StreamingResponse(
                iter([response.content]),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[TTS ERROR] Exception occurred:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


    
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
