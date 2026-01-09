from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum 

class QueryCategory(str, Enum):
    create= "create"
    search = "search"
    update = "update"
    delete = "delete"

class CategorizeQueryOutput(BaseModel):
    category: QueryCategory= Field(
        ...,
        description="The category assigned to the user's query, indicating the type of help requested"
    )


class AIResponseOutput(BaseModel):
    response : str = Field(
        ..., 
        description= "The draft response provided by the AI to the user's query, including explanation, guidance and study tips"
    )

class ProofReaderOutput(BaseModel):
    feedback : str = Field(
        ...,
        description= "Detailed feedback explaining whether the AI's response is complete clear, and helpful"
    )
    send : bool = Field (
        ...,
        description= "Indicates whether the AI response is ready to be sent (true) or requires revisions (false)"
    )

class CreateEventArgs(BaseModel):
    summary: str = Field(..., description="Short title of the event")
    start_datetime: str = Field(..., description="Event start datetime, format: 'YYYY-MM-DD HH:MM:SS'")
    end_datetime: Optional[str] = Field(
        default=None,
        description="Optional event end datetime, format: 'YYYY-MM-DD HH:MM:SS'",
    )
    timezone: str = Field(
        default="Asia/Beirut",
        description="IANA timezone (e.g., 'Asia/Beirut', 'UTC', 'Europe/Paris')",
    )
    location: Optional[str] = Field(default=None, description="Optional event location")
    description: Optional[str] = Field(default=None, description="Optional event description")