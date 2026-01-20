from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class StudentQueryCategory(str, Enum):
    homework = "homework"
    concept_question = "concept_question"
    exam_preparation = "exam_preparation"
    general_inquiry = "general_inquiry"

class CategorizeQueryOutput(BaseModel):
    category: StudentQueryCategory = Field(
        ..., 
        description="The category assigned to the student's query, indicating the type of help requested."
    )

class RAGQueriesOutput(BaseModel):
    queries: List[str] = Field(
        ..., 
        description="A list of up to three short, actionable guidance items (not questions) to help the student immediately."
    )

class AIResponseOutput(BaseModel):
    response: str = Field(
        ..., 
        description="The draft response provided by the AI to the student's query, including explanations, guidance, or study tips."
    )

class ProofReaderOutput(BaseModel):
    feedback: str = Field(
        ..., 
        description="Detailed feedback explaining whether the AI's response is complete, clear, and helpful."
    )
    send: bool = Field(
        ..., 
        description="Indicates whether the AI response is ready to be sent (true) or requires revision (false)."
    )
