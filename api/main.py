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


class OrionTestRequest(BaseModel):
    user_request: str = Field(..., description="User request to categorize")
    thread_id: Optional[str] = Field(None, description="Thread id for short-term memory")


class OrionTestResponse(BaseModel):
    user_request: str
    category: Optional[str]
    observation: str


class OrionRunRequest(BaseModel):
    user_request: str = Field(..., description="User request (e.g., create/search/update/delete calendar)")
    thread_id: Optional[str] = Field(None, description="Thread id for short-term memory")


class OrionRunResponse(BaseModel):
    user_request: str
    category: Optional[str]
    route: Optional[str]
    ai_response: str
    observation: str
    calendar_result: Optional[dict] = None


class GmailTestRequest(BaseModel):
    email_subject: str = Field(..., description="Email subject")
    email_body: str = Field(..., description="Email body content")


class GmailTestResponse(BaseModel):
    email_subject: str
    email_body: str
    category: Optional[str]
    observation: str


class GmailRunRequest(BaseModel):
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    sender: Optional[str] = None
    thread_id: Optional[str] = None
    user_approved: Optional[bool] = Field(False, description="User approves sending (default: False = creates draft)")


class GmailRunResponse(BaseModel):
    email_subject: str
    email_category: Optional[str]
    generated_email: str
    sendable: bool
    trials: int
    observation: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "message": "Voicera API is running"
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


@app.post("/orion/test-receive-categorize", response_model=OrionTestResponse)
async def orion_test_receive_categorize(payload: OrionTestRequest):
    """Test Orion graph receive + categorize only."""
    try:
        # Import inside the endpoint to avoid triggering Google Calendar credential loading at app startup.
        from agents.orion.nodes.calendar_nodes import CalendarNodes

        nodes = CalendarNodes()

        initial_state = {
            "events": [],
            "current_interaction": {
                "user_request": payload.user_request,
                "ai_response": "",
                "recommendations": [],
                "observation": "",
            },
            "agent_messages": [],
            "sendable": False,
            "trials": 0,
            "max_trials": 1,
            "rewrite_feedback": "",
            "user_context": "",
            "conversation_history": [],
            "query_category": None,
        }

        # Run only the two nodes (no routing / calendar calls).
        state1 = {**initial_state, **nodes.receive_user_query(initial_state)}
        state2 = {**state1, **nodes.categorize_user_query(state1)}

        interaction = state2.get("current_interaction")
        if isinstance(interaction, dict):
            observation = interaction.get("observation", "")
        else:
            observation = getattr(interaction, "observation", "")

        category = state2.get("query_category")
        return OrionTestResponse(
            user_request=payload.user_request,
            category=category,
            observation=observation or "",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orion/run", response_model=OrionRunResponse)
async def orion_run(payload: OrionRunRequest):
    """Run the full Orion graph (includes routing and may create events)."""
    try:
        # Import inside the endpoint to avoid side effects at app startup.
        from agents.orion.graphs.calendar_graph import graph as orion_graph

        initial_state = {
            "events": [],
            "current_interaction": {
                "user_request": payload.user_request,
                "ai_response": "",
                "recommendations": [],
                "observation": "",
            },
            "agent_messages": [],
            "sendable": False,
            "trials": 0,
            "max_trials": 1,
            "rewrite_feedback": "",
            "user_context": "",
            "conversation_history": [],
            "query_category": None,
        }

        thread_id = payload.thread_id or "orion"
        result = orion_graph.invoke(initial_state, {"configurable": {"thread_id": thread_id}})

        interaction = result.get("current_interaction")
        if isinstance(interaction, dict):
            ai_response = interaction.get("ai_response", "")
            observation = interaction.get("observation", "")
        else:
            ai_response = getattr(interaction, "ai_response", "")
            observation = getattr(interaction, "observation", "")

        category = result.get("query_category")
        route = result.get("route")
        calendar_result = result.get("calendar_result")
        if calendar_result is not None and not isinstance(calendar_result, dict):
            calendar_result = {"result": str(calendar_result)}

        return OrionRunResponse(
            user_request=payload.user_request,
            category=category,
            route=route,
            ai_response=ai_response or "",
            observation=observation or "",
            calendar_result=calendar_result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gmail/test-categorize", response_model=GmailTestResponse)
async def gmail_test_categorize(payload: GmailTestRequest):
    """Test Gmail agent: categorize email only."""
    try:
        from agents.orion.nodes.gmail_nodes import GmailNodes

        nodes = GmailNodes()

        email_content = f"Subject: {payload.email_subject}\n\n{payload.email_body}"
        
        result = nodes.agents.categorize_email.invoke({
            "email": email_content
        })
        category = result.category.value

        return GmailTestResponse(
            email_subject=payload.email_subject,
            email_body=payload.email_body,
            category=category,
            observation=f"Email categorized as: {category}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gmail/run", response_model=GmailRunResponse)
async def gmail_run(payload: GmailRunRequest):
    """Run full Gmail workflow: fetch real emails from Gmail → categorize → generate → verify."""
    try:
        from agents.orion.graphs.gmail_graph import graph as gmail_graph
        from tools.gmailTools import GmailTool

        # Fetch real emails from Gmail
        gmail_tool = GmailTool()
        unanswered_emails = gmail_tool.fetch_unanswered_emails(max_results=10)

        if not unanswered_emails:
            return GmailRunResponse(
                email_subject="No emails",
                email_category="none",
                generated_email="",
                sendable=False,
                trials=0,
                observation="No unanswered emails found in your inbox"
            )

        # Process emails through the workflow
        initial_state = {
            "emails": [],  # Will be loaded by graph
            "current_email": None,
            "current_interaction": None,
            "email_category": None,
            "rag_queries": [],
            "retrieved_documents": "",
            "generated_email": "",
            "sendable": False,
            "trials": 0,
            "writer_messages": [],
            "agent_messages": [],
            "conversation_history": [],
            "is_processing": False,
            "route": None,
            "user_approved": payload.user_approved or False,
        }

        # Convert to Email objects and add to state
        from agents.orion.states.gmail_state import Email
        emails = [
            Email(
                id=email.get("id"),
                thread_id=email.get("threadId"),
                message_id=email.get("messageId"),
                sender=email.get("sender"),
                subject=email.get("subject"),
                body=email.get("body")
            )
            for email in unanswered_emails
        ]
        initial_state["emails"] = emails

        thread_id = payload.thread_id or "gmail_auto_run"
        result = gmail_graph.invoke(initial_state, {"configurable": {"thread_id": thread_id}})

        # Return summary of processing
        emails_processed = len(unanswered_emails)
        user_approved = payload.user_approved or False

        return GmailRunResponse(
            email_subject=f"Processed {emails_processed} email(s)",
            email_category="batch_processed",
            generated_email="",
            sendable=user_approved,
            trials=0,
            observation=f"✓ Processed {emails_processed} email(s) from Gmail - Mode: {'Send' if user_approved else 'Draft (for review)'}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
