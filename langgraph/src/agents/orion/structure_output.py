from pydantic import BaseModel, Field
from typing import List
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