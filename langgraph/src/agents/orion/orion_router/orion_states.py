from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    State for Orion router agent
    Includes fields necessary for routing through orion router
    """

    query:str
    category: Optional[str]
    messages: Annotated[List[BaseMessage], add_messages]
    