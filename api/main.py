import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

langgraph_src = str(Path(__file__).parent.parent / "langgraph" / "src")
sys.path.insert(0, langgraph_src)

from agents.eureka.graph import graph


app = FastAPI(
    title="Voicera ClassroomAI API",
    description="AI-powered classroom assistant API",
    version="1.0.0"
)

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


DEFAULT_MAX_TRIALS = 3

class AIResponse(BaseModel):
    question: str
    response: str
    recommendations: List[str]
    feedback: str
    sendable: bool
    trials: int
    observation: Optional[str] = Field(default="", description="Agent observation")

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "message": "Voicera ClassroomAI API is running"
    }

@app.post("/ask", response_model=AIResponse)
async def ask_question(query: StudentQuestion):
    try:
        initial_state = {
            "courses": [],
            "courseworks": [],
            "requested_course_id": query.course_id,
            "student_id": query.student_id or "default_student",  # Use provided ID or default
            "student_context": "",
            "conversation_history": [],
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
        }
        
        # Invoke graph with thread_id for memory persistence
        result = graph.invoke(
            initial_state,
            {"configurable": {"thread_id": str(query.student_id or "default")}}
        )
        
        # Extract the course from result if it was loaded
        courses = result.get("courses", [])
        current_course = courses[0] if courses else None
        
        interaction = result.get("current_interaction", {})
        
        # Ensure current_course is set in interaction
        if isinstance(interaction, dict):
            if current_course and not interaction.get("current_course"):
                interaction["current_course"] = current_course
        
        ai_response = interaction.get("ai_response", "") if isinstance(interaction, dict) else getattr(interaction, "ai_response", "")
        recommendations = interaction.get("recommendations", []) if isinstance(interaction, dict) else getattr(interaction, "recommendations", [])
        observation = interaction.get("observation", "") if isinstance(interaction, dict) else getattr(interaction, "observation", "")
        
        return AIResponse(
            question=query.question,
            response=ai_response,
            recommendations=recommendations,
            feedback="Response generated successfully",
            sendable=result.get("sendable", False),
            trials=result.get("trials", 0),
            observation=observation
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-simple")
async def ask_simple(question: str):
    try:
        query = StudentQuestion(question=question)
        return await ask_question(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
