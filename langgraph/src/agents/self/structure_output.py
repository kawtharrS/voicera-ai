from pydantic import BaseModel, Field 
from enum import Enum 
from typing import Optional

class SelfAction(str, Enum):
    updated_prefrences = "updated_prefrences"
    get_prefrences="get_prefrences"

class SelfAgentOutput(BaseModel):
    action: SelfAction = Field(
        ...,
        description="Action the SelfAgent should take"
    )

    language: Optional[str] = Field(
        None,
        description="Preferred language of the user"
    )

    tone: Optional[str] = Field(
        None,
        description="Preferred response tone"
    )

    name: Optional[str] = Field(
        None,
        description="User name"
    )

    preference: Optional[str] = Field(
        None,
        description="Any additional user preference"
    )

