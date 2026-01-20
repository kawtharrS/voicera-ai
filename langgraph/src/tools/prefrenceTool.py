from .selfTool import UpdatePreferencesTool
from typing import Optional
import os 
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

class PreferencesTool:
    def __init__(self):
        print(os.getenv("SUPABASE_URL"))
        print(os.getenv("SUPABASE_KEY"))
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_KEY")

        if not self._supabase_url or not self._supabase_key:
            raise ValueError("Supabase URL and KEY must be provided")

        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is None:
            self._client = create_client(self._supabase_url, self._supabase_key)
        return self._client

    def updatePreferences(self) -> UpdatePreferencesTool:
        return UpdatePreferencesTool(supabase=self._get_client())
