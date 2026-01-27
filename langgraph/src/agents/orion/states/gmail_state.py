from pydantic import BaseModel, Field 
from typing import Any, List, Optional, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime


class Email(BaseModel):
    id: str = Field(..., description="Unique identifier of the email")
    thread_id: str = Field(..., description="Gmail thread ID")
    message_id: str = Field(..., description="RFC 2822 message ID")
    sender: str = Field(..., description="Email sender address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    timestamp: Optional[datetime] = Field(None, description="Email received timestamp")


class EmailInteraction(BaseModel):
    email: Optional[Email] = Field(None, description="The current email being processed")
    category: Optional[str] = Field(None, description="Categorized email type")
    rag_queries: List[str] = Field(default_factory=list, description="Generated RAG queries")
    retrieved_documents: str = Field(default="", description="Retrieved information from RAG")
    generated_email: str = Field(default="", description="AI-generated response email")
    ai_response: str = Field(default="", description="The final response to show the user")
    sendable: bool = Field(default=False, description="Whether email is ready to send")
    trials: int = Field(default=0, description="Number of generation attempts")
    writer_messages: List[str] = Field(default_factory=list, description="Writer agent history")
    observation: Optional[str] = Field(None, description="Current operation observation")


class GraphState(TypedDict):
    query: str
    emails: List[Email]
    current_email: Optional[Email]
    current_interaction: Optional[EmailInteraction]
    email_category: Optional[str]
    rag_queries: List[str]
    retrieved_documents: str
    generated_email: str
    ai_response: str
    sendable: bool
    trials: int
    writer_messages: List[str]
    agent_messages: Annotated[list, add_messages]
    conversation_history: List[BaseMessage]
    is_processing: bool
    route: Optional[str]
    is_first_message: Optional[bool]
    sending_drafts: Optional[bool]
    retrieving_drafts: Optional[bool]
    available_drafts: Optional[List[dict]]
    user_approved: Optional[bool]
    user_preferences: Optional[dict]
