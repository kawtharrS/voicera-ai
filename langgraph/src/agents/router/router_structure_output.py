from pydantic import BaseModel, Field
from enum import Enum

class RouteCategory(str, Enum):
    work = "work"
    study = "study"
    personal = "personal"

class RouterOutput(BaseModel):
    category: RouteCategory = Field(
        ...,
        description="The category assigned to the user query (work, study, or personal)"
    )
