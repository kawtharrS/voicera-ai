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


class SearchEventArgs(BaseModel):
    min_datetime: str = Field(..., description="Search start datetime, format: 'YYYY-MM-DD HH:MM:SS'")
    max_datetime: str = Field(..., description="Search end datetime, format: 'YYYY-MM-DD HH:MM:SS'")
    query: Optional[str] = Field(
        default=None,
        description="Optional free-text query to match summary/description/location/attendees",
    )
    max_results: int = Field(default=10, description="Maximum number of events to return")


class UpdateEventArgs(BaseModel):
    event_id: Optional[str] = Field(default=None, description="The event ID to update (if known)")
    calendar_id: str = Field(default="primary", description="Calendar ID")

    target_min_datetime: Optional[str] = Field(
        default=None,
        description="Target event search window start, format: 'YYYY-MM-DD HH:MM:SS'",
    )
    target_max_datetime: Optional[str] = Field(
        default=None,
        description="Target event search window end, format: 'YYYY-MM-DD HH:MM:SS'",
    )
    target_query: Optional[str] = Field(
        default=None,
        description="Optional free-text search term for the target event (title/location/etc)",
    )
    max_results: int = Field(default=10, description="Maximum target candidates to return")

    new_summary: Optional[str] = Field(default=None, description="Updated event title")
    new_start_datetime: Optional[str] = Field(
        default=None, description="New start datetime, format: 'YYYY-MM-DD HH:MM:SS'"
    )
    new_end_datetime: Optional[str] = Field(
        default=None, description="New end datetime, format: 'YYYY-MM-DD HH:MM:SS'"
    )
    timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone (e.g., 'Asia/Beirut', 'UTC', 'Europe/Paris')",
    )
    new_location: Optional[str] = Field(default=None, description="Updated event location")
    new_description: Optional[str] = Field(default=None, description="Updated event description")
    send_updates: Optional[str] = Field(
        default=None,
        description="Whether to send updates to attendees: 'all', 'externalOnly', or 'none'",
    )


class DeleteEventArgs(BaseModel):
    event_id: Optional[str] = Field(default=None, description="The event ID to delete (if known)")
    calendar_id: str = Field(default="primary", description="Calendar ID")
    target_min_datetime: Optional[str] = Field(
        default=None,
        description="Target event search window start, format: 'YYYY-MM-DD HH:MM:SS'",
    )
    target_max_datetime: Optional[str] = Field(
        default=None,
        description="Target event search window end, format: 'YYYY-MM-DD HH:MM:SS'",
    )
    target_query: Optional[str] = Field(
        default=None,
        description="Optional free-text search term for the target event (title/location/etc)",
    )
    max_results: int = Field(default=10, description="Maximum target candidates to return")
    send_updates: Optional[str] = Field(
        default=None,
        description="Whether to send updates to attendees: 'all', 'externalOnly', or 'none'",
    )
