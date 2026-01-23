from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    query: str
    category: Optional[str]
    messages: Annotated[List[BaseMessage], add_messages]
    
    question: Optional[str] 
    course_id: Optional[str]
    student_id: Optional[str]
    conversation_history: Optional[List[dict]]
    
    ai_response: Optional[str]
    recommendations: Optional[List[str]]
    sendable: Optional[bool]
    trials: Optional[int]
    max_trials: Optional[int]
    observation: Optional[str]

    emotion: Optional[str]
    detected_emotion: Optional[str]
    emotion_output: Optional[dict]
    
    courses: Optional[List[dict]]
    courseworks: Optional[List[dict]]
    requested_course_id: Optional[str]
    current_interaction: Optional[dict]
    agent_messages: Optional[List[dict]]
    rewrite_feedback: Optional[str]
    user_preferences: Optional[dict]
    is_first_message: Optional[bool]
