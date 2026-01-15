from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    State for the Router Agent.
    Includes fields necessary for routing and for the sub-agents (Eureka/Classroom).
    """
    # Router fields
    query: str
    category: Optional[str]
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Eureka / Shared fields
    question: Optional[str] # alias for query often used in Eureka
    course_id: Optional[str]
    student_id: Optional[str]
    conversation_history: Optional[List[dict]]
    
    # Response fields
    ai_response: Optional[str]
    recommendations: Optional[List[str]]
    sendable: Optional[bool]
    trials: Optional[int]
    max_trials: Optional[int]
    observation: Optional[str]
    
    # Eureka specific
    courses: Optional[List[dict]]
    courseworks: Optional[List[dict]]
    requested_course_id: Optional[str]
    current_interaction: Optional[dict]
    agent_messages: Optional[List[dict]]
    rewrite_feedback: Optional[str]