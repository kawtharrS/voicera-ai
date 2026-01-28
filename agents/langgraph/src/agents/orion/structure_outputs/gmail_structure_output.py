from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class EmailCategory(str, Enum):
    study = "study"
    work = "work"
    general = "general"
    unrelated = "unrelated"


class CategorizeEmailOutput(BaseModel):
    category: EmailCategory = Field(
        ...,
        description="The category assigned to the email"
    )


class GenerateRAGQueriesOutput(BaseModel):
    queries: List[str] = Field(
        ...,
        description="List of up to 3 queries for RAG retrieval"
    )


class GenerateRAGAnswerOutput(BaseModel):
    answer: str = Field(
        ...,
        description="Answer to the RAG query based on retrieved context"
    )


class EmailWriterOutput(BaseModel):
    email: str = Field(
        ...,
        description="The drafted email response"
    )


class EmailProofreaderOutput(BaseModel):
    send: bool = Field(
        ...,
        description="Whether the email is ready to send (true) or needs revision (false)"
    )
    feedback: str = Field(
        ...,
        description="Detailed feedback for improvements if send is false"
    )


class SendNewEmailArgs(BaseModel):
    recipient: str = Field(..., description="The email address of the recipient")
    subject: str = Field(..., description="The subject of the email")
    body: str = Field(..., description="The body content of the email")
