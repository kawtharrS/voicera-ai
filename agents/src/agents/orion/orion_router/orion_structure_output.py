from pydantic import BaseModel, Field
from enum import Enum

class RouteOrion(str, Enum):
    gmail= "gmail"
    calendar = "calendar"

class RouterOutput(BaseModel):
    category: RouteOrion = Field(
        ...,
        description="The category assigned to the user query within orion (gemail or calendar)"
    )