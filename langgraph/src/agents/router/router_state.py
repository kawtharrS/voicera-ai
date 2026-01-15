from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    query: str
    category: Optional[str]
    messages: Annotated[List[BaseMessage], add_messages]