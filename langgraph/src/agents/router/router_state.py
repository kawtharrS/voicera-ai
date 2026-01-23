from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    State for the Router Agent.
    Includes fields necessary for routing and for the sub-agents).

    NOTE: We explicitly include emotion-related fields so that the Aria
    (emotion) subgraph can write them and the top-level API can read them.
    Without these, LangGraph may drop those keys when merging state.
    """
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

    # Emotion-related fields populated by the Aria personal agent
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
