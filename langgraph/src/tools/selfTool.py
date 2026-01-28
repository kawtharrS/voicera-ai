from __future__ import annotations

from typing import Optional, Type

from supabase import Client
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class UpdatePreferenceInput(BaseModel):
    user_id: int = Field(..., description="User ID from users table")
    language: Optional[str] = ""
    tone: Optional[str] = ""
    name: Optional[str] = ""
    preference: Optional[str] = ""


class UpdatePreferencesTool(BaseTool):
    name: str = "update_user_preferences"
    description: str = "Create or update a user's preferences in Supabase"
    args_schema: Type[BaseModel] = UpdatePreferenceInput

    supabase: Client

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, supabase: Client):
        super().__init__(supabase=supabase)

    def _run(
        self,
        user_id: int,
        language: str = "",
        tone: str = "",
        name: str = "",
        preference: str = "",
    ) -> str:
        payload = {
            "user_id": user_id,
            "language": language,
            "tone": tone,
            "name": name,
            "preference": preference,
        }

        existing = (
            self.supabase
            .table("preferences")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )

        if existing.data:
            (
                self.supabase
                .table("preferences")
                .update(payload)
                .eq("user_id", user_id)
                .execute()
            )
            return "Preferences updated."

        self.supabase.table("preferences").insert(payload).execute()
        return "Preferences created."

    async def _arun(self, **kwargs):
        return self._run(**kwargs)
