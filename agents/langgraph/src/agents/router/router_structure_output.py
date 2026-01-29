from pydantic import BaseModel, Field
from enum import Enum

class RouteCategory(str, Enum):
    work = "work"
    study = "study"
    personal = "personal"
    setting = "setting"

class RouterOutput(BaseModel):
    category: RouteCategory = Field(
        ...,
        description="The category assigned to the user query (work, study, personal or settings)"
    )

class ContinuationDecision(str, Enum):
    continue_workflow = "continue"
    end_workflow = "end"

class ContinuationOutput(BaseModel):
    decision: ContinuationDecision = Field(
        ...,
        description="Whether to continue the workflow (schedule calendar events) or end"
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for the decision"
    )
