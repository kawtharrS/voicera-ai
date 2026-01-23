from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    query: str
    category: Optional[str]
    messages: Annotated[List[BaseMessage], add_messages]
    
    student_id: Optional[str]
    current_interaction: Optional[dict]
    agent_messages: Optional[List[dict]]
    sendable: Optional[bool]
    trials: Optional[int]
    max_trials: Optional[int]
    rewrite_feedback: Optional[str]
    user_context: Optional[str]
    conversation_history: Optional[List[dict]]
    is_first_message: Optional[bool]
    