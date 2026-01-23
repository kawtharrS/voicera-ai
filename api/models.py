from pydantic import BaseModel, Field
from typing import List, Optional

class AIResponse(BaseModel):
    question: str
    response: str
    recommendations: List[str]
    feedback: str
    sendable: bool
    trials: int
    observation: Optional[str] = Field(default="", description="Agent observation")
    category: Optional[str] = Field(default=None, description="Query category")
    emotion: Optional[str] = Field(default=None, description="Agent emotion")

class HealthResponse(BaseModel):
    status: str
    message: str

class StudentQuestion(BaseModel):
    question: str = Field(..., description="Student's question")
    course_id: Optional[str] = Field(None, description="Optional course ID")
    student_id: Optional[str] = Field(None, description="Optional student ID for memory/context")
    conversation_history: Optional[List[dict]] = Field(
        default=None,
        description="Previous messages for context"
    )
    preferences: Optional[dict] = Field(None, description="User preferences")
