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
    emotion: Optional[str] = Field(default=None, description="Detected emotion (if available)")

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
        
        # DEBUG: Log what we got back
        print(f"\n=== RESULT STATE ===")
        print(f"Category: {result.get('category')}")
        print(f"Direct ai_response: {result.get('ai_response')}")
        print(f"Detected emotion: {result.get('detected_emotion')}")
        print(f"Emotion output: {result.get('emotion_output')}")
        print(f"==================\n")
        
        courses = result.get("courses", [])
        current_course = courses[0] if courses else None
        
        # Get the AI response
        ai_response = result.get("ai_response", "")
        if not ai_response:
            interaction = result.get("current_interaction", {})
            if isinstance(interaction, dict):
                ai_response = interaction.get("ai_response", "")
            else:
                ai_response = getattr(interaction, "ai_response", "")
        
        # IMPORTANT: Remove emotion context from response for normal chat
        # The emotion is detected but we only send it back in the JSON, not in the response text
        if ai_response.startswith("I noticed you're feeling"):
            # Extract just the meaningful part without emotion message
            parts = ai_response.split(". ", 1)
            if len(parts) > 1:
                ai_response = parts[1]
            else:
                ai_response = "How can I help you today?"
        
        # Extract recommendations
        recommendations = result.get("recommendations", [])
        if not recommendations:
            interaction = result.get("current_interaction", {})
            if isinstance(interaction, dict):
                recommendations = interaction.get("recommendations", [])
            else:
                recommendations = getattr(interaction, "recommendations", [])
        
        observation = result.get("observation", "")
        category = result.get("category")

        # CRITICAL: Extract emotion properly
        # 1) First try the simple `emotion` field set by the personal assistant path
        emotion: Optional[str] = result.get("emotion")
        if emotion:
            print(f"[DEBUG] Extracted emotion from result['emotion']: {emotion}")
        
        # 2) Fall back to detected_emotion (Enum or string) from Aria workflow
        if not emotion:
            detected_emotion = result.get("detected_emotion")
            if detected_emotion is not None:
                emotion = getattr(detected_emotion, "value", None) or str(detected_emotion)
                print(f"[DEBUG] Extracted emotion from detected_emotion: {emotion}")
        
        # 3) Fall back to emotion_output dict from Aria workflow
        if not emotion:
            emotion_output = result.get("emotion_output") or {}
            if isinstance(emotion_output, dict):
                emotion = emotion_output.get("emotion")
                print(f"[DEBUG] Extracted emotion from emotion_output: {emotion}")
        
        # Filter out 'unknown' emotions
        if emotion == "unknown":
            emotion = None
        
        print(f"[DEBUG] Final emotion: {emotion}")
        
        return AIResponse(
            question=query.question,
            response=ai_response,
            recommendations=recommendations,
            feedback="Response generated successfully",
            sendable=result.get("sendable", False),
            trials=result.get("trials", 0),
            observation=observation,
            category=category,
            emotion=emotion,  # Return only the emotion value, not in the response text
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
