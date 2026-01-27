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

langgraph_src = Path(__file__).parent.parent.parent / "langgraph" / "src"
sys.path.insert(0, str(langgraph_src))
from agents.router.router_graph import graph


DEFAULT_MAX_TRIALS = 3
DEFAULT_STUDENT_ID = "default_student"

# In-memory cache for study plans (keyed by student_id)
_study_plan_cache: Dict[str, Optional[Dict[str, Any]]] = {}
# In-memory cache for last created email draft id (keyed by student_id)
_email_draft_cache: Dict[str, Optional[str]] = {}

async def process_question(query: StudentQuestion) -> AIResponse:
    student_id = query.student_id or DEFAULT_STUDENT_ID
    
    # Retrieve cached study plan / email draft if it exists
    cached_study_plan = _study_plan_cache.get(student_id)
    cached_email_draft_id = _email_draft_cache.get(student_id)
    
    # Prepare study_plan as dict if it exists (for sub-graph compatibility)
    study_plan_dict = None
    if cached_study_plan:
        if hasattr(cached_study_plan, 'model_dump'):
            study_plan_dict = cached_study_plan.model_dump()
        elif isinstance(cached_study_plan, dict):
            study_plan_dict = cached_study_plan
    
    initial_state = {
        "courses": [],
        "courseworks": [],
        "requested_course_id": query.course_id,
        "student_id": student_id,
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
        "study_plan": study_plan_dict,  # Pass cached study plan as dict
        "email_draft_id": cached_email_draft_id,
    }
    result = await graph.ainvoke(
        initial_state,
        {"configurable": {"thread_id": str(initial_state["student_id"])}},
    )
    
    # Cache the study plan if it was generated or updated
    if result.get("study_plan"):
        plan = result["study_plan"]
        # Convert to dict if it's a Pydantic model
        if hasattr(plan, 'model_dump'):
            _study_plan_cache[student_id] = plan.model_dump()
        else:
            _study_plan_cache[student_id] = plan

    # Cache email draft id if created during calendar actions
    # Check both calendar_result and top-level email_draft_id
    email_draft_id = result.get("email_draft_id")
    if not email_draft_id:
        cal_res = result.get("calendar_result")
        if isinstance(cal_res, dict):
            email_draft_id = cal_res.get("email_draft_id")
    
    if email_draft_id:
        _email_draft_cache[student_id] = email_draft_id
    
    # If we just sent the email, clear the cached draft id
    cal_res = result.get("calendar_result")
    if isinstance(cal_res, dict) and cal_res.get("email_sent"):
        _email_draft_cache[student_id] = None
    
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
