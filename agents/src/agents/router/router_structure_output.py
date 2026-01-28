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
