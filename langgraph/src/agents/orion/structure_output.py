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


class RAGQueriesOutput(BaseModel):
    queries : List[str] = Field(
        ..., 
        description="A list of up to three short, actionable guidance items to help the user immediately"
    )