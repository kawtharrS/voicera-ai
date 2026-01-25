import os
import sys
from pathlib import Path

from models import StudentQuestion, AIResponse
from utils.response_extractor import (
    extract_ai_response,
    extract_recommendations,
    extract_emotion,
)

def _load_graph():
    # Primary path for Docker environment
    docker_src = "/langgraph/src"
    
    # Fallback for local development
    local_src = str(Path(__file__).parent.parent.parent / "langgraph" / "src")
    
    if os.path.exists(docker_src):
        if docker_src not in sys.path:
            sys.path.insert(0, docker_src)
    elif os.path.exists(local_src):
        if local_src not in sys.path:
            sys.path.insert(0, local_src)
            
    try:
        from agents.router.router_graph import graph
        return graph
    except ImportError as e:
        print(f"Failed to import graph. Path: {sys.path}")
        raise e

graph = _load_graph()

DEFAULT_MAX_TRIALS = 3
DEFAULT_STUDENT_ID = "default_student"

async def process_question(query: StudentQuestion) -> AIResponse:
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
        "messages": [],
    }
    result = await graph.ainvoke(
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
