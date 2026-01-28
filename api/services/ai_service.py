import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from models import StudentQuestion, AIResponse
from utils.response_extractor import (
    extract_ai_response,
    extract_recommendations,
    extract_emotion,
)

langgraph_src = Path(__file__).parent.parent.parent / "agents" / "langgraph" / "src"
sys.path.insert(0, str(langgraph_src))
from agents.router.router_graph import graph


DEFAULT_MAX_TRIALS = 3

def build_initial_state(query: StudentQuestion) -> dict:
    return {
        "courses": [],
        "courseworks": [],
        "requested_course_id": query.course_id,
        "student_id": query.student_id or "",
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
        "study_plan": None,
    }


async def process_question(query: StudentQuestion) -> AIResponse:
    initial_state = build_initial_state(query)
    
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